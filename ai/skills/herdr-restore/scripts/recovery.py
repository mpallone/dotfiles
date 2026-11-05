#!/usr/bin/env python3
"""Recover Herdr layouts with a Codex fallback (Python 3.9+, standard library).

Only install --approved changes Herdr state. Reports and plans are written only
to explicitly requested files outside that directory. Start with inspect --help.
"""
from __future__ import annotations

import argparse
import copy
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


class RecoveryError(Exception):
    """Evidence is incomplete or a restore precondition failed."""


def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def digest(path, size=None):
    """Hash a whole file or a recorded prefix, permitting later journal appends."""
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        remaining = size
        while remaining is None or remaining > 0:
            block = handle.read(1048576 if remaining is None else min(remaining, 1048576))
            if not block:
                if remaining:
                    raise RecoveryError("Evidence was truncated: " + str(path))
                break
            result.update(block)
            if remaining is not None:
                remaining -= len(block)
    return result.hexdigest()


def fingerprint(path):
    path = Path(path).resolve()
    size = path.stat().st_size
    return {"path": str(path), "size": size, "sha256": digest(path, size)}


def check_fingerprint(item, allow_append=False):
    path = Path(item["path"])
    if not allow_append and path.stat().st_size != item["size"]:
        raise RecoveryError("Evidence changed: " + str(path))
    if digest(path, item["size"]) != item["sha256"]:
        raise RecoveryError("Evidence changed: " + str(path))


def instant(value):
    """Parse an ISO timestamp with a mandatory offset, e.g. 2026-01-02T09:10-08:00."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise RecoveryError("Timestamp needs an explicit UTC offset: " + value)
    return parsed


def snapshot_rows(snapshot):
    """Validate schema 3 and flatten panes without assuming a workspace or count."""
    if not isinstance(snapshot, dict) or snapshot.get("version") != 3:
        raise RecoveryError("Unsupported Herdr snapshot version; inspect the installed schema")
    if not isinstance(snapshot.get("workspaces"), list):
        raise RecoveryError("Snapshot has no workspace array")
    rows = []
    for wi, workspace in enumerate(snapshot["workspaces"]):
        for ti, tab in enumerate(workspace["tabs"]):
            panes, leaves = tab["panes"], []
            if not isinstance(panes, dict):
                raise RecoveryError("Snapshot pane collection is not an object")

            def walk(node):
                if isinstance(node, dict) and set(node) == {"Pane"}:
                    leaves.append(str(node["Pane"]))
                elif isinstance(node, dict) and set(node) == {"Split"}:
                    split = node["Split"]
                    if split["direction"] not in ("Horizontal", "Vertical") or not 0 < split["ratio"] < 1:
                        raise RecoveryError("Invalid split geometry")
                    walk(split["first"])
                    walk(split["second"])
                else:
                    raise RecoveryError("Unsupported layout node")
            walk(tab["layout"])
            if len(leaves) != len(set(leaves)) or set(leaves) != set(panes):
                raise RecoveryError("Layout and pane records disagree")
            for pane_id, pane in panes.items():
                if not isinstance(pane.get("cwd"), str) or not Path(pane["cwd"]).is_absolute():
                    raise RecoveryError("Pane cwd must be an absolute path")
                reference = pane.get("agent_session")
                launch = pane.get("launch_argv")
                if launch is not None and (not isinstance(launch, list) or not launch or not all(
                    isinstance(part, str) and part and "\0" not in part for part in launch
                )):
                    raise RecoveryError("Unsupported saved launch command")
                if reference is not None:
                    if not isinstance(reference, dict) or not all(
                        isinstance(reference.get(key), str) and reference[key]
                        for key in ("source", "agent", "kind", "value")
                    ) or reference["kind"] not in ("id", "path"):
                        raise RecoveryError("Unsupported agent session reference")
                rows.append({
                    "workspace": workspace.get("id"), "workspace_index": wi,
                    "tab_index": ti, "tab_name": tab.get("custom_name"),
                    "pane": str(pane_id), "cwd": pane["cwd"], "agent_session": reference,
                    "launch_argv": launch, "managed_agent_kind": pane.get("managed_agent_kind"),
                })
    return rows


def file_summary(path, zone, target_date, before):
    try:
        rows = snapshot_rows(read_json(path))
        epoch = Path(path).stat().st_mtime
        modified = datetime.fromtimestamp(epoch, zone)
        return {
            "path": str(Path(path).resolve()), "fingerprint": fingerprint(path),
            "mtime": modified.isoformat(), "mtime_epoch": epoch,
            "target_day": modified.date() == target_date, "pre_cutoff": modified < before,
            "panes": rows, "agent_panes": sum(row["agent_session"] is not None for row in rows),
            "unreferenced_panes": sum(row["agent_session"] is None for row in rows),
        }
    except (OSError, ValueError, KeyError, TypeError, RecoveryError) as error:
        return {"path": str(path), "error": str(error)}


def has_conversation(lines):
    """Distinguish conversation records from startup/settings events in a transcript.

    Metadata plus thread_settings_applied still represents a blank session.
    """
    for line in lines:
        record = json.loads(line)
        payload = record.get("payload", {})
        if record.get("type") == "event_msg" and payload.get("type") in (
            "user_message", "user_msg", "agent_message"
        ):
            return True
        if record.get("type") == "response_item":
            if payload.get("role") == "assistant":
                return True
            if payload.get("role") == "user":
                content = payload.get("content", "")
                text = " ".join(item.get("text", "") for item in content if isinstance(item, dict)) if isinstance(content, list) else str(content)
                if text.strip() and not text.lstrip().startswith((
                    "# AGENTS.md", "<environment_context>", "<user_instructions>"
                )):
                    return True
    return False


def codex_inventory(codex_home):
    """Read root metadata including idle and metadata-only sessions; exclude subagents.

    SQLite supplies optional titles. JSONL metadata supplies IDs, cwd, and original
    creation times. No modification-time filter is applied to matching evidence.
    """
    home = Path(codex_home)
    titles, user_events, warnings, errors = {}, {}, [], []
    database = home / "state_5.sqlite"
    if database.exists():
        try:
            with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as connection:
                connection.execute("PRAGMA query_only=ON")
                for sid, title, has_user, first_user in connection.execute(
                    "SELECT id, title, has_user_event, first_user_message FROM threads"
                ):
                    titles[sid] = title
                    user_events[sid] = bool(has_user or first_user)
        except sqlite3.Error as error:
            warnings.append("Optional Codex titles unavailable: " + str(error))
    sessions = home / "sessions"
    if not sessions.is_dir():
        return [], ["Codex sessions directory is missing: " + str(sessions)], warnings
    roots = []
    for path in sessions.rglob("*.jsonl"):
        try:
            with path.open(encoding="utf-8") as handle:
                lines = (line for line in handle if line.strip())
                first = json.loads(next(lines))
                metadata = first["payload"]
                if first.get("type") != "session_meta":
                    raise RecoveryError("First record is not session_meta")
                source = metadata.get("source")
                if metadata.get("parent_thread_id") or (
                    isinstance(source, dict) and "subagent" in source
                ) or str(metadata.get("thread_source", "")).startswith("guardian"):
                    continue
                session_id = str(uuid.UUID(metadata["id"]))
                roots.append({
                    "id": session_id, "cwd": metadata["cwd"],
                    "created": instant(metadata["timestamp"]).isoformat(),
                    "mtime_epoch": path.stat().st_mtime, "path": str(path.resolve()),
                    "empty": not (user_events.get(session_id) or has_conversation(lines)),
                    "title": titles.get(session_id),
                })
        except (OSError, ValueError, KeyError, TypeError, StopIteration, RecoveryError) as error:
            errors.append(str(path) + ": " + str(error))
    return roots, errors, warnings


def log_lines(path):
    with Path(path).open(encoding="utf-8") as handle:
        yield from handle


def ambiguous_creation(pending, active):
    """Keep ambiguous request interleavings from inventing workspace/tab provenance."""
    pending["ambiguous"] = True
    for pane in pending["panes"]:
        if pane in active:
            active[pane].update(workspace=None, tab=None, topology_warning="overlapping_tab_creation")


def log_layout(path, before):
    """Replay pane lifetimes up to cutoff, freezing the layout at graceful shutdown.

    Exits remove panes; agent changes replace the preceding agent start. This
    prevents resurrecting closed tabs or selecting an earlier process in a pane.
    """
    active, frozen, shutting_down, pending = {}, None, False, None
    for number, line in enumerate(log_lines(path), 1):
        try:
            stamp = instant(line.split()[0])
        except (ValueError, IndexError, RecoveryError):
            continue
        if stamp >= before:
            continue
        if "server using persistent user service context" in line:
            active, frozen, shutting_down, pending = {}, None, False, None
        if "server shutdown initiated" in line:
            frozen, shutting_down = copy.deepcopy(active), True
        if shutting_down:
            continue
        if "api.request.start" in line and 'method="tab.create"' in line:
            if pending is None:
                pending = {"timestamp": stamp, "panes": [], "depth": 1, "ambiguous": False}
            else:
                pending["depth"] += 1
                ambiguous_creation(pending, active)
        match = re.search(r'\bpane_id=(\d+)\b', line)
        if 'event="pane.spawn.start"' in line and match:
            pane_id = match.group(1)
            active[pane_id] = {
                "pane": pane_id, "spawned": stamp.isoformat(), "agent": None,
                "agent_started": None, "workspace": None, "tab": None, "line": number,
            }
            if pending and abs((stamp - pending["timestamp"]).total_seconds()) < 2:
                pending["panes"].append(pane_id)
                if len(pending["panes"]) > 1:
                    ambiguous_creation(pending, active)
        if pending and not pending["ambiguous"] and pending["depth"] == 1 and len(pending["panes"]) == 1 and any(
            event in line for event in ('event="tab.rename"', 'event="tab.focus"')
        ):
            workspace = re.search(r'workspace_id="([^"]+)"', line)
            tab = re.search(r'tab_id="([^"]+)"', line)
            if workspace and tab:
                active[pending["panes"][0]].update(workspace=workspace.group(1), tab=tab.group(1))
        if "api.request.complete" in line and 'method="tab.create"' in line:
            if pending:
                pending["depth"] -= 1
                if not pending["depth"]:
                    pending = None
        if 'event="workspace.create"' in line and match:
            workspace = re.search(r'workspace_id="([^"]+)"', line)
            if workspace and match.group(1) in active:
                active[match.group(1)]["workspace"] = workspace.group(1)
        if "agent changed" in line:
            pane = re.search(r'\bpane=(\d+)\b', line)
            agent = re.search(r'(?:^|\s)agent=(?:Some\(([^)]+)\)|(None))', line)
            if pane and agent and pane.group(1) in active:
                active[pane.group(1)].update(
                    agent=agent.group(1).casefold() if agent.group(1) else None,
                    agent_started=stamp.isoformat() if agent.group(1) else None,
                    agent_line=number,
                )
        if 'event="pane.exit"' in line and match:
            active.pop(match.group(1), None)
    return list((frozen if shutting_down and frozen is not None else active).values())


def match_log_panes(panes, sessions, before, window):
    """Accept only one-to-one timestamp matches; retain ambiguous alternatives."""
    result = []
    for pane in panes:
        row = dict(pane, matches=[])
        if pane["agent"] == "codex" and pane["agent_started"]:
            start = instant(pane["agent_started"])
            for session in sessions:
                created = instant(session["created"])
                delta = (created - start).total_seconds()
                if created < before and abs(delta) <= window:
                    row["matches"].append(dict(session, delta_seconds=round(delta, 6)))
        result.append(row)
    for row in result:
        candidates = row["matches"]
        shared = len(candidates) == 1 and any(
            other is not row and any(match["id"] == candidates[0]["id"] for match in other["matches"])
            for other in result
        )
        row["resolved"] = row["agent"] is None or (
            row["agent"] == "codex" and len(candidates) == 1 and not shared
        )
    return result


def inspect(args):
    """Collect evidence without launching Herdr or changing state."""
    directory = Path(args.state_dir).expanduser().resolve()
    zone, target, before = ZoneInfo(args.timezone), date.fromisoformat(args.date), instant(args.before)
    since = date.fromisoformat(args.since) if args.since else target - timedelta(days=3)
    if args.expect_agents and not 0 <= args.expect_agents[0] <= args.expect_agents[1]:
        raise RecoveryError("Expected counts require 0 <= MIN <= MAX")
    if args.match_window <= 0:
        raise RecoveryError("Match window must be positive")
    current = file_summary(directory / "session.json", zone, target, before)
    paths = []
    snapshots = directory / "session-snapshots"
    if snapshots.is_dir():
        paths.extend(path for path in snapshots.iterdir() if path.is_file())
    paths.extend(path for path in directory.glob("session.json.bak-*") if path.is_file())
    summaries = [file_summary(path, zone, target, before) for path in paths]
    summaries.sort(key=lambda item: (item.get("mtime_epoch", -1), item["path"]))
    current["source_type"] = "current"
    for item in summaries:
        item["source_type"] = "backup" if Path(item["path"]).name.startswith("session.json.bak-") else "snapshot"
    candidates = sorted([current] + summaries, key=lambda item: (item.get("mtime_epoch", -1), item["path"]))
    valid = [item for item in candidates if item.get("pre_cutoff") and "error" not in item]
    eligible = [
        item for item in valid if args.expect_agents is None
        or args.expect_agents[0] <= item["agent_panes"] <= args.expect_agents[1]
    ]
    sessions, errors, warnings = codex_inventory(Path(args.codex_home).expanduser())
    log = directory / "herdr-server.log"
    replay = match_log_panes(log_layout(log, before), sessions, before, args.match_window) if log.is_file() else []
    recent = [
        dict(item, mtime=datetime.fromtimestamp(item["mtime_epoch"], zone).isoformat())
        for item in sessions
        if datetime.fromtimestamp(item["mtime_epoch"], zone).date() >= since
    ]
    recent.sort(key=lambda item: (item["mtime_epoch"], item["id"]))
    return {
        "format": 1, "state_dir": str(directory), "session_name": args.session,
        "timezone": args.timezone, "date": args.date, "before": before.isoformat(),
        "expect_agents": args.expect_agents, "current": current, "snapshots": summaries,
        "layout_candidates": candidates,
        "snapshot_directory_exists": snapshots.is_dir(),
        "latest_pre_cutoff": valid[-1]["path"] if valid else None,
        "suggested_snapshot": eligible[-1]["path"] if eligible else None,
        "selection_needs_review": bool(valid and eligible and valid[-1] != eligible[-1]),
        "log_fingerprint": fingerprint(log) if log.is_file() else None,
        "log_panes": replay, "codex_sessions": sessions, "recent_codex_sessions": recent,
        "codex_errors": errors, "warnings": warnings,
    }


def topology(snapshot):
    """Compare pane locations while allowing focus and late session-reference saves."""
    return [
        {"workspace": workspace.get("id"), "cwd": workspace["identity_cwd"], "tabs": [
            {"layout": tab["layout"], "panes": [
                {"pane": key, "cwd": pane["cwd"]} for key, pane in sorted(tab["panes"].items())
            ]} for tab in workspace["tabs"]
        ]} for workspace in snapshot["workspaces"]
    ]


def normalize(snapshot):
    """Remap internal IDs across merged workspaces and preserve existing split geometry."""
    result, next_id, workspace_ids = copy.deepcopy(snapshot), 1, set()
    for workspace in result["workspaces"]:
        wid = workspace.get("id")
        if wid in workspace_ids:
            workspace["id"] = None
        if wid:
            workspace_ids.add(wid)
        old_numbers, numbers = workspace.get("public_pane_numbers", {}), {}
        for tab in workspace["tabs"]:
            mapping = {}
            for old_id in tab["panes"]:
                mapping[str(old_id)] = next_id
                numbers[str(next_id)] = old_numbers.get(str(old_id), len(numbers) + 1)
                next_id += 1

            def remap(node):
                if "Pane" in node:
                    return {"Pane": mapping[str(node["Pane"])]}
                split = copy.deepcopy(node["Split"])
                split["first"], split["second"] = remap(split["first"]), remap(split["second"])
                return {"Split": split}
            tab["layout"] = remap(tab["layout"])
            tab["panes"] = {str(mapping[key]): value for key, value in tab["panes"].items()}
            for field in ("focused", "root_pane"):
                if tab.get(field) is not None:
                    tab[field] = mapping[str(tab[field])]
        if len(set(numbers.values())) != len(numbers) or any(
            not isinstance(number, int) or number < 1 for number in numbers.values()
        ):
            numbers = {key: index + 1 for index, key in enumerate(numbers)}
        workspace["public_pane_numbers"] = numbers
        workspace["next_public_pane_number"] = max(numbers.values(), default=0) + 1
        tabs = workspace.get("public_tab_numbers", [])
        if len(tabs) != len(workspace["tabs"]) or len(set(tabs)) != len(tabs) or any(
            not isinstance(number, int) or number < 1 for number in tabs
        ):
            tabs = list(range(1, len(workspace["tabs"]) + 1))
        workspace["public_tab_numbers"] = tabs
        workspace["next_public_tab_number"] = max(tabs, default=0) + 1
        workspace["active_tab"] = min(workspace.get("active_tab", 0), max(len(tabs) - 1, 0))
    snapshot_rows(result)
    return result


def validate_sessions(snapshot, inventory):
    """Check Codex IDs and cwd against real metadata; return journal fingerprints."""
    by_id, evidence, seen = {}, [], set()
    for session in inventory:
        by_id.setdefault(session["id"], []).append(session)
    for row in snapshot_rows(snapshot):
        if not Path(row["cwd"]).is_dir():
            raise RecoveryError("Working directory is missing: " + row["cwd"])
        reference = row["agent_session"]
        if not reference:
            continue
        key = tuple(reference[field] for field in ("source", "agent", "kind", "value"))
        if key in seen:
            raise RecoveryError("Duplicate agent reference; reconcile overlapping layouts first")
        seen.add(key)
        if reference["agent"] != "codex":
            continue
        if reference["source"] != "herdr:codex" or reference["kind"] != "id":
            raise RecoveryError("Unsupported Codex reference")
        matches = by_id.get(reference["value"], [])
        if len(matches) != 1:
            raise RecoveryError("Missing or duplicate Codex transcript: " + reference["value"])
        session = matches[0]
        if Path(session["cwd"]).resolve() != Path(row["cwd"]).resolve():
            raise RecoveryError("Transcript and pane cwd disagree: " + session["id"])
        evidence.append(fingerprint(session["path"]))
    return evidence


def prepare(args):
    """Build a reviewable plan outside Herdr state; never stop a server."""
    report = read_json(args.report)
    current = report["current"]
    if "error" in current:
        raise RecoveryError("Cannot protect current state: " + current["error"])
    check_fingerprint(current["fingerprint"])
    original, sources, preserved = read_json(current["path"]), [], None
    if args.snapshot:
        selected = next((item for item in report["layout_candidates"]
                         if item["path"] == str(Path(args.snapshot).resolve())), None)
        if selected is None or not selected.get("pre_cutoff") or "error" in selected:
            raise RecoveryError("Choose a validated pre-cutoff snapshot from the report")
        check_fingerprint(selected["fingerprint"])
        candidate = read_json(selected["path"])
        sources.append(dict(selected["fingerprint"], allow_append=False))
    else:
        panes = report["log_panes"]
        if not panes or report["codex_errors"] or any(not row["resolved"] for row in panes):
            raise RecoveryError("Log reconstruction has incomplete or ambiguous evidence")
        check_fingerprint(report["log_fingerprint"], allow_append=True)
        sources.append(dict(report["log_fingerprint"], allow_append=True))
        groups = {}
        for row in panes:
            workspace = groups.setdefault(row["workspace"], {
                "id": row["workspace"], "custom_name": None, "identity_cwd": None,
                "tabs": [], "active_tab": 0,
            })
            if row["agent"] is None:
                raise RecoveryError("Logs do not establish a shell pane cwd; inspect other evidence")
            session = row["matches"][0]
            pane = {"cwd": session["cwd"], "agent_session": {
                "source": "herdr:codex", "agent": "codex", "kind": "id", "value": session["id"],
            }}
            workspace["identity_cwd"] = workspace["identity_cwd"] or session["cwd"]
            raw_id = int(row["pane"])
            workspace["tabs"].append({
                "custom_name": (session.get("title") or ("Empty Codex" if session["empty"] else "Recovered Codex"))[:80],
                "layout": {"Pane": raw_id}, "panes": {str(raw_id): pane},
                "zoomed": False, "focused": raw_id, "root_pane": raw_id,
            })
        candidate = {
            "version": 3, "workspaces": list(groups.values()), "active": 0, "selected": 0,
            "sidebar_width": original.get("sidebar_width"),
            "sidebar_section_split": original.get("sidebar_section_split"), "collapsed_space_keys": [],
        }
    recovered_count = sum(row["agent_session"] is not None for row in snapshot_rows(candidate))
    if args.current == "preserve":
        if not args.current_layout:
            raise RecoveryError("Preserve needs --current-layout with verified live references; see SKILL.md")
        preserved = read_json(args.current_layout)
        snapshot_rows(preserved)
        if topology(preserved) != topology(original):
            raise RecoveryError("Preserved layout must retain every current pane and cwd")
        if preserved != candidate:
            candidate["workspaces"].extend(copy.deepcopy(preserved["workspaces"]))
    candidate = normalize(candidate)
    evidence = validate_sessions(candidate, report["codex_sessions"])
    rows = snapshot_rows(candidate)
    ids = {row["agent_session"]["value"] for row in rows if row["agent_session"]}
    bounds = report["expect_agents"]
    return {
        "format": 1, "session_name": report["session_name"], "state_dir": report["state_dir"],
        "candidate": candidate, "source_state": current["fingerprint"], "source_topology": topology(original),
        "source_panes": snapshot_rows(original),
        "sources": sources, "transcripts": evidence, "current_policy": args.current, "panes": rows,
        "preserved_state": preserved,
        "additional_target_day_sessions": [
            item for item in report["recent_codex_sessions"]
            if item["mtime"][:10] == report["date"] and item["id"] not in ids
        ],
        "recovered_agent_panes": recovered_count,
        "agent_panes": sum(row["agent_session"] is not None for row in rows),
        "unreferenced_panes": sum(row["agent_session"] is None for row in rows),
        "expected_count_matches": bounds is None or bounds[0] <= recovered_count <= bounds[1],
    }


def run(command):
    completed = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if completed.returncode:
        raise RecoveryError("Command failed: " + " ".join(command) + "\n" + (completed.stderr or completed.stdout))
    return completed.stdout


def json_result(command, runner=run):
    response = json.loads(runner(command))
    if isinstance(response, dict) and "error" in response:
        raise RecoveryError("Herdr API error: " + json.dumps(response["error"]))
    return response.get("result", response)


def server_alive(socket_path):
    """A Unix socket permission denial is unknown, never evidence of a stopped server."""
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(1)
    try:
        client.connect(str(socket_path))
        return True
    except OSError as error:
        if error.errno in (errno.ENOENT, errno.ECONNREFUSED):
            return False
        raise RecoveryError("Cannot verify Herdr socket access: " + str(error)) from error
    finally:
        client.close()


def install(plan, approved, runner=run, probe=server_alive):
    """Back up the selected server's final saved state and atomically install an approved plan.

    The calling agent obtains user approval. Startup remains separate so a real
    terminal can supply client context. Existing logs, sockets, and backups survive.
    """
    if not approved:
        raise RecoveryError("Installation requires user approval of the prepared plan")
    if plan.get("format") != 1:
        raise RecoveryError("Unsupported recovery plan format")
    directory = Path(plan["state_dir"])
    if os.environ.get("HERDR_ENV") == "1":
        raise RecoveryError("Install outside Herdr so server shutdown cannot kill this operation")
    state = directory / "session.json"
    if state.is_symlink() or not state.is_file():
        raise RecoveryError("Install supports an existing regular session.json only")
    if Path(plan["source_state"]["path"]).resolve() != state.resolve():
        raise RecoveryError("Source fingerprint does not describe the target session.json")
    if snapshot_rows(plan["candidate"]) != plan["panes"]:
        raise RecoveryError("Candidate differs from the prepared pane table; prepare a new plan")
    if not plan["expected_count_matches"]:
        raise RecoveryError("Expected count differs; revise the reviewed plan before installation")
    check_fingerprint(plan["source_state"])
    for source in plan["sources"]:
        check_fingerprint(source, source["allow_append"])
    for transcript in plan["transcripts"]:
        check_fingerprint(transcript, allow_append=True)
    inventory = []
    for transcript in plan["transcripts"]:
        with Path(transcript["path"]).open(encoding="utf-8") as handle:
            metadata = json.loads(next(handle))["payload"]
        inventory.append({"id": metadata["id"], "cwd": metadata["cwd"], "path": transcript["path"]})
    validate_sessions(plan["candidate"], inventory)
    sessions = json_result(["herdr", "session", "list", "--json"], runner)["sessions"]
    session = next((item for item in sessions if item["name"] == plan["session_name"]), None)
    if not session or Path(session["session_dir"]).resolve() != directory.resolve():
        raise RecoveryError("Named session no longer resolves to the reviewed directory")
    socket_path = Path(session["socket_path"])
    probe(socket_path)
    runner(["herdr", "--session", plan["session_name"], "server", "stop"])
    for _ in range(20):
        if not probe(socket_path):
            break
        time.sleep(0.1)
    else:
        raise RecoveryError("Herdr did not stop; state was not replaced")
    before = state.read_bytes()
    stopped_snapshot = json.loads(before)
    if topology(stopped_snapshot) != plan["source_topology"]:
        raise RecoveryError("Pane topology changed during shutdown; state was not replaced")
    if plan["current_policy"] == "preserve":
        if not plan.get("preserved_state"):
            raise RecoveryError("Preserve plan lacks reviewed current identities; prepare it again")
        key = lambda row: (row["workspace_index"], row["tab_index"], row["pane"])
        prior = {key(row): row["agent_session"] for row in plan["source_panes"]}
        intended = {key(row): row["agent_session"] for row in snapshot_rows(plan["preserved_state"])}
        for row in snapshot_rows(stopped_snapshot):
            reference = row["agent_session"]
            if reference != prior[key(row)] and reference != intended[key(row)]:
                raise RecoveryError("Preserved session identity changed during shutdown; state was not replaced")
    backup = directory / ("session.json.bak-" + datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f%z"))
    descriptor = os.open(str(backup), os.O_WRONLY | os.O_CREAT | os.O_EXCL, stat.S_IMODE(state.stat().st_mode))
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(before)
        handle.flush()
        os.fsync(handle.fileno())
    if backup.read_bytes() != before:
        raise RecoveryError("Backup verification failed; state was not replaced")
    data = (json.dumps(plan["candidate"], indent=2) + "\n").encode()
    staged = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=".herdr-restore-", dir=str(directory.parent))
        staged = Path(name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(staged, stat.S_IMODE(state.stat().st_mode))
        if probe(socket_path) or state.read_bytes() != before:
            raise RecoveryError("Herdr restarted or state changed; state was not replaced")
        os.replace(staged, state)
        if state.read_bytes() != data:
            raise RecoveryError("Installed state verification failed; backup: " + str(backup))
    finally:
        if staged and staged.exists():
            staged.unlink()
    return {"backup": str(backup), "session": str(state), "agent_panes": plan["agent_panes"],
            "unreferenced_panes": plan["unreferenced_panes"], "ready_to_launch": True}


def verify(plan, runner=run):
    """Check live references and foreground resume commands against an approved plan."""
    prefix = ["herdr", "--session", plan["session_name"]]
    workspaces = json_result(prefix + ["workspace", "list"], runner)["workspaces"]
    live = []
    for workspace in workspaces:
        wid = workspace.get("workspace_id", workspace.get("id"))
        if not wid:
            raise RecoveryError("Unexpected workspace list response")
        live.extend(json_result(prefix + ["pane", "list", "--workspace", wid], runner)["panes"])
    results = []
    for expected in plan["panes"]:
        reference = expected["agent_session"]
        if not reference:
            continue
        matches = [pane for pane in live if pane.get("agent_session") == reference]
        result = {"expected": expected, "ok": False}
        if len(matches) == 1:
            pane = matches[0]
            info = json_result(prefix + ["pane", "process-info", "--pane", pane["pane_id"]], runner)["process_info"]
            processes = info["foreground_processes"]
            option = "resume" if reference["agent"] == "codex" else "--resume"
            command_matches = any(
                bool(process.get("argv"))
                and (reference["agent"] != "codex" or Path(process["argv"][0]).name in ("codex", "codex.exe"))
                and option in process["argv"]
                and process["argv"].index(option) + 1 < len(process["argv"])
                and process["argv"][process["argv"].index(option) + 1] == reference["value"]
                and bool(process.get("cwd"))
                and Path(process["cwd"]).resolve() == Path(expected["cwd"]).resolve()
                for process in processes
            ) if reference["agent"] in ("codex", "claude") else None
            result.update(
                pane_id=pane["pane_id"], status=pane.get("agent_status"),
                commands=processes, native_resume_command_matches=command_matches,
                ok=(pane.get("agent") == reference["agent"] and command_matches is True
                    and Path(pane["cwd"]).resolve() == Path(expected["cwd"]).resolve()),
            )
        else:
            result["error"] = "Expected exactly one live pane with this reference"
        results.append(result)
    return {
        "all_agent_commands_match": bool(results) and all(item["ok"] for item in results),
        "pane_count_matches": len(live) == len(plan["panes"]), "results": results,
        "live_panes": len(live), "plain_shells": sum(not pane.get("agent") for pane in live),
        "screen_verification_required": True,
    }


def write_output(value, output, state_dir):
    text = json.dumps(value, indent=2) + "\n"
    if output:
        path = Path(output).expanduser().resolve()
        if path == Path(state_dir).resolve() or Path(state_dir).resolve() in path.parents:
            raise RecoveryError("Reports and plans must be outside Herdr state")
        descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(str(path))
    else:
        print(text, end="")


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("inspect", help="Read layouts, logs, and Codex metadata")
    scan.add_argument("--state-dir", required=True)
    scan.add_argument("--session", default="default")
    scan.add_argument("--date", required=True)
    scan.add_argument("--before", required=True, help="Exclusive cutoff with UTC offset")
    scan.add_argument("--timezone", required=True)
    scan.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    scan.add_argument("--since")
    scan.add_argument("--expect-agents", type=int, nargs=2, metavar=("MIN", "MAX"))
    scan.add_argument("--match-window", type=float, default=2)
    scan.add_argument("--output")
    make = commands.add_parser("prepare", help="Write a reviewable restore plan")
    make.add_argument("--report", required=True)
    selection = make.add_mutually_exclusive_group(required=True)
    selection.add_argument("--snapshot")
    selection.add_argument("--reconstruct", action="store_true")
    make.add_argument("--current", choices=("preserve", "replace"), default="preserve")
    make.add_argument("--current-layout", help="Current snapshot enriched with verified live IDs")
    make.add_argument("--output", required=True)
    apply = commands.add_parser("install", help="Install an approved plan; leave client closed")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--approved", action="store_true")
    check = commands.add_parser("verify", help="Check panes after client launch")
    check.add_argument("--plan", required=True)
    return root


def main():
    args = parser().parse_args()
    try:
        if args.command == "inspect":
            write_output(inspect(args), args.output, args.state_dir)
        elif args.command == "prepare":
            report = read_json(args.report)
            write_output(prepare(args), args.output, report["state_dir"])
        else:
            plan = read_json(args.plan)
            result = install(plan, args.approved) if args.command == "install" else verify(plan)
            print(json.dumps(result, indent=2))
            if args.command == "verify" and not (result["all_agent_commands_match"] and result["pane_count_matches"]):
                return 1
    except (RecoveryError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Behavioral checks use synthetic records and never contact a real Herdr server."""
import argparse
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
from zoneinfo import ZoneInfo

SPEC = importlib.util.spec_from_file_location("recovery", Path(__file__).parents[1] / "scripts/recovery.py")
recovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recovery)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def layout(cwd, ids=()):
    tabs = []
    for index, sid in enumerate(ids or (None, None), 1):
        pane = {"cwd": str(cwd)}
        if sid:
            pane["agent_session"] = {"source": "herdr:codex", "agent": "codex", "kind": "id", "value": sid}
        tabs.append({"custom_name": None, "layout": {"Pane": index}, "panes": {str(index): pane},
                     "zoomed": False, "focused": index, "root_pane": index})
    return {"version": 3, "workspaces": [{"id": "w1", "identity_cwd": str(cwd), "tabs": tabs}],
            "active": 0, "selected": 0}


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.codex = self.root / "codex"
        self.cwd = self.root / "project"
        self.cwd.mkdir()
        self.original = layout(self.cwd)
        save(self.state / "session.json", self.original)
        self.ids = [str(uuid.UUID(int=index + 1)) for index in range(12)]
        self.events = []

        def event(stamp, body):
            self.events.append((stamp, body))
        event("2026-01-01T09:00:00Z", "server using persistent user service context")
        for index in range(9):
            stamp = datetime(2026, 1, 1 if 1 <= index <= 4 else 10, 10, index, tzinfo=timezone.utc)
            self.transcript(self.ids[index], stamp + timedelta(milliseconds=100), empty=index in (0, 5))
            self.spawn(index + 1, stamp)
        self.transcript(self.ids[9], datetime(2026, 1, 10, 19, tzinfo=timezone.utc))
        self.spawn(10, datetime(2026, 1, 10, 19, tzinfo=timezone.utc))
        event("2026-01-10T19:05:00Z", 'event="pane.exit" pane_id=10')
        event("2026-01-11T08:59:00Z", "server shutdown initiated")
        for index in range(1, 10):
            event("2026-01-11T08:59:01Z", 'event="pane.exit" pane_id=' + str(index))
        event("2026-01-11T10:00:00Z", "server using persistent user service context")
        self.transcript(self.ids[10], datetime(2026, 1, 11, 10, tzinfo=timezone.utc))
        self.spawn(11, datetime(2026, 1, 11, 10, tzinfo=timezone.utc))
        self.flush_log()

    def transcript(self, sid, created, empty=False, **metadata):
        path = self.codex / "sessions" / "2026" / (sid + ".jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"id": sid, "timestamp": created.isoformat(), "cwd": str(self.cwd),
                   "source": "vscode", **metadata}
        records = [{"type": "session_meta", "timestamp": "2026-01-11T08:59:01Z", "payload": payload}]
        if not empty:
            records.append({"type": "response_item", "payload": {"role": "user", "content": "synthetic prompt"}})
        path.write_text("".join(json.dumps(record) + "\n" for record in records))
        os.utime(path, (created.timestamp(), created.timestamp()))
        return path

    def spawn(self, pane, stamp):
        start = stamp.isoformat().replace("+00:00", "Z")
        self.events.extend([
            (start, 'event="api.request.start" method="tab.create"'),
            (start, 'event="pane.spawn.start" pane_id=' + str(pane)),
            (start, 'event="tab.rename" workspace_id="w1" tab_id="original-' + str(pane) + '"'),
            (start, 'event="api.request.complete" method="tab.create"'),
            (start, 'agent changed pane=' + str(pane) + ' previous_agent=None agent=Some(Codex)'),
        ])

    def flush_log(self):
        path = self.state / "herdr-server.log"
        path.write_text("".join(stamp + " INFO test: " + body + "\n"
                                for stamp, body in sorted(self.events, key=lambda row: row[0])))

    def inspect(self, **changes):
        args = dict(state_dir=str(self.state), session="default", date="2026-01-10",
                    before="2026-01-11T09:00:00+00:00", timezone="UTC", codex_home=str(self.codex),
                    since=None, expect_agents=[7, 13], match_window=2)
        args.update(changes)
        report = recovery.inspect(argparse.Namespace(**args))
        save(self.root / "report.json", report)
        return report

    def plan(self, **changes):
        self.inspect()
        args = dict(report=str(self.root / "report.json"), snapshot=None, reconstruct=True,
                    current="replace", current_layout=None)
        args.update(changes)
        return recovery.prepare(argparse.Namespace(**args))

    def fake_cli(self, flush=True):
        calls = []

        def runner(command):
            calls.append(command)
            if command == ["herdr", "session", "list", "--json"]:
                return json.dumps({"sessions": [{"name": "default", "session_dir": str(self.state),
                                                "socket_path": str(self.state / "herdr.sock")} ]})
            if command[-2:] == ["server", "stop"]:
                if flush:
                    value = recovery.read_json(self.state / "session.json")
                    value["sidebar_width"] = 37
                    save(self.state / "session.json", value)
                return ""
            raise AssertionError(command)
        return runner, calls

    def test_reconstructs_survivors_including_idle_and_blank_sessions_without_writes(self):
        before = {path.name: path.read_bytes() for path in self.state.iterdir()}
        report = self.inspect()
        self.assertFalse(report["snapshot_directory_exists"])
        self.assertEqual(len(report["log_panes"]), 9)
        self.assertTrue(all(row["resolved"] for row in report["log_panes"]))
        self.assertEqual({row["matches"][0]["id"] for row in report["log_panes"]}, set(self.ids[:9]))
        self.assertEqual(sum(row["matches"][0]["empty"] for row in report["log_panes"]), 2)
        self.assertLess(len(report["recent_codex_sessions"]), len(report["codex_sessions"]))
        plan = self.plan()
        self.assertEqual(plan["agent_panes"], 9)
        self.assertEqual({path.name: path.read_bytes() for path in self.state.iterdir()}, before)

    def test_agent_none_clears_the_previous_codex_and_latest_start_wins(self):
        stamp = "2026-01-10T20:00:00Z"
        self.events.append((stamp, "agent changed pane=1 previous_agent=Some(Codex) agent=None"))
        self.flush_log()
        row = next(row for row in self.inspect()["log_panes"] if row["pane"] == "1")
        self.assertIsNone(row["agent"])
        with self.assertRaisesRegex(recovery.RecoveryError, "shell pane cwd"):
            self.plan()
        created = datetime(2026, 1, 10, 20, 1, tzinfo=timezone.utc)
        self.transcript(self.ids[11], created)
        self.events.append(("2026-01-10T20:01:00Z", "agent changed pane=1 previous_agent=None agent=Some(Codex)"))
        self.flush_log()
        row = next(row for row in self.inspect()["log_panes"] if row["pane"] == "1")
        self.assertEqual(row["matches"][0]["id"], self.ids[11])

    def test_subagents_excluded_and_ambiguous_matches_block_preparation(self):
        stamp = datetime(2026, 1, 10, 10, tzinfo=timezone.utc)
        self.transcript(str(uuid.UUID(int=99)), stamp, parent_thread_id=self.ids[0],
                        source={"subagent": {"other": "guardian"}})
        self.assertTrue(all(row["resolved"] for row in self.inspect()["log_panes"]))
        self.transcript(str(uuid.UUID(int=100)), stamp)
        report = self.inspect()
        self.assertFalse(next(row for row in report["log_panes"] if row["pane"] == "1")["resolved"])
        with self.assertRaisesRegex(recovery.RecoveryError, "ambiguous"):
            self.plan()

    def test_snapshot_selection_uses_local_day_and_real_mtime(self):
        directory = self.state / "session-snapshots"
        directory.mkdir()
        for name, count, moment in [
            ("good.json", 9, "2026-01-11T06:00:00+00:00"),
            ("latest.json", 2, "2026-01-11T07:00:00+00:00"),
            ("after.json", 9, "2026-01-11T12:00:00+00:00"),
        ]:
            path = directory / name
            save(path, layout(self.cwd, self.ids[:count]))
            epoch = datetime.fromisoformat(moment).timestamp()
            os.utime(path, (epoch, epoch))
        report = self.inspect(timezone="America/Los_Angeles")
        self.assertEqual(Path(report["latest_pre_cutoff"]).name, "latest.json")
        self.assertEqual(Path(report["suggested_snapshot"]).name, "good.json")
        self.assertTrue(report["selection_needs_review"])
        self.assertTrue(next(row for row in report["snapshots"] if Path(row["path"]).name == "latest.json")["target_day"])

    def test_snapshot_order_is_correct_across_daylight_saving_repeated_hour(self):
        directory = self.state / "session-snapshots"
        directory.mkdir()
        for name, stamp in [("first.json", "2026-11-01T01:30:00-07:00"),
                            ("second.json", "2026-11-01T01:15:00-08:00")]:
            path = directory / name
            save(path, layout(self.cwd, self.ids[:9]))
            epoch = recovery.instant(stamp).timestamp()
            os.utime(path, (epoch, epoch))
        report = self.inspect(date="2026-11-01", before="2026-11-01T03:00:00-08:00",
                              timezone="America/Los_Angeles")
        self.assertEqual(Path(report["latest_pre_cutoff"]).name, "second.json")

    def test_intact_current_layout_is_a_selectable_pre_cutoff_source(self):
        path = self.state / "session.json"
        save(path, layout(self.cwd, self.ids[:9]))
        epoch = recovery.instant("2026-01-11T08:00:00+00:00").timestamp()
        os.utime(path, (epoch, epoch))
        report = self.inspect()
        self.assertEqual(report["suggested_snapshot"], str(path.resolve()))
        plan = recovery.prepare(argparse.Namespace(report=str(self.root / "report.json"),
                                snapshot=str(path), reconstruct=False, current="replace", current_layout=None))
        self.assertEqual(plan["recovered_agent_panes"], 9)

    def test_concurrent_tab_creation_has_unknown_provenance_instead_of_wrong_labels(self):
        stamp = "2026-01-10T21:00:00Z"
        for message in (
            'event="api.request.start" method="tab.create"',
            'event="pane.spawn.start" pane_id=20',
            'event="api.request.start" method="tab.create"',
            'event="pane.spawn.start" pane_id=21',
            'event="tab.rename" workspace_id="workspace-a" tab_id="tab-a"',
            'event="api.request.complete" method="tab.create"',
            'event="tab.rename" workspace_id="workspace-b" tab_id="tab-b"',
            'event="api.request.complete" method="tab.create"',
        ):
            self.events.append((stamp, message))
        self.flush_log()
        rows = [row for row in self.inspect()["log_panes"] if row["pane"] in ("20", "21")]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIsNone(row["workspace"])
            self.assertIsNone(row["tab"])
            self.assertEqual(row["topology_warning"], "overlapping_tab_creation")

    def test_preserve_requires_verified_current_layout_and_keeps_shells(self):
        with self.assertRaisesRegex(recovery.RecoveryError, "current-layout"):
            self.plan(current="preserve")
        plan = self.plan(current="preserve", current_layout=str(self.state / "session.json"))
        self.assertEqual(len(recovery.snapshot_rows(plan["candidate"])), 11)
        self.assertEqual(plan["agent_panes"], 9)
        self.assertEqual(plan["unreferenced_panes"], 2)
        raw = [row["pane"] for row in plan["panes"]]
        self.assertEqual(len(raw), len(set(raw)))

    def test_approval_and_stale_state_block_before_server_stop(self):
        plan = self.plan()
        runner, calls = self.fake_cli()
        with self.assertRaisesRegex(recovery.RecoveryError, "approval"):
            recovery.install(plan, False, runner, lambda _: False)
        self.assertFalse(calls)
        value = copy.deepcopy(self.original)
        value["sidebar_width"] = 10
        save(self.state / "session.json", value)
        with self.assertRaisesRegex(recovery.RecoveryError, "Evidence changed"):
            recovery.install(plan, True, runner, lambda _: False)
        self.assertFalse(calls)

    def test_backup_contains_final_shutdown_save_and_other_state_survives(self):
        plan = json.loads(json.dumps(self.plan()))
        extra = self.state / "unrelated.txt"
        extra.write_text("keep")
        runner, calls = self.fake_cli()
        with patch.dict(os.environ, {"HERDR_ENV": ""}):
            result = recovery.install(plan, True, runner, lambda _: False)
        backup = recovery.read_json(result["backup"])
        self.assertEqual(backup["sidebar_width"], 37)
        self.assertEqual(recovery.read_json(self.state / "session.json"), plan["candidate"])
        self.assertEqual(extra.read_text(), "keep")
        self.assertTrue(any(command[-2:] == ["server", "stop"] for command in calls))
        self.assertFalse(list(self.root.glob(".herdr-restore-*")))

    def test_socket_denial_and_failed_replace_do_not_overwrite_state(self):
        plan = self.plan()
        runner, calls = self.fake_cli(flush=False)
        before = (self.state / "session.json").read_bytes()

        def denied(_):
            raise recovery.RecoveryError("Cannot verify Herdr socket access")
        with patch.dict(os.environ, {"HERDR_ENV": ""}):
            with self.assertRaisesRegex(recovery.RecoveryError, "socket access"):
                recovery.install(plan, True, runner, denied)
        self.assertFalse(any(command[-2:] == ["server", "stop"] for command in calls))
        with patch.dict(os.environ, {"HERDR_ENV": ""}), patch.object(recovery.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                recovery.install(plan, True, runner, lambda _: False)
        self.assertEqual((self.state / "session.json").read_bytes(), before)
        self.assertEqual(len(list(self.state.glob("session.json.bak-*"))), 1)
        self.assertFalse(list(self.root.glob(".herdr-restore-*")))

    def test_preserve_aborts_on_a_conflicting_session_identity_saved_during_shutdown(self):
        save(self.state / "session.json", layout(self.cwd, [self.ids[9]]))
        plan = self.plan(current="preserve", current_layout=str(self.state / "session.json"))
        base_runner, calls = self.fake_cli(flush=False)

        def runner(command):
            result = base_runner(command)
            if command[-2:] == ["server", "stop"]:
                value = recovery.read_json(self.state / "session.json")
                value["workspaces"][0]["tabs"][0]["panes"]["1"]["agent_session"]["value"] = self.ids[10]
                save(self.state / "session.json", value)
            return result
        with patch.dict(os.environ, {"HERDR_ENV": ""}):
            with self.assertRaisesRegex(recovery.RecoveryError, "identity changed during shutdown"):
                recovery.install(plan, True, runner, lambda _: False)
        saved = recovery.snapshot_rows(recovery.read_json(self.state / "session.json"))
        self.assertEqual(saved[0]["agent_session"]["value"], self.ids[10])

    def test_preserve_allows_a_verified_live_reference_to_first_persist_on_shutdown(self):
        enriched = copy.deepcopy(self.original)
        enriched["workspaces"][0]["tabs"][0]["panes"]["1"]["agent_session"] = {
            "source": "herdr:codex", "agent": "codex", "kind": "id", "value": self.ids[9]
        }
        save(self.root / "enriched.json", enriched)
        plan = self.plan(current="preserve", current_layout=str(self.root / "enriched.json"))
        base_runner, _ = self.fake_cli(flush=False)

        def runner(command):
            result = base_runner(command)
            if command[-2:] == ["server", "stop"]:
                save(self.state / "session.json", enriched)
            return result
        with patch.dict(os.environ, {"HERDR_ENV": ""}):
            result = recovery.install(plan, True, runner, lambda _: False)
        self.assertEqual(recovery.read_json(result["backup"]), enriched)
        self.assertEqual(result["agent_panes"], 10)

    def test_expected_count_is_not_filled_and_unsupported_schema_is_not_selected(self):
        report = self.inspect(expect_agents=[1, 2])
        plan = recovery.prepare(argparse.Namespace(report=str(self.root / "report.json"),
                                snapshot=None, reconstruct=True, current="replace", current_layout=None))
        self.assertEqual(plan["recovered_agent_panes"], 9)
        self.assertFalse(plan["expected_count_matches"])
        runner, calls = self.fake_cli()
        with self.assertRaisesRegex(recovery.RecoveryError, "count differs"):
            recovery.install(plan, True, runner, lambda _: False)
        self.assertFalse(calls)
        directory = self.state / "session-snapshots"
        save(directory / "future.json", {"version": 99, "workspaces": []})
        self.assertIn("Unsupported", self.inspect()["snapshots"][0]["error"])

    def test_fingerprints_allow_append_but_reject_rewritten_history(self):
        path = self.root / "journal"
        path.write_bytes(b"original\n")
        recorded = recovery.fingerprint(path)
        path.write_bytes(b"original\nnew\n")
        recovery.check_fingerprint(recorded, allow_append=True)
        path.write_bytes(b"rewritten\n")
        with self.assertRaisesRegex(recovery.RecoveryError, "Evidence changed"):
            recovery.check_fingerprint(recorded, allow_append=True)

    def test_settings_written_on_resume_do_not_turn_a_blank_into_a_conversation(self):
        path = next((self.codex / "sessions").rglob(self.ids[0] + ".jsonl"))
        with path.open("a") as handle:
            handle.write(json.dumps({"type": "event_msg", "payload": {"type": "thread_settings_applied"}}) + "\n")
        row = next(row for row in self.inspect()["codex_sessions"] if row["id"] == self.ids[0])
        self.assertTrue(row["empty"])

    def test_changed_candidate_is_rejected_before_stop(self):
        plan = json.loads(json.dumps(self.plan()))
        plan["candidate"]["workspaces"][0]["tabs"][0]["panes"]["1"]["agent_session"]["value"] = self.ids[11]
        runner, calls = self.fake_cli()
        with self.assertRaisesRegex(recovery.RecoveryError, "Candidate differs"):
            recovery.install(plan, True, runner, lambda _: False)
        self.assertFalse(calls)

    def test_verify_checks_foreground_resume_id_instead_of_trusting_saved_reference(self):
        plan = self.plan()
        live = [
            {"pane_id": "actual-" + str(index), "agent": "codex", "agent_status": "idle",
             "cwd": row["cwd"], "agent_session": row["agent_session"]}
            for index, row in enumerate(plan["panes"])
        ]

        def runner(command):
            if command[-2:] == ["workspace", "list"]:
                return json.dumps({"result": {"workspaces": [{"workspace_id": "actual-workspace"}]}})
            if "list" in command and "pane" in command:
                return json.dumps({"result": {"panes": live}})
            pane = next(item for item in live if item["pane_id"] == command[-1])
            return json.dumps({"result": {"process_info": {"foreground_processes": [
                {"argv": ["codex", "resume", pane["agent_session"]["value"]], "cwd": pane["cwd"]}
            ]}}})
        verified = recovery.verify(plan, runner)
        self.assertTrue(verified["all_agent_commands_match"])
        self.assertTrue(verified["pane_count_matches"])

        def wrong(command):
            output = runner(command)
            if "process-info" in command:
                value = json.loads(output)
                value["result"]["process_info"]["foreground_processes"][0]["argv"][-1] = "wrong-id"
                return json.dumps(value)
            return output
        self.assertFalse(recovery.verify(plan, wrong)["all_agent_commands_match"])

        def wrong_process(command):
            output = runner(command)
            if "process-info" in command:
                value = json.loads(output)
                value["result"]["process_info"]["foreground_processes"][0]["argv"][0] = "python3"
                return json.dumps(value)
            return output
        self.assertFalse(recovery.verify(plan, wrong_process)["all_agent_commands_match"])


if __name__ == "__main__":
    unittest.main()

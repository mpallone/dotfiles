#!/usr/bin/env python3
"""Classify active-sprint Jira issues into a cleanup plan.

Pure, deterministic classifier for the `jira-sprint-cleanup` skill. It never
touches Jira -- the skill fetches the sprint over the Atlassian Rovo MCP, writes
the issues to a JSON file, and this script decides which to close and which to
keep. Keeping the rules here means they are applied identically every run instead
of being re-derived by hand across 200+ tickets.

Input: a JSON file holding a list of issues, each an object with:
    key           "MCP-1234"                      (required)
    summary       the ticket title                (required; these tickets are
                                                    title-only, description null)
    statusCategory "new" | "indeterminate" | "done"  (optional; when present,
                                                    "done" items are dropped -- we
                                                    only act on To-Do items)
    created       ISO-8601 timestamp              (optional; display only)

Every non-Done issue lands in exactly one bucket:
    banner    -- automation START/END markers or separator rows -> close all
    chore     -- "(... automation)" recurring chores -> keep newest per group,
                 close the older duplicates
    real      -- everything else -> never auto-closed
    divider   -- one of the 6 permanent manual dividers -> never touched
    borderline-- tripped the separator rule but reads like prose -> flagged for a
                 human decision, never auto-closed

"Newest" within a chore group is the highest issue number: Jira assigns keys
sequentially, so the largest MCP-N in a group was created last. This sidesteps
timezone-sensitive date parsing.

Usage:
    python classify.py issues.json

Prints a human-readable plan (grouped, keep-list last) followed by a delimited
MACHINE block the skill parses to drive the transitions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# --- Constants for the MCP personal-todo project (do not re-derive each run). ---
PROJECT_KEY = "MCP"
CLOUD_ID = "f438107c-ea02-4718-a002-5ce3646a61dd"
BASE_JQL = "project = MCP AND sprint in openSprints()"
# Verify against getTransitionsForJiraIssue on the first target before using it.
DONE_TRANSITION_ID = "31"

# The 6 permanent manual dividers kept as board structure. They look exactly like
# automation separator rows, so key is the ONLY thing distinguishing them -- never
# close these, whatever their summary matches.
PERMANENT_DIVIDERS = {
    "MCP-1193", "MCP-1550", "MCP-5493", "MCP-6580", "MCP-7207", "MCP-8954",
}

# --- Classification rules. ---
# Automation posts explicit START/END text markers around its daily run.
BANNER_PHRASE = re.compile(r"daily automation (start|end)", re.IGNORECASE)
# Separator rows: a run of 4+ chars that are each "=" or "|".
SEP_RUN = re.compile(r"[=|]{4,}")
# Recurring chores carry a "(... automation)" parenthetical, e.g. "(daily
# automation)", "(Monday automation)". The day-name lives inside it, so stripping
# the whole parenthetical collapses day variants of one chore into one group.
CHORE_SUFFIX = re.compile(r"\(\s*[^()]*\bautomation\s*\)", re.IGNORECASE)

# A separator row with this many word tokens (2+ letters) is likely a real task
# that happens to contain a "====" run, not a pure divider -> flag, don't close.
PROSE_TOKEN_THRESHOLD = 5
WORD_TOKEN = re.compile(r"[A-Za-z]{2,}")

# Standalone day-name tokens, used only for a "these groups may be the same chore"
# heads-up -- never to auto-merge or auto-close.
DAY_TOKENS = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "mon", "tue", "tues", "wed", "weds", "thu", "thur", "thurs", "fri", "sat", "sun",
    "daily", "weekly", "weekday", "weekend",
}


def issue_number(key: str) -> int:
    """Sequential number from an issue key (MCP-1234 -> 1234); -1 if unparseable."""
    try:
        return int(key.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return -1


def is_done(issue: dict) -> bool:
    """True if the issue's statusCategory is Done. Missing category -> not Done."""
    cat = (issue.get("statusCategory") or "").strip().lower()
    return cat == "done"


def normalize_chore(summary: str) -> str:
    """Group key for a chore: drop the (...automation) suffix, lowercase, strip
    punctuation, collapse whitespace. Day variants of one chore collapse together
    because the day-name rides inside the stripped parenthetical."""
    s = CHORE_SUFFIX.sub(" ", summary)
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)   # strip punctuation (keeps letters/digits/_)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def looks_like_prose(summary: str) -> bool:
    """True if a separator-row match reads like a real task (many word tokens)."""
    stripped = SEP_RUN.sub(" ", summary)
    return len(WORD_TOKEN.findall(stripped)) >= PROSE_TOKEN_THRESHOLD


def day_stripped(norm: str) -> str:
    """Chore key with leading/trailing day-name tokens removed, for the same-chore
    heads-up only."""
    tokens = norm.split()
    while tokens and tokens[0] in DAY_TOKENS:
        tokens.pop(0)
    while tokens and tokens[-1] in DAY_TOKENS:
        tokens.pop()
    return " ".join(tokens)


def classify(issues: list[dict]) -> dict:
    """Bucket every non-Done issue. Returns lists of (key, summary) tuples plus the
    grouped chore decisions and diagnostics."""
    banners: list[tuple[str, str]] = []
    dividers: list[tuple[str, str]] = []
    borderline: list[tuple[str, str, str]] = []   # (key, summary, reason)
    reals: list[tuple[str, str]] = []
    chores: list[dict] = []                        # {key, summary, group}
    done_count = 0

    for issue in issues:
        key = issue["key"]
        summary = issue.get("summary") or ""
        if is_done(issue):
            done_count += 1
            continue

        if key in PERMANENT_DIVIDERS:
            dividers.append((key, summary))
        elif BANNER_PHRASE.search(summary):
            banners.append((key, summary))
        elif SEP_RUN.search(summary):
            if looks_like_prose(summary):
                borderline.append((key, summary,
                                   "separator run but reads like a real task"))
            else:
                banners.append((key, summary))
        elif CHORE_SUFFIX.search(summary):
            chores.append({"key": key, "summary": summary,
                           "group": normalize_chore(summary)})
        else:
            reals.append((key, summary))

    # Group chores; keep the highest issue number (newest), close the rest.
    groups: dict[str, list[dict]] = {}
    for c in chores:
        groups.setdefault(c["group"], []).append(c)

    chore_plan: list[dict] = []   # {group, keep, close: [...]}
    for group, members in sorted(groups.items()):
        members.sort(key=lambda c: issue_number(c["key"]), reverse=True)
        chore_plan.append({
            "group": group,
            "keep": members[0],
            "close": members[1:],
        })

    # Heads-up: distinct groups that differ only by a day name -- possibly the same
    # chore the normalizer didn't merge. Informational, never acted on.
    by_daystrip: dict[str, list[str]] = {}
    for group in groups:
        by_daystrip.setdefault(day_stripped(group), []).append(group)
    merge_hints = [sorted(v) for v in by_daystrip.values() if len(v) > 1]

    return {
        "banners": banners,
        "dividers": dividers,
        "borderline": borderline,
        "reals": reals,
        "chore_plan": chore_plan,
        "merge_hints": merge_hints,
        "done_count": done_count,
    }


def render(plan: dict) -> None:
    """Print the human plan (keep-list last) then a MACHINE block for the skill."""
    banners = plan["banners"]
    chore_plan = plan["chore_plan"]
    chore_close = [c for g in chore_plan for c in g["close"]]
    chore_keep = [g["keep"] for g in chore_plan]

    print("=" * 70)
    print("JIRA SPRINT CLEANUP PLAN")
    print("=" * 70)

    print(f"\n### BANNER CLUTTER -> transition to Done ({len(banners)})")
    for key, summary in sorted(banners, key=lambda t: issue_number(t[0])):
        print(f"  CLOSE  {key}  {summary}")

    n_chore_close = len(chore_close)
    print(f"\n### RECURRING CHORES -> keep newest, close older dupes "
          f"({n_chore_close} to close across {len(chore_plan)} group(s))")
    for g in chore_plan:
        if not g["close"]:
            continue   # single occurrence: nothing to close, shown in keep-list
        print(f"  group: \"{g['group']}\"")
        k = g["keep"]
        print(f"    KEEP   {k['key']}  {k['summary']}")
        for c in sorted(g["close"], key=lambda c: issue_number(c["key"])):
            print(f"    CLOSE  {c['key']}  {c['summary']}")

    if plan["borderline"]:
        print(f"\n### BORDERLINE -- REVIEW, not auto-closed ({len(plan['borderline'])})")
        for key, summary, reason in plan["borderline"]:
            print(f"  FLAG   {key}  {summary}   <- {reason}")

    if plan["merge_hints"]:
        print("\n### HEADS-UP: chore groups that may be the same chore")
        for groups in plan["merge_hints"]:
            print(f"  possibly same: {', '.join(repr(g) for g in groups)}")

    # Keep-list last, per the skill's plan format.
    print("\n" + "-" * 70)
    print("KEEP (untouched)")
    print("-" * 70)
    print(f"\nReal tasks ({len(plan['reals'])}):")
    for key, summary in sorted(plan["reals"], key=lambda t: issue_number(t[0])):
        print(f"  keep   {key}  {summary}")

    print(f"\nPermanent dividers ({len(plan['dividers'])}):")
    for key, summary in sorted(plan["dividers"], key=lambda t: issue_number(t[0])):
        print(f"  keep   {key}  {summary}")

    singles = [g["keep"] for g in chore_plan if not g["close"]]
    print(f"\nSingle-occurrence chores kept live ({len(singles)}):")
    for c in sorted(singles, key=lambda c: issue_number(c["key"])):
        print(f"  keep   {c['key']}  {c['summary']}")

    close_all = [k for k, _ in banners] + [c["key"] for c in chore_close]
    kept = (len(plan["reals"]) + len(plan["dividers"])
            + len(chore_keep) + len(plan["borderline"]))

    print("\n" + "=" * 70)
    print(f"SUMMARY: {len(close_all)} to close, {kept} to keep, "
          f"{len(plan['borderline'])} flagged for review")
    if plan["done_count"]:
        print(f"({plan['done_count']} already-Done items in the sprint were "
              f"ignored -- they clear only when the sprint is closed.)")
    print("=" * 70)

    # Machine block: the skill reads CLOSE_ALL to drive transitions.
    print("\n### MACHINE (for the skill, not the plan the user approves) ###")
    print(f"CLOSE_BANNER={','.join(k for k, _ in banners)}")
    print(f"CLOSE_CHORE={','.join(c['key'] for c in chore_close)}")
    print(f"CLOSE_ALL={','.join(close_all)}")
    print(f"COUNTS close={len(close_all)} keep={kept} "
          f"borderline={len(plan['borderline'])} done_ignored={plan['done_count']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify active-sprint Jira issues into a cleanup plan.")
    parser.add_argument("issues_json",
                        help="Path to a JSON file: list of {key, summary, "
                             "statusCategory?, created?} issue objects.")
    args = parser.parse_args()

    try:
        with open(args.issues_json, encoding="utf-8") as fh:
            issues = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read issues JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(issues, list):
        print("error: expected a JSON list of issue objects", file=sys.stderr)
        return 2
    for i, issue in enumerate(issues):
        if not isinstance(issue, dict) or "key" not in issue:
            print(f"error: item {i} is not an issue object with a 'key'",
                  file=sys.stderr)
            return 2

    render(classify(issues))
    return 0


if __name__ == "__main__":
    sys.exit(main())

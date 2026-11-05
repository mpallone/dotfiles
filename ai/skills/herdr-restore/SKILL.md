---
name: herdr-restore
description: Recover a lost local Herdr layout after a reboot, crash, or accidental overwrite. Inspect saved snapshots and backups, reconstruct Codex panes from surviving logs when needed, propose a restore, and verify native session resume. Use for Herdr recovery, not ordinary pane management.
---

# Herdr Restore

Recover the user's requested point in time. Prefer intact layouts; use the Codex
log fallback only when saved layouts cannot establish the requested sessions.
This is local server maintenance and can run outside Herdr. Installation must
run outside the target server so shutdown cannot kill the recovery operation.

Use Python 3.9+ and the bundled `scripts/recovery.py`. Read
[formats and evidence limits](references/formats.md) when interpreting a schema,
using the log fallback, or investigating a failed check.

## Inspect without launching the client

1. Run `herdr session list --json`, `last reboot`, and a local clock/timezone
   check. Select the intended named session and its returned `session_dir`.
   Resolve an ambiguous session or recovery time before proceeding. Do not
   infer a state path from defaults. Keep the Herdr client closed until install
   completes; early launch can overwrite the remaining layout.
2. Read the actual `session.json`, snapshot directory, and backups. Missing
   snapshots are a finding, not a reason to stop investigating. For a latest
   pre-reboot recovery, use reboot time as an exclusive cutoff; the helper
   freezes a graceful shutdown layout before exit events empty its panes.
3. Create a private temporary working directory outside Herdr state. Supply
   explicit dates and offsets; no remembered date, cwd, pane count, or ID is a
   default. For example, from the skill directory:

   ```bash
   python3 scripts/recovery.py inspect \
     --state-dir "$STATE_DIR" --session "$SESSION_NAME" \
     --date "$RECOVERY_DATE" --before "$CUTOFF_ISO" --timezone "$TIMEZONE" \
     --output "$WORK/inspection.json"
   ```

   Add `--expect-agents MIN MAX` only when the user supplied a rough range.
   It is a sanity check, not a target to fill. The recent-session inventory
   defaults to three days before the target date; `--since YYYY-MM-DD` widens it.
   Matching always includes older transcripts.
4. If a server is alive, capture its live workspaces, panes, and foreground
   commands with narrowly targeted CLI reads. Saved JSON can omit a live
   agent's session ID. Permission-denied socket access is unknown state;
   retry read-only checks with the necessary host permissions, not a guessed
   conclusion that the server stopped.

## Select and prepare the proposal

- Compare current-state, snapshot, and backup counts by actual mtime. An intact
  pre-cutoff current session.json is also a recovery candidate. Prefer the latest
  pre-cutoff candidate consistent with the user's expectations. If the latest
  count differs, show the alternatives and explain the proposed selection.
  Distinguish panes with references from panes without references; the latter
  are not proof of plain shells.
- With no suitable snapshot, inspect `log_panes`: closed panes are excluded,
  the latest agent start wins, and only unique one-to-one Codex metadata matches
  are resolved. Include old idle sessions and metadata-only blank sessions.
  Show match deltas; timestamp correlation is an inference. Investigate
  ambiguous/unmatched panes further; do not choose the closest ID or widen the
  match window merely to reach the expected count.
- Preserve current tabs by default. Copy current JSON to `$WORK/current.json`
  and enrich it with verified live session references before preparing.
  Resolve IDs from explicit foreground resume arguments or independently
  corroborated agent records. If live work cannot be identified, explain the
  gap before replacing it. Honor an explicit request to discard current tabs.
- For a saved layout, prepare with:

  ```bash
  python3 scripts/recovery.py prepare --report "$WORK/inspection.json" \
    --snapshot "$CHOSEN_SNAPSHOT" --current-layout "$WORK/current.json" \
    --output "$WORK/plan.json"
  ```

  Use `--reconstruct` instead of `--snapshot` for the log fallback.
  Use `--current replace` instead of `--current-layout` when replacement was
  requested. The fallback creates one tab per recovered pane; original split
  geometry and custom names are not recoverable from those logs.

Present a table with original pane/tab/workspace, cwd, agent, session ID, source,
and validation result. Show saved launch_argv commands too: a pane without a
session reference can restart a command when the client launches. Show counts,
populated versus blank sessions,
and additional top-level sessions modified on the target date outside the
chosen layout. These extras can include intentionally closed sessions. Include
their cwd and IDs with an example `cd <cwd> && codex resume <id>`.

Read `herdr --version`, `herdr integration status`, and the actual session config.
Confirm native resume is enabled for the selected agents in that installed
version. The verified baseline is Herdr 0.9.1, schema 3, Codex integration v8;
newer versions require checking their actual capability/config, not automatic
upgrades. Intact snapshots can reference other agents, but this helper checks
only Codex's own store: verify other agents' IDs and native resume separately.

Show the concrete plan and obtain approval before stopping a server or changing
its state. Approval already given for that same proposal remains valid. If
evidence changes, recheck it and seek new approval only for a material change.
Do not require another permission just to run read-only investigation.

## Install and verify

After approval, from outside the target Herdr server:

```bash
python3 scripts/recovery.py install --plan "$WORK/plan.json" --approved
```

The installer rechecks evidence and session identity, stops the selected server,
backs up the state it saved during shutdown, verifies the backup, and atomically
replaces only `session.json`. It leaves logs, sockets, integrations, old backups,
and agent transcripts untouched. It does not launch the client.

Launch/attach the same named Herdr session in a real terminal, then run:

```bash
python3 scripts/recovery.py verify --plan "$WORK/plan.json"
```

Use returned live pane IDs to read each agent's recent screen. Command/reference
matches alone do not prove history loaded: confirm the expected conversation
and a usable prompt, including the expected blank sessions. Do not submit work
or answer permission/authentication dialogs during verification.

Report each resumed session, blank session, plain shell, failed pane, and backup
path. If a metadata-only blank cannot resume, open fresh Codex there only when
that fallback was included in the approved plan. On an install error, keep the
client closed, inspect the reported state/backup, and explain the failure before
retrying a mutation. Do not restore the whole backup merely because one pane
failed; it can replace successfully recovered work.

# Formats and evidence limits

The helper implements the layout format inspected in Herdr 0.9.1. It rejects
other snapshot versions. Check the installed release's source when a format
differs; do not add fields based on an online example from another version.

## Saved layout

Schema 3 stores `workspaces[] -> tabs[] -> panes[raw_id]`. Each pane has an
absolute `cwd` and can contain:

```json
{
  "agent_session": {
    "source": "herdr:codex",
    "agent": "codex",
    "kind": "id",
    "value": "11111111-1111-4111-8111-111111111111"
  }
}
```

The tab's layout tree contains `{"Pane": raw_id}` leaves or a `Split` with
`direction`, `ratio`, `first`, and `second`. Snapshot restore preserves split
geometry. Merging layouts remaps internal pane IDs to avoid collisions, retains
valid public pane/tab numbers, and lets Herdr assign a new workspace ID on a
collision. Discover the resulting public IDs through the live API.

The verified release defaults `[session].resume_agents_on_restore` to true.
Its Codex native command is `codex resume <ID>`. The installed config and
integration status must still be checked for each recovery.

Herdr 0.9.1's persistence source has no snapshot-rotation directory. A missing
`session-snapshots/` can be consistent with the installed version. Later
versions can behave differently.

Source baseline:
- [snapshot schema](https://github.com/herdrdev/herdr/blob/065ef9d6a531c49fb8bee7e818ef837065b21ee9/src/persist/snapshot.rs)
- [native resume](https://github.com/herdrdev/herdr/blob/065ef9d6a531c49fb8bee7e818ef837065b21ee9/src/agent_resume.rs)
- [session defaults](https://github.com/herdrdev/herdr/blob/065ef9d6a531c49fb8bee7e818ef837065b21ee9/src/config/model.rs)

## Codex fallback

Read `<codex-home>/sessions/**/*.jsonl`. The first record is `session_meta`;
its payload supplies `id`, `cwd`, and original `timestamp`. The outer record
timestamp can reflect a later write, including shutdown. Use the payload time
for process-start matching.

Exclude metadata with `parent_thread_id`, `source.subagent`, or a guardian
thread source. A source named `vscode` can still describe a terminal Codex
session, so it is not a reason to exclude the file. A transcript containing
only metadata is a legitimate blank session, even if it has no SQLite row.
The helper opens `state_5.sqlite` read-only for optional titles; it does not
depend on those titles for matching.

Replay Herdr's UTC log timestamps against the requested offset-aware cutoff.
The helper tracks `pane.spawn.start`, `agent changed`, `pane.exit`, and graceful
server shutdown. It associates tab-create events when those logs are present.
An `agent=None` transition must not be misread as the preceding
`previous_agent=Some(Codex)`.

A unique creation time within the match window supplies a proposed match,
not proof that no unrecorded process/session exists. The helper refuses multiple
candidates or reuse of one candidate across two panes. Missing/rotated logs,
resuming an older ID, changed logging, non-Codex agents, or surviving shells
without a known cwd require additional evidence. Do not represent these cases
as a complete reconstruction.

Modification time is used only for snapshot ordering and the extra-session
inventory. It cannot identify every pane open on a past day. Idle sessions can
be older than that day; resumed files can have newer mtimes.

## Plan and install boundaries

Plans and inspection files contain private local paths and session metadata.
Write them into a private temporary directory; never commit them or real
transcripts. Tests must use synthetic IDs, paths, prompts, and logs.

A prepared plan records source fingerprints and the complete candidate layout.
Install rechecks those fingerprints before stopping the server. Appended journal
records are allowed only when the recorded prefix remains unchanged. A stale or
rewritten source needs reinspection. UI focus saves can also stale a plan; check
whether its approved session selection actually changed before asking again.

A shutdown can flush sidebar or agent metadata. Back up that final state rather
than requiring byte equality with the pre-stop save; workspace/tab/pane topology
and cwd must remain unchanged. Never overwrite an existing backup. For preserved
tabs, a newly saved session reference must match the reviewed live identity.
A conflicting identity or a removed reference aborts installation. The atomic
staging file lives beside the Herdr directory and is removed on failure, leaving
only the backed-up and installed session files inside Herdr state.

The installer checks a real Unix socket. EPERM/EACCES/timeouts are failures to
verify access, not stopped-server results. Use host permissions when required.
It refuses to install from inside Herdr and leaves client launch to the agent.

Verification checks native session references, foreground commands, cwd, and
pane count. Read screens afterwards; an agent process can be sitting at an
authentication, trust, error, or picker screen.

The helper automates foreground-command checks for Codex and Claude. Other
agents return an incomplete command check and need manual process/screen
verification; do not label that result as a successful automated verification.

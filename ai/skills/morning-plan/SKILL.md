---
name: morning-plan
description: >
  Run Mark's interactive morning planning ritual against his personal Jira board
  (project MCP), or clean up the sprint's automation clutter. Planning mode reads
  the current sprint, interviews him item-by-item with tappable options to sort
  tasks into effort buckets (stored as Jira labels), closes anything he reports
  done, and ends with a short ordered plan for the day. Sprint cleanup mode
  closes automation banner rows and older duplicates of recurring chores — it
  always prints a full plan and waits for an explicit "go", transitions to Done
  (never deletes), and never touches the backlog or the permanent divider rows.
  Use whenever Mark says "morning plan", "plan my day", "run my daily planning",
  "triage my sprint/jira", "what should I do today", or otherwise wants to
  review, sort, or prioritize his personal Jira tasks — and for cleanup alone,
  "clean up my jira sprint", "dedupe my to-do list", "clear the automation
  clutter", or "tidy up my active sprint".
---

# Morning Plan

An interactive daily-planning ritual plus a sprint-cleanup sweep over Mark's
personal Jira. Claude is the frontend; Jira is a dumb backing store. Two modes
share the constants below:

- **Planning mode** (default) — the item-by-item triage interview (steps 1–4).
  Bucket membership lives in **labels** (the connector cannot re-rank issues,
  so rank order and divider tickets are ignored).
- **Sprint cleanup mode** — closes automation banner rows and dedupes
  recurring chores. Runs standalone when Mark asks for cleanup ("clean up my
  jira sprint", "dedupe my to-do list", "clear the automation clutter", "tidy
  up my active sprint"), and is auto-run from planning step 1 when duplicates
  turn up. See **Sprint cleanup mode** below.

Requires the **Atlassian Rovo connector** enabled in the chat — if its tools
are unavailable, say so and stop.

## Constants

- cloudId: `f438107c-ea02-4718-a002-5ce3646a61dd`
- Project key: `MCP`
- Scope: **current sprint only** — every JQL includes `sprint in openSprints()`.
  Never read or write the backlog. (`openSprints()` never returns backlog
  issues, so the backlog is safe by construction. Never widen the query.)
- Bucket labels (exact strings): `daily-target`, `prioritize`, `aspirational`,
  `not-daily-goals`
- Workflow transitions (global, verified): `11` = To Do, `31` = Done
- Separator / banner rows — structural rows that must NEVER be triaged.
  Identify by parent epic, never by summary pattern:
  - **Permanent structure — never surfaced.** Any child of epic `MCP-2213`
    ("separators"). Exclude from triage and **never prompt, list, mention,
    label, close, or modify** — no matter how banner-like the summary looks
    (`^ Sunday (day)`, `===== ^ right after planning =====`,
    `v ==== v new v ==== v`, etc.). Parentage is the only signal; summary text
    is never a reason to surface one. Sprint cleanup mode protects these rows
    by the same parentage rule.
  - **Disposable automation banners**: separator-style summaries NOT parented to
    `MCP-2213` (e.g. `DAILY AUTOMATION START/END` rows Jira Automation
    regenerates). Also excluded from bucket triage; they are disposable clutter:
    list them once in the final brief and close them only if Mark says to — bulk
    cleanup belongs to Sprint cleanup mode below, not triage. Never a
    tap-prompt.

## Planning workflow

### 1. Read (no writes yet)

```
searchJiraIssuesUsingJql
  jql: project = MCP AND sprint in openSprints() AND statusCategory != Done
       ORDER BY updated DESC
  fields: ["summary", "labels", "status", "parent"]
```

Group results by existing bucket label — this grouping is only for the
snapshot, not a filter on who gets interviewed. Present a compact snapshot:
yesterday's buckets (from labels) plus the total count of open, non-separator
items. The entire open, non-separator set is the triage queue (see Interview),
whether or not an item already carries a bucket label.

**Duplicate check**: if two or more open non-separator issues share effectively
the same summary (typical cause: automation re-created a recurring chore that
was never closed), do not triage them here — and do not ask whether to clean
them up. **Automatically run Sprint cleanup mode** (below). Just tell Mark
duplicates were found, then switch into it. "Automatically run" means
auto-*start* cleanup, never auto-*close*: cleanup mode keeps its
non-negotiable gate — it prints a full plan and waits for Mark's explicit "go"
before transitioning anything — and the planning flow must not bypass that
gate. Capture which issues cleanup closed so they can be reported in the final
brief (step 4). Resume the morning plan with whatever survives cleanup.

### 2. Interview

Triage **every** open (not-done), non-separator item, whether or not it already
carries a bucket label — nothing is carried over untouched; yesterday's labeled
items get re-triaged fresh each run. Re-triage is automatic and unconditional:
**never ask Mark whether he wants to revisit or re-triage his not-done items —
he always does.** Go straight into the item-by-item questions; never gate the
interview behind a "want to revisit yesterday's items?" yes/no prompt. Rules:

- Batches of **at most 6 items** per round, using tappable single-select
  options. Two different caps apply: each *question* offers at most 4 options —
  **Daily target / Aspirational / Not daily goals / Mark as done** — and each
  tappable prompt (`AskUserQuestion`) holds at most 4 *questions*. So a round of
  6 cannot be a single prompt: deliver it as two consecutive tap-prompts (e.g.
  3+3), then pause for the next round of 6. `prioritize` stays a valid bucket
  via typed reply (it saw zero use in the first session — promote it back into
  the tap set if Mark starts using it).
- **"Mark as done" is an action, not a label**: on selection, first pull the
  issue's current state (`getJiraIssue`) to confirm it isn't already Done or
  otherwise changed (see **Verify state before writing**), then transition it
  to Done (`transitionJiraIssue`, id `31`) and write no bucket label.
- Embed a suggested bucket in each question, always computed from the heuristic
  below — independent of any bucket label the item already carries. A stored
  label never pre-selects the answer; it is only context. You may note an item's
  current bucket briefly ("currently: aspirational") for context, but the
  *suggestion* is the heuristic result:
  - **Low-effort must-dos rise to the top** → suggest `daily-target`
    (examples: litter box, trash to curb, cat feeder).
  - **High-effort items and exercise-like items** → suggest `aspirational`.
  - Time-pinned items (due today, "(Sunday automation)" on a Sunday) lean
    `daily-target`; blocked or deferred-dependency items lean
    `not-daily-goals`.
  - Mark overrides freely — his answer always wins over the heuristic.
- Handle free-text answers, not just taps:
  - "done" / "I did it" / "wife owns it now" → same as tapping "Mark as done".
    Whenever an issue is closed this way and its summary carries an
    "(… automation)" tag and ownership changed permanently, remind Mark once
    to edit the generating rule in Jira **Project settings → Automation**.
  - A different bucket name → use it.
  - "skip" → leave the item's current label untouched (an unlabeled item stays
    unlabeled; an already-labeled item keeps its existing bucket) and mention it
    in the final brief. Skipping never erases a bucket.

### 3. Write labels (batched, after the interview)

For each triaged open issue, first re-fetch its current state with
`getJiraIssue` (see **Verify state before writing**), then set its bucket via
`editJiraIssue` with `fields: {"labels": [...]}`. The fresh read is also what
lets you honor the non-bucket-label exception below — you can only preserve a
label that appeared since step 1 if you just read it.

**Labels are owned by this system** — Mark does not use Jira labels for
anything else. Set `labels` to exactly the one bucket label (the write replaces
the whole array, which is the desired behavior). Rare exception: if an
unexpected non-bucket label ever appears on an issue, keep it in the array and
mention it in the brief. If an edit fails, report the specific issue key and
error, and continue with the rest — no silent failures.

### 4. Final brief

Formatted for a phone screen, in this order:

- **Closed this session** — print this summary *first*, before the day's plan.
  Cover everything closed this run, from both sources: duplicates and banners
  closed by the auto-run sprint cleanup (step 1), and items Mark marked done
  during the interview. One line each (key + summary). If nothing was closed,
  say so in a single line or omit the section — don't manufacture one.

Then the day's plan:

- **Daily target** — ordered quick-wins-first (lowest effort at top).
- **Aspirational**, then **Not daily goals** — one line each.
- Anything skipped during the session.
- Any disposable automation banners present (separator-style rows **not** under
  `MCP-2213`) — listed once as clutter, closed only if Mark asks. Permanent
  structure (children of `MCP-2213`) never appears here.
- If `daily-target` exceeds ~5 items, say so once, plainly: "the less
  ambitious, the more achievable" — and name the best demotion candidates.
  Don't nag beyond that.

## Planning guardrails

- Reads before writes; all label writes happen in step 3, transitions may
  happen mid-interview when Mark reports something done.
- **Verify state before writing**: the step-1 snapshot goes stale as the
  interview runs — Jira Automation can re-create or close issues, and Mark may
  edit in the Jira UI in parallel. Before *any* state change to an issue (a Done
  transition in step 2 or a label write in step 3), pull that one issue's
  current state with `getJiraIssue` and confirm the planned action still holds
  against it. If the fresh state contradicts the decision (already Done, status
  moved, an unexpected label present), surface the discrepancy and re-confirm
  with Mark before writing — never act on the stale snapshot.
- Never touch issues outside the open sprint; never surface, prompt on, or
  modify permanent structure (any child of `MCP-2213`); close disposable
  automation banners only on explicit request; never edit Automation rules
  yourself (Mark does that in the Jira UI).
- Fine-grained order *within* a bucket is session-only. If Mark wants an
  artifact of the day's exact ordering, offer to write it as a comment on the
  `week planning ritual` ticket (or the topmost daily-target item) — don't do
  this unprompted.
- Every not-done, non-separator item is re-triaged on every run —
  automatically, never gated behind a "want to revisit?" question. A stored
  bucket label neither suppresses the prompt nor pre-selects the answer (the
  suggestion is recomputed from the effort heuristic each time). Permanent
  structure (children of `MCP-2213`) and disposable automation banners remain
  excluded from triage per the rules above.

## Sprint cleanup mode

Close the automation clutter piling up in the active sprint and dedupe the
recurring chores, leaving real work and board structure untouched. The
classifier lives in `scripts/classify.py`; the cleanup constants below live
there too, so they are not re-derived each run.

### The gate (non-negotiable)

**Print the full plan and STOP. Do not transition a single issue until Mark
replies "go".** The plan lists every affected ticket (key + summary + exact
action), grouped into Banner clutter, Recurring chores, Borderline, and a
keep-list last. `scripts/classify.py` prints exactly this format — show its
plan output, then wait. "go" (or an explicit equivalent) is the only signal to
mutate. Anything short of that — silence, a question, "looks good?" from Mark
as a question — is not approval.

### Cleanup constants

The shared constants above apply (cloudId, project `MCP`, active sprint only,
never the backlog). In addition:

- Base JQL: `project = MCP AND sprint in openSprints()`. Never widen it.
- **Done transition id:** `31` in this project — but **verify it** (see step
  4), don't hardcode blindly.
- **Permanent dividers, never touched:** any child of epic `MCP-2213` (see
  Constants). They look exactly like automation separator rows; their
  parentage is the only thing marking them as board structure.
- **Title-only tickets.** Description is null on these issues — treat the
  `summary` as the title. Never rely on description.

### 1. Fetch the active sprint — paginate fully

Call `searchJiraIssuesUsingJql` with:
- `cloudId`: the constant above
- `jql`: `project = MCP AND sprint in openSprints() AND statusCategory != Done`
  (the base scope + the To-Do filter — we only act on non-Done items)
- `maxResults`: `100` (the tool caps here)
- `fields`: `["summary", "status", "created", "parent"]`

The sprint can hold 200+ issues. **Loop on `nextPageToken`:** re-call with the
same `jql` and the returned `nextPageToken` until no token comes back. Do not set
`computeIssueCount` on these calls. Accumulate every page — a partial fetch
produces a wrong plan.

For each issue collect: `key`, `summary`, `status.statusCategory` (the `key`:
`new` / `indeterminate` / `done`), `created`, and `parent` (the parent issue
key from `fields.parent.key`, or null when there is no parent). Write them as
a JSON list to a scratch file, e.g.:

```json
[{"key": "MCP-1234", "summary": "...", "statusCategory": "new", "created": "...", "parent": "MCP-2213"}]
```

### 2. Classify

Run the bundled classifier (deterministic — same rules every run):

```bash
python scripts/classify.py <path-to-issues.json>
```

It buckets every non-Done issue and prints the plan plus a trailing `### MACHINE`
block. The rules it applies (also documented here so Mark can audit them):

- **Permanent dividers** — any child of epic `MCP-2213`. Never touched, no
  matter what the summary matches; excluded from every other rule below.
- **Banner clutter** — summary matches `DAILY AUTOMATION START`/`END`, or
  contains a run of 4+ `=` or `|` chars. A separator-run summary that reads
  like prose (5+ word tokens) is **flagged Borderline, not closed**.
- **Recurring chores** — summary contains a `(... automation)` parenthetical and
  is not a banner. Grouped by normalized summary (strip the `(...automation)`
  suffix, lowercase, strip punctuation) so day-name variants of one chore collapse
  together.
- **Real tasks** — everything else. Never auto-closed. This deliberately
  includes automation-*created* items that lack a `(...automation)` suffix (e.g.
  a reminder ticket) — those are real tasks, not clutter.

### 3. Present the plan and STOP

Show the classifier's plan output verbatim (or lightly reformatted — keep every
key, summary, and action, and keep the keep-list last). Call out the Borderline
section and any "may be the same chore" heads-up explicitly; do not resolve them
yourself. **Wait for "go".** See the gate above.

### 4. Verify the Done transition (on approval, before the first mutation)

Call `getTransitionsForJiraIssue` on the **first** target key. Find the
transition whose destination is a Done status (statusCategory `done`, usually
named "Done"). Confirm its id is `31`; if the project has changed it, use the id
you found. If no Done transition is available on that issue, **stop and report**
— do not guess.

### 5. Transition the targets to Done

The plan can be stale: an arbitrary approval wait sits between the step-1 fetch
and this mutation, and in that window Jira automation regenerates/closes rows
and Mark may have closed some by hand. So for every key in the classifier's
`CLOSE_ALL` list, **pull the issue's current state with `getJiraIssue`
immediately before mutating it** and confirm the decision still holds against
up-to-date state — it must still be non-Done and still match what the plan
classified (summary unchanged). Only then call `transitionJiraIssue` with
`cloudId`, `issueIdOrKey`, and `transition: {id: "<verified id>"}`. If the fresh
read contradicts the plan (already Done, or the summary changed so it is no
longer clutter), **skip it and report** — never transition against the stale
plan. **Transition to Done — never delete.** Leave Borderline items, real
tasks, single-occurrence chores, and the permanent dividers alone.

### 6. Report

State the final tally: **N closed, M kept** (and how many were flagged
Borderline for Mark to handle). Then note the two things this does **not** fix:

1. **Already-Done items still sit in the sprint.** Closing issues doesn't remove
   them — Done items only leave when the sprint itself is closed. (Report the
   count from a one-shot `project = MCP AND sprint in openSprints() AND
   statusCategory = Done` query with `computeIssueCount: true` if useful.)
2. **The clutter comes back.** Jira automation regenerates banner rows and
   recurring chores on its next scheduled run; this cleanup is a sweep, not a
   fix at the source.

### Hard rules (learned the hard way)

- Transition to Done, **never delete**.
- **Plan first, mutate only after "go".** No exceptions.
- **Surface ambiguity, never guess.** Borderline items are flagged, not closed.
- **Verify state before writing.** The plan is built before an arbitrary
  approval wait; re-read each target with `getJiraIssue` immediately before
  closing it and skip anything whose current state no longer matches the plan
  (already Done, summary changed). Never mutate against the stale snapshot.
- Never touch the backlog, real tasks, or the permanent dividers (children of
  `MCP-2213`).
- A partial fetch is a wrong plan — paginate to the last page before classifying.

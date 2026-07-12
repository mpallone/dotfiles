---
name: jira-sprint-cleanup
description: |
  Clean up the active sprint of my personal Jira to-do project (MCP): close the
  automation banner rows and the older duplicates of each recurring chore, keep
  the newest copy of every chore plus every real task, and never touch the
  backlog or the 6 permanent dividers. Transitions to Done -- never deletes --
  and ALWAYS prints a full plan and waits for my explicit "go" before changing
  anything. Use when I say "clean up my jira sprint", "dedupe my to-do list",
  "clear the automation clutter", or "tidy up my active sprint".
---

# jira-sprint-cleanup

Close the automation clutter piling up in my active Jira sprint and dedupe the
recurring chores, leaving real work and board structure untouched. Access is via
the Atlassian Rovo MCP. The classifier lives in `scripts/classify.py`; the
constants below live there too, so they are not re-derived each run.

## The gate (non-negotiable)

**Print the full plan and STOP. Do not transition a single issue until I reply
"go".** The plan lists every affected ticket (key + summary + exact action),
grouped into Banner clutter, Recurring chores, Borderline, and a keep-list last.
`scripts/classify.py` prints exactly this format -- show its plan output, then
wait. "go" (or an explicit equivalent) is the only signal to mutate. Anything
short of that -- silence, a question, "looks good?" from me as a question -- is
not approval.

## Scope and constants

- **Project:** `MCP`  **cloudId:** `f438107c-ea02-4718-a002-5ce3646a61dd`
- **Active sprint only.** Base JQL: `project = MCP AND sprint in openSprints()`.
  `openSprints()` never returns backlog issues, so the backlog is safe by
  construction. Never widen this query.
- **Done transition id:** `31` in this project -- but **verify it** (see step 5),
  don't hardcode blindly.
- **6 permanent dividers, never touched:** `MCP-1193, MCP-1550, MCP-5493,
  MCP-6580, MCP-7207, MCP-8954`. They look exactly like automation separator
  rows; their key is the only thing marking them as board structure.
- **Title-only tickets.** Description is null on these issues -- treat the
  `summary` as the title. Never rely on description.

## Workflow

### 1. Fetch the active sprint -- paginate fully

Call `searchJiraIssuesUsingJql` with:
- `cloudId`: the constant above
- `jql`: `project = MCP AND sprint in openSprints() AND statusCategory != Done`
  (the base scope + the To-Do filter -- we only act on non-Done items)
- `maxResults`: `100` (the tool caps here)
- `fields`: `["summary", "status", "created"]`

The sprint can hold 200+ issues. **Loop on `nextPageToken`:** re-call with the
same `jql` and the returned `nextPageToken` until no token comes back. Do not set
`computeIssueCount` on these calls. Accumulate every page -- a partial fetch
produces a wrong plan.

For each issue collect: `key`, `summary`, `status.statusCategory` (the `key`:
`new` / `indeterminate` / `done`), and `created`. Write them as a JSON list to a
scratch file, e.g.:

```json
[{"key": "MCP-1234", "summary": "...", "statusCategory": "new", "created": "..."}]
```

### 2. Classify

Run the bundled classifier (deterministic -- same rules every run):

```bash
python scripts/classify.py <path-to-issues.json>
```

It buckets every non-Done issue and prints the plan plus a trailing `### MACHINE`
block. The rules it applies (also documented here so I can audit them):

- **Banner clutter** -- summary matches `DAILY AUTOMATION START`/`END`, or
  contains a run of 4+ `=` or `|` chars. The 6 divider keys are excluded even
  when they match. A separator-run summary that reads like prose (5+ word tokens)
  is **flagged Borderline, not closed**.
- **Recurring chores** -- summary contains a `(... automation)` parenthetical and
  is not a banner. Grouped by normalized summary (strip the `(...automation)`
  suffix, lowercase, strip punctuation) so day-name variants of one chore collapse
  together.
- **Real tasks** -- everything else. Never auto-closed. This deliberately
  includes automation-*created* items that lack a `(...automation)` suffix (e.g.
  a reminder ticket) -- those are real tasks, not clutter.

### 3. Present the plan and STOP

Show the classifier's plan output verbatim (or lightly reformatted -- keep every
key, summary, and action, and keep the keep-list last). Call out the Borderline
section and any "may be the same chore" heads-up explicitly; do not resolve them
yourself. **Wait for "go".** See the gate above.

### 4. Verify the Done transition (on approval, before the first mutation)

Call `getTransitionsForJiraIssue` on the **first** target key. Find the
transition whose destination is a Done status (statusCategory `done`, usually
named "Done"). Confirm its id is `31`; if the project has changed it, use the id
you found. If no Done transition is available on that issue, **stop and report**
-- do not guess.

### 5. Transition the targets to Done

For every key in the classifier's `CLOSE_ALL` list, call `transitionJiraIssue`
with `cloudId`, `issueIdOrKey`, and `transition: {id: "<verified id>"}`.
**Transition to Done -- never delete.** Leave Borderline items, real tasks,
single-occurrence chores, and the 6 dividers alone.

### 6. Report

State the final tally: **N closed, M kept** (and how many were flagged
Borderline for me to handle). Then note the two things this does **not** fix:

1. **Already-Done items still sit in the sprint.** Closing issues doesn't remove
   them -- Done items only leave when the sprint itself is closed. (Report the
   count from a one-shot `project = MCP AND sprint in openSprints() AND
   statusCategory = Done` query with `computeIssueCount: true` if useful.)
2. **The clutter comes back.** Jira automation regenerates banner rows and
   recurring chores on its next scheduled run; this cleanup is a sweep, not a
   fix at the source.

## Hard rules (learned the hard way)

- Transition to Done, **never delete**.
- **Plan first, mutate only after "go".** No exceptions.
- **Surface ambiguity, never guess.** Borderline items are flagged, not closed.
- Never touch the backlog, real tasks, or the 6 dividers.
- A partial fetch is a wrong plan -- paginate to the last page before classifying.

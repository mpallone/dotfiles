---
name: morning-plan
description: >
  Run Mark's interactive morning planning ritual against his personal Jira board
  (project MCP), or clean up the sprint's automation clutter. Planning mode reads
  the current sprint, interviews him item-by-item with tappable options to sort
  tasks into effort buckets (stored as Jira labels), closes anything he reports
  done, and ends every single answer — not just the last one — with the full
  ordered plan for the day. Sprint cleanup mode closes automation banner rows
  and older duplicates of recurring chores — it
  runs unattended with no approval prompt: it prints the plan, closes the
  targets immediately, then reports what changed. It transitions to Done (never
  deletes), and never touches the backlog or the permanent divider rows.
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

## Always end every answer with the full day plan

**Every** message sent while this skill is running ends with the full day plan —
no exceptions, in both modes. Not just the final brief: the opening snapshot,
each interview prompt, the cleanup plan, the cleanup report, the final brief,
and any follow-up answer afterward all carry it as their last block. If a reply
has room for nothing else, it still has room for this.

Three subsections, in this order — **Today**, **Aspirational**, **Not today** —
each a bold header on its own line, followed by bullets, one item per bullet:

```
**Today's plan**

**Today**
- MCP-14061 — pull trash to curb
- MCP-14063 — order wipes/diapers/TP

**Aspirational**
- MCP-14057 — laundry progress
- MCP-14060 — cardio or strength training

**Not today**
- MCP-14058 — YNAB reconcile
- MCP-14046 — meal plan

**Still to triage:** 3 · **Closing today:** MCP-14012, MCP-14030
```

Formatting rules — the layout is the point, a wall of text is not readable on
a phone:

- **Bullets only. Never a numbered list.** A numbered item swallows every
  indented line under it, which collapses the whole block into one paragraph.
- **One item per bullet**, `KEY — summary`. Never join items on one line with
  `·` or commas.
- **Blank line before and after every subsection header.** Headers are bold
  text on their own line, never a bullet and never inline with the first item.
- **Never indent** a bullet or a header — everything sits at the left margin.
- Bucket → subsection: `daily-target` → **Today**, `aspirational` →
  **Aspirational**, `not-daily-goals` → **Not today**. **Today** is ordered
  quick-wins-first (lowest effort at top); the order carries that, so no
  numbering is needed. An item labeled `prioritize` goes in **Today** with a
  trailing `(prioritize)`.
- Omit a subsection entirely when it is empty — no empty headers.
- **The trailing counts line** is one line, not a subsection: untriaged count
  and the keys closing this session. Drop either half when it is zero.

Content rules:

- **Mid-session it reflects decisions so far**, which are not yet written to
  Jira: items Mark has already bucketed sit in their new subsection, items he
  answered "done" on go to *Closing today*, and everything still queued is
  counted in *Still to triage*. Count the untriaged items, don't list them —
  the queue can be long.
- **Reading it costs no tool calls.** It is rendered from the step-1 snapshot
  plus the answers recorded so far. It never triggers a Jira read and never
  interrupts the write-free interview (see step 2).
- Permanent structure (children of `MCP-2213`) never appears in it.
- In the final brief the plan block *is* the day's plan section — print it once
  there, after **Closed this session**, not twice.

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
them up. **Automatically run Sprint cleanup mode** (below) start to finish —
it needs no approval. Just tell Mark duplicates were found, then switch into
it, close what it targets, and come back. Capture which issues cleanup closed
so they can be reported in the final brief (step 4). Resume the morning plan
with whatever survives cleanup.

### 2. Interview

Triage **every** open (not-done), non-separator item, whether or not it already
carries a bucket label — nothing is carried over untouched; yesterday's labeled
items get re-triaged fresh each run. Re-triage is automatic and unconditional:
**never ask Mark whether he wants to revisit or re-triage his not-done items —
he always does.** Go straight into the item-by-item questions; never gate the
interview behind a "want to revisit yesterday's items?" yes/no prompt. Rules:

- Deliver the triage as tappable single-select prompts. **Fill every prompt
  to the maximum number of questions AskUserQuestion allows. As of this
  writing the max is 4, so include at least 4 items per prompt** — fewer only
  when fewer than 4 remain in the queue. Never send a 3-item prompt when a
  4th item is waiting. Each
  *question* offers at most 4 options — **Daily target / Aspirational / Not
  daily goals / Mark as done**. Pause for Mark's answers after each prompt,
  then continue with the next full prompt until the queue is done.
  `prioritize` stays a valid bucket via typed reply (it saw zero use in the
  first session — promote it back into the tap set if Mark starts using it).
- **The interview is write-free.** Between prompts the only tool call is the
  next `AskUserQuestion` — never pause the interview to read or write Jira.
  Every answer (bucket or done) is just recorded; all Jira calls wait for
  step 3. The message that carries each prompt still ends with the full
  day plan (see **Always end every answer with the full day plan**) — it is
  rendered from state already in hand, so it costs no tool call and does not
  break the write-free rule.
- **"Mark as done" is a recorded decision, not an immediate action**: note the
  issue as pending-done and move straight to the next prompt. The actual Done
  transition happens in step 3 with the other writes; no bucket label is
  written for these items.
- **Never recommend or suggest a bucket in the questions** — no embedded
  suggestions, no "recommended" markers; Mark finds them clutter. His answer
  is the only input. A stored label never pre-selects the answer either; you
  may note an item's current bucket briefly ("currently: aspirational") as
  factual context, nothing more.
- Handle free-text answers, not just taps:
  - "done" / "I did it" / "wife owns it now" → same as tapping "Mark as done"
    (recorded now, closed in step 3). Whenever an issue closed this way
    carries an "(… automation)" tag in its summary and ownership changed
    permanently, remind Mark once — in the final brief — to edit the
    generating rule in Jira **Project settings → Automation**.
  - A different bucket name → use it.
  - "skip" → leave the item's current label untouched (an unlabeled item stays
    unlabeled; an already-labeled item keeps its existing bucket) and mention it
    in the final brief. Skipping never erases a bucket.

### 3. Take actions (after the whole interview)

Every Jira write happens here, once the triage queue is empty. Two passes:

1. **Close the pending-done items.** For each issue marked done in the
   interview, re-fetch its current state with `getJiraIssue` (see **Verify
   state before writing**), then transition it to Done (`transitionJiraIssue`,
   id `31`). No bucket label is written for these.
2. **Write bucket labels.** For each remaining triaged issue, re-fetch its
   current state with `getJiraIssue`, then set its bucket via `editJiraIssue`
   with `fields: {"labels": [...]}`. The fresh read is also what lets you
   honor the non-bucket-label exception below — you can only preserve a label
   that appeared since step 1 if you just read it.

**Labels are owned by this system** — Mark does not use Jira labels for
anything else. Set `labels` to exactly the one bucket label (the write replaces
the whole array, which is the desired behavior). Rare exception: if an
unexpected non-bucket label ever appears on an issue, keep it in the array and
mention it in the brief. If a transition or edit fails, report the specific
issue key and error, and continue with the rest — no silent failures.

### 4. Final brief

Print only after every step-3 action has completed — actions first, then the
report. Formatted for a phone screen, in this order:

- **Closed this session** — print this summary *first*, before the day's plan.
  Cover everything closed this run, from both sources: duplicates and banners
  closed by the auto-run sprint cleanup (step 1), and items Mark marked done
  during the interview. One line each (key + summary). If nothing was closed,
  say so in a single line or omit the section — don't manufacture one.

Then the day's plan — the same **Today / Aspirational / Not today** block every
other answer ends with, now reflecting the writes that just landed. Same
formatting rules; no numbered lists, one item per bullet.

- Anything skipped during the session.
- Any disposable automation banners present (separator-style rows **not** under
  `MCP-2213`) — listed once as clutter, closed only if Mark asks. Permanent
  structure (children of `MCP-2213`) never appears here.
- If **Today** exceeds ~5 items, say so once, plainly: "the less
  ambitious, the more achievable" — and name the best demotion candidates.
  Don't nag beyond that.

## Planning guardrails

- **Every answer ends with the full day plan** — snapshot, every interview
  prompt, cleanup output, final brief, and every follow-up. Never send a
  message in this skill without it.
- Reads before writes; **all** writes — label edits and Done transitions —
  happen in step 3, after the interview finishes. Never pause the interview
  to call Jira; done-answers are recorded and closed in step 3.
- **Verify state before writing**: the step-1 snapshot goes stale as the
  interview runs — Jira Automation can re-create or close issues, and Mark may
  edit in the Jira UI in parallel. Before *any* state change to an issue (a Done
  transition or a label write, both in step 3), pull that one issue's
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
  bucket label neither suppresses the prompt nor pre-selects the answer — and
  the questions never embed a suggested bucket. Permanent
  structure (children of `MCP-2213`) and disposable automation banners remain
  excluded from triage per the rules above.

## Sprint cleanup mode

Close the automation clutter piling up in the active sprint and dedupe the
recurring chores, leaving real work and board structure untouched. The
classifier lives in `scripts/classify.py`; the cleanup constants below live
there too, so they are not re-derived each run.

### No approval prompt — run it end to end

**Never ask Mark to confirm the cleanup.** Fetch, classify, close, report — in
one pass, no "reply go", no "shall I proceed?", no `AskUserQuestion`. Print the
plan for the record (it lists every affected ticket: key + summary + exact
action, grouped into Banner clutter, Recurring chores, Borderline, keep-list
last — `scripts/classify.py` prints exactly this format), then immediately
close the targets and report the result.

What makes running unattended safe is the classifier plus the write rules, not
a human check:

- Only two categories are ever closed: banner clutter and older duplicates of a
  recurring chore. Real tasks, single-occurrence chores, and permanent dividers
  are never touched.
- **Borderline items are flagged, never closed** — ambiguity is routed to Mark
  by hand, instead of a blanket confirm on every run.
- Every close is a transition to Done, reversible in the Jira UI. Nothing is
  deleted.
- Each target is re-read immediately before it is closed (step 5), so a stale
  plan can't mutate an issue that changed.

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
- `fields`: `["summary", "status", "created", "parent", "labels"]` — `labels`
  is not used by the classifier; it is what lets a cleanup-only run render the
  day plan block every answer ends with, without a second query

The sprint can hold 200+ issues. **Loop on `nextPageToken`:** re-call with the
same `jql` and the returned `nextPageToken` until no token comes back. Do not set
`computeIssueCount` on these calls. Accumulate every page — a partial fetch
produces a wrong plan.

For each issue collect: `key`, `summary`, `status.statusCategory` (the `key`:
`new` / `indeterminate` / `done`), `created`, and `parent` (the parent issue
key from `fields.parent.key`, or null when there is no parent). Keep `labels`
in hand for the day plan block; the classifier ignores it. Write them as
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

### 3. Print the plan, then keep going

Show the classifier's plan output verbatim (or lightly reformatted — keep every
key, summary, and action, and keep the keep-list last). Call out the Borderline
section and any "may be the same chore" heads-up explicitly; do not resolve them
yourself and do not close them. Then go straight to step 4 — **do not stop for
approval.**

End that message, like every other, with the full day plan block — the cleanup
plan (what gets closed) and the day plan (what Mark works on) are different
things and both belong here.

### 4. Verify the Done transition (before the first mutation)

Call `getTransitionsForJiraIssue` on the **first** target key. Find the
transition whose destination is a Done status (statusCategory `done`, usually
named "Done"). Confirm its id is `31`; if the project has changed it, use the id
you found. If no Done transition is available on that issue, **stop and report**
— do not guess.

### 5. Transition the targets to Done

The plan can be stale: time passes between the step-1 fetch and this mutation
(a full sprint fetch paginates, and in planning mode an entire triage interview
can sit in between), and in that window Jira automation regenerates/closes rows
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
Borderline for Mark to handle).

Because nothing was confirmed up front, the report is where Mark gets his
chance to object — make the reversible decisions visible:

- Name every chore group where day-name variants were collapsed into one
  (e.g. a Wednesday row closed against a Saturday row), plus any "may be the
  same chore" heads-up. One line: if a variant should stay separate, he
  reopens it in the Jira UI and the classifier's grouping needs a fix.
- Anything skipped in step 5 because the fresh read contradicted the plan.

Then note the two things this does **not** fix:

1. **Already-Done items still sit in the sprint.** Closing issues doesn't remove
   them — Done items only leave when the sprint itself is closed. (Report the
   count from a one-shot `project = MCP AND sprint in openSprints() AND
   statusCategory = Done` query with `computeIssueCount: true` if useful.)
2. **The clutter comes back.** Jira automation regenerates banner rows and
   recurring chores on its next scheduled run; this cleanup is a sweep, not a
   fix at the source.

### Hard rules (learned the hard way)

- **End every answer with the full day plan**, cleanup-only runs included.
- Transition to Done, **never delete**.
- **Never ask for approval.** Print the plan, then close — one uninterrupted
  pass.
- **Surface ambiguity, never guess.** Borderline items are flagged, not closed.
  With no human gate in the loop, this rule is the only thing standing between
  an ambiguous row and a wrong close — widen Borderline before widening CLOSE.
- **Verify state before writing.** The plan is built before the mutations, and
  the gap can be long; re-read each target with `getJiraIssue` immediately before
  closing it and skip anything whose current state no longer matches the plan
  (already Done, summary changed). Never mutate against the stale snapshot.
- Never touch the backlog, real tasks, or the permanent dividers (children of
  `MCP-2213`).
- A partial fetch is a wrong plan — paginate to the last page before classifying.

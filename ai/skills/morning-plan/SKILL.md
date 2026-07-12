---
name: morning-plan
description: >
  Run Mark's interactive morning planning ritual against his personal Jira board
  (project MCP). Reads the current sprint, interviews him item-by-item with
  tappable options to sort tasks into effort buckets (stored as Jira labels),
  closes anything he reports done, and ends with a short ordered plan for the
  day. Use this skill whenever Mark says "morning plan", "plan my day", "run my
  daily planning", "triage my sprint/jira", "what should I do today", or
  otherwise wants to review, sort, or prioritize his personal Jira tasks — even
  if he doesn't say the word "plan".
---

# Morning Plan

An interactive daily-planning ritual over Mark's personal Jira. Claude is the
frontend; Jira is a dumb backing store. Bucket membership lives in **labels**
(the connector cannot re-rank issues, so rank order and divider tickets are
ignored). Requires the **Atlassian Rovo connector** enabled in the chat — if
its tools are unavailable, say so and stop.

## Constants

- cloudId: `f438107c-ea02-4718-a002-5ce3646a61dd`
- Project key: `MCP`
- Scope: **current sprint only** — every JQL includes `sprint in openSprints()`.
  Never read or write the backlog.
- Bucket labels (exact strings): `daily-target`, `prioritize`, `aspirational`,
  `not-daily-goals`
- Workflow transitions (global, verified): `11` = To Do, `31` = Done
- Separator-looking tickets (summaries with `===` or similar) come in two kinds
  — differentiate by parent epic, not by summary pattern:
  - **Legacy visual separators**: children of epic `MCP-2213` ("separators").
    Permanent. Exclude from triage; never label, close, or modify them.
  - **Automation banner rows**: separator-style summaries NOT parented to
    `MCP-2213` (created by Jira Automation). Also excluded from bucket triage,
    but they are disposable clutter: list them in the final brief and close
    them only if Mark says to — bulk cleanup belongs to his "clean up my jira
    sprint" flow, not this one.

## Workflow

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
was never closed), do not triage them here. Tell Mark what was found, then
invoke the **jira-sprint-cleanup** skill — read its SKILL.md and follow its
workflow (it plans first and waits for his explicit "go"). Resume the morning
plan with whatever survives cleanup.

### 2. Interview

Triage **every** open (not-done), non-separator item, whether or not it already
carries a bucket label — nothing is carried over untouched; yesterday's labeled
items get re-triaged fresh each run. Rules:

- Batches of **at most 3 items** per round, using tappable single-select
  options. Tap options cap at 4, so each question offers: **Daily target /
  Aspirational / Not daily goals / Mark as done**. `prioritize` stays a valid
  bucket via typed reply (it saw zero use in the first session — promote it
  back into the tap set if Mark starts using it).
- **"Mark as done" is an action, not a label**: on selection, immediately
  transition the issue to Done (`transitionJiraIssue`, id `31`) and write no
  bucket label.
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

For each triaged open issue, set its bucket via `editJiraIssue` with
`fields: {"labels": [...]}`.

**Labels are owned by this system** — Mark does not use Jira labels for
anything else. Set `labels` to exactly the one bucket label (the write replaces
the whole array, which is the desired behavior). Rare exception: if an
unexpected non-bucket label ever appears on an issue, keep it in the array and
mention it in the brief. If an edit fails, report the specific issue key and
error, and continue with the rest — no silent failures.

### 4. Final brief

End with the day's plan, formatted for a phone screen:

- **Daily target** — ordered quick-wins-first (lowest effort at top).
- **Aspirational**, then **Not daily goals** — one line each.
- Anything closed or skipped during the session.
- If `daily-target` exceeds ~5 items, say so once, plainly: "the less
  ambitious, the more achievable" — and name the best demotion candidates.
  Don't nag beyond that.

## Guardrails

- Reads before writes; all label writes happen in step 3, transitions may
  happen mid-interview when Mark reports something done.
- Never touch issues outside the open sprint; never modify legacy separators
  (children of `MCP-2213`); close automation banner rows only on explicit
  request; never edit Automation rules yourself (Mark does that in the Jira
  UI).
- Fine-grained order *within* a bucket is session-only. If Mark wants an
  artifact of the day's exact ordering, offer to write it as a comment on the
  `week planning ritual` ticket (or the topmost daily-target item) — don't do
  this unprompted.
- Every not-done, non-separator item is re-triaged on every run: a stored
  bucket label neither suppresses the prompt nor pre-selects the answer (the
  suggestion is recomputed from the effort heuristic each time). Separators and
  automation banner rows remain excluded from triage per the rules above.
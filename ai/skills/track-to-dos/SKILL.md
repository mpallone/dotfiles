---
name: track-to-dos
description: Track open actions in the current conversation and print remaining to-dos at the end of every response. Use for $track-to-dos, /track-to-dos, or requests to keep a running checklist in replies; not for a one-time task list or querying an external TODO system.
---

# Track to-dos

When invoked, start from the open actions already established in this conversation. Keep tracking through later turns and topic changes until the user asks to stop. A completed checklist does not turn tracking off.

## Maintain the list

- Track the user's requested actions and necessary next steps. Do not turn suggestions, hypothetical work, or ordinary questions into commitments.
- Update the list before every user-facing reply. Add new actions, incorporate corrections, remove cancelled or superseded items, and preserve unfinished work when the topic changes.
- Mark work complete only when the conversation provides evidence, including the user's report. An attempt, draft, or offer is not completion of the underlying action.
- Keep blocked work open and state the dependency briefly. Identify the owner when useful, especially when an action belongs to the user rather than the AI.
- Order items by dependencies and the next useful action. Combine duplicate items and omit routine implementation details.
- Remove completed items by default. If the user asks to retain a milestone, keep it with `[x]`; use `[ ]` for open items.
- Keep the state in the conversation. If you produce a context summary, preserve that tracking is active, the current items, and their owners and blockers. Do not create files, reminders, Jira tickets, or other external records just to maintain this tracker.

Tracking is not authorization to execute an item. Preserve the user's scope and approval requirements, and do not take over actions assigned to them.

## End every reply with the list

Append `Remaining to-dos:` and a compact Markdown checklist as the last content in every user-facing response, including commentary progress updates, answers to unrelated questions, clarification requests, and final replies. Do not append the footer to tool inputs or generated deliverables such as code, commit messages, or pull-request descriptions.

For example, if a draft is ready but the user still needs to review it:

```markdown
Remaining to-dos:

- [ ] You review the draft.
- [ ] AI applies any requested revisions.
```

If nothing remains, end with `Remaining to-dos: None.` Do not invent tasks to fill the list. When the user asks to stop tracking, stop adding the footer immediately; resume only if they ask again.

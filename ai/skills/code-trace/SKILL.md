---
name: code-trace
description: >-
  Walk through how existing code, a service, workflow, or pipeline works by
  following execution across files and repositories. Use for requests to trace
  a code path or explain a system with clickable source links, short snippets,
  and a paced walkthrough. Focuses on implemented behavior; a walkthrough of
  changes in a pull request belongs to code-review-walkthrough.
---

# Code trace

Make the implementation easy to follow with the source open beside the chat.
Explain one coherent part of the execution path, then pause for the reader.
Keep the walkthrough read-only unless the user separately requests changes.

## Establish the path and evidence

- Resolve the entry point and the question being answered. Use available
  context rather than asking the user to repeat it. Start with a compact map
  of the flow and the next useful section to inspect.
- Verify the relevant source revision against its remote. Preserve local work;
  use an isolated checkout when refreshing the source would disturb it.
  Reuse verified revisions during the walkthrough unless freshness matters.
- Follow callers into the code that does the work, including shared workflows,
  libraries, scripts, generated output, and downstream consumers as needed.
  Inspect the versions selected by the caller. A workflow's version and the
  version of the scripts it downloads can differ.
- Distinguish implementation, checked-in configuration, deployed configuration,
  and observed execution. Before claiming a feature is active in production,
  verify the relevant deployment settings or records. State the limit when
  only source configuration is available.
- Read enough to support the current section and its handoff. Avoid turning a
  focused explanation into an exhaustive dependency audit. If a source is
  inaccessible, identify the gap and continue with the verified portion.

## Make each section clickable

Lead with what this part accomplishes. Then connect the relevant pieces in
execution order: what triggers it, which inputs it selects, what it changes or
returns, and who consumes the result. Explain the conditions that materially
change that path, including skips, failures, retries, and asynchronous work.

For each important code step:

1. Link the file and relevant function or line range immediately beside the
   explanation. Use a commit-pinned repository URL when available; follow the
   actual dependency revision rather than linking every repository's main.
2. Show a short excerpt containing the lines that explain the behavior. Keep
   real identifiers and semantics. Mark omissions, and label expanded commands
   or simplified pseudocode instead of presenting them as verbatim source.
3. Explain why those lines matter in plain language, then connect them to the
   next inspected file. Define unfamiliar terms where they first become useful.

Verify each linked path exists at the linked revision and the line anchors
cover the cited code. Construct links from inspected paths; do not reconstruct
long package paths from memory. For source without a repository URL, use an
absolute local Markdown link with a line number and identify local modifications.
Do not make a private source public to obtain a clickable link.

Include a concrete example in each explanatory section: an actual input and
output, a small hypothetical case clearly labeled as such, or a failure trace.
Show how it moves through the code. A compact diagram helps when branches,
multiple repositories, or asynchronous handoffs are otherwise hard to follow.

## Explain what the evidence proves

- Use executable conditions and actual configuration over job names, comments,
  and documentation. If they disagree, explain the consequence with a link.
- Explain the boundary of success. A successful enqueue, HTTP response, job,
  or publication does not by itself prove that a later consumer completed.
  Distinguish requested work, completed writes, and acknowledged delivery.
- Use a relevant existing run or test result when it materially strengthens
  the explanation. Do not trigger deployments or production work to obtain
  an example for a walkthrough.
- Surface material gaps encountered along the path without converting the
  walkthrough into a formal review or an unsolicited redesign. When the user
  asks for a design, clearly separate proposed behavior from existing code;
  label invented interfaces and pseudocode as proposals.

## Keep the reader in control

- Default to one coherent stage per response, which may span several tightly
  related files. Avoid both a whole-system monologue and a rigid one-file rule.
- Treat "next" or "continue" as advancing from the current checkpoint. Answer
  a detour, then preserve the place in the original flow. Do not restart the
  overview or re-fetch unchanged evidence on every turn.
- Treat "more detail" as a request for additional implementation and snippets
  in the current section. If the user asks for the entire explanation at once,
  honor that instead of enforcing pauses.
- End a section at a natural boundary and name what remains. No repeated menu
  or permission question is needed. When the requested path is covered, say so;
  do not keep inventing additional stages.
- Deliver any reminder the user requested at the agreed stopping point. Create
  a skill, handoff, document, or ticket only when separately requested.

## Example invocation

`$code-trace Walk me through how an order reaches the fulfillment worker.`

After verifying the implementation, start with the request-to-worker map. In
the first detailed section, link the request handler and queue publisher, show
the enqueue and response lines, and trace one example order. Explain exactly
what the response establishes, then pause before the worker. On "next," follow
the worker's consumption, persistence, and acknowledgement path using the same
source-link-and-snippet format.

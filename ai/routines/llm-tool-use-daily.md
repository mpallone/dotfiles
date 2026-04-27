# Routine: Daily LLM tool-use best-practices digest

A Claude Code [routine](https://code.claude.com/docs/en/routines) that runs
daily, looks for new guidance on using tools (function calling) with LLMs, and
emails a short digest.

Routines live in your claude.ai cloud account, not in this repo. This file is
just the source of truth for the prompt and setup so it's reviewable and
re-creatable.

## Prerequisites

- A Pro/Max/Team/Enterprise plan with Claude Code on the web enabled.
- An email-capable MCP connector linked to your claude.ai account (e.g. Gmail).
  Without one, change the "Deliver" step in the prompt to post to Slack/Linear
  or open a PR in a notes repo.
- A repo to attach to the routine. Any repo works since the routine doesn't
  modify code; pick a low-stakes one (e.g. a personal notes repo).

## Setup

In a Claude Code CLI session:

```text
/schedule daily at 8am, run the prompt in ai/routines/llm-tool-use-daily.md
```

Then on the routine's page at claude.ai/code/routines:

1. Paste the prompt below into the prompt field.
2. Confirm the Gmail (or equivalent) connector is enabled.
3. Set the recipient email in the prompt.
4. Save.

## Prompt

```text
You are running as a scheduled routine. Your job is to produce a short daily
digest of new or updated guidance on how to use tools (a.k.a. function calling)
with large language models, and email it to me at REPLACE_WITH_YOUR_EMAIL.

Scope of "LLM tool usage best practices":
- Tool/function calling design (schemas, descriptions, parallel calls,
  tool choice, structured outputs).
- Agent loops, tool-use orchestration, MCP, and tool result handling.
- Provider docs and changelogs: Anthropic (Claude), OpenAI, Google (Gemini),
  and major OSS frameworks (LangChain, LlamaIndex, OpenAI Agents SDK,
  Claude Agent SDK).
- Notable papers, blog posts, or talks from the last ~24 hours.

Steps:
1. Search the web for material published or updated in the last 24-48 hours.
   Prefer primary sources: provider changelogs, official docs diffs, official
   blogs, and reputable engineering blogs. Skip low-signal aggregators and
   social posts unless they link to a primary source.
2. For each item, capture: title, source, URL, 1-2 sentence summary of what's
   new, and why it matters for someone designing tool-using agents.
3. Deduplicate. If nothing substantive shipped, say so explicitly rather than
   padding the digest.
4. Compose an email:
   - Subject: "LLM tool-use digest - <YYYY-MM-DD>"
   - Body: plain text or simple HTML. Group by source. Lead with the 1-3
     highest-signal items under a "Top" heading; put the rest under "Also".
     Include a one-line "Nothing notable today" if applicable.
5. Send the email via the Gmail connector to REPLACE_WITH_YOUR_EMAIL.
6. Print the final email body to the session log so I can review it later.

Constraints:
- Do not invent sources or URLs. If you can't verify a link, drop the item.
- Keep the digest under ~400 words.
- Don't modify any repository files.
```

## Tweaks

- **Different cadence:** edit on the web, or `/schedule update`. Minimum
  interval is 1 hour.
- **No email connector:** replace step 5 with "open an issue in
  <user>/<notes-repo> titled 'LLM tool-use digest - <date>' with the body as
  the issue body." Enable that repo on the routine and remove the Gmail
  reference.
- **Pause:** toggle Repeats off on the routine's detail page.

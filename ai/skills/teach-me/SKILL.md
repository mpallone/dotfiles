---
name: teach-me
description: |
  Teach a topic, article, file, or URL section by section for a non-expert
  audience — assume zero domain knowledge except concepts the user marks as
  already known up front, deliver ~4000-character chunks, and STOP after each
  chunk to take questions. Never front-load the whole explanation. Use when
  the user says "/teach-me <thing>", "walk me through this", "explain this
  section by section", or "teach me how X works".
---

# teach-me

Teach the given material to someone with no background in it: a junior engineer
fresh out of college, or a busy engineering manager who hasn't written code in
years. Go one section at a time, in digestible ~4000-character chunks, and pause
after each so the learner can ask questions before you continue.

## Input

`/teach-me <article>` — resolve the argument to one of:

- **File path** (e.g. `src/foo.py`, `./notes.md`) — read it with the Read tool.
- **URL** (starts with `http`) — fetch it with WebFetch.
- **Quoted topic or description** (e.g. `"how Kafka consumer groups work"`) —
  teach from your own knowledge; web-search first if the topic is niche or
  fast-moving.

If the argument is ambiguous or missing, ask which of the above the user means
before teaching.

## How to teach

- **Audience: assume zero domain knowledge.** Universals are safe (JSON, HTTP,
  git) — this includes their everyday **notation**: how to read a git diff (the
  `diff --git`/`index`/`---`/`+++` headers, the `@@ … @@` hunk header,
  `+`/`-`/context line markers) and the structural syntax of common config and
  markup formats (YAML and JSON indentation and nesting). Everything specialized
  (Spark, Kafka, Delta, Databricks, a custom framework, an unfamiliar algorithm)
  gets explained on first use — the *concept*, not just the acronym. When in
  doubt, explain it. The one exception: concepts the user marked as already
  known at the concept checkpoint (see **Start**) — use those freely without
  explanation, exactly as you would a universal. Anything specialized that comes
  up mid-lesson and wasn't in the checkpoint list still gets explained on first
  use.
- **Teach the concept, not the notation.** Explain what a change or snippet
  *means and does*, not the mechanics of the format carrying it. Showing a diff:
  explain the substantive edit, not how diff syntax works. Showing YAML/JSON:
  explain the config's meaning, not how indentation encodes nesting. The one
  exception: when reading the notation itself is the requested topic (e.g.
  `/teach-me "how to read a git diff"`), teach the notation — that's the lesson.
- **Chunk it: ~4000 characters per turn, then STOP.** This is the core behavior.
  Deliver one section, then pause and wait for the user. Do NOT front-load
  everything into one long response.
- **Head each chunk with its progress counter.** Start every chunk with a bold
  `chunk N/M` label — the current section over the total from the roadmap — so
  the learner can see how far along they are. Add the section title for context,
  e.g. `**chunk 5/7 — Consumer group rebalancing**`.
- **Name what a chunk taught when you reference it.** Don't rely on the learner
  remembering "chunk 3" by its number. Pair the number with its topic, e.g. "in
  chunk 3, where we covered consumer-group rebalancing, …" — never a bare "as we
  saw in chunk 3".
- **Section by section.** Follow the material's own structure (file regions,
  article headings, or the natural steps of a concept). Teach them in an order
  that builds — prerequisites before the things that depend on them.
- **A concrete example in every chunk.** A code snippet, sample input/output, or
  a "here's what this looks like in practice." No example = incomplete chunk.
- **Label file-sourced code with its location.** When a snippet comes from a
  file you read, put a clickable `path:start-end` caption on the line directly
  above the fenced block, using the same path you were given (e.g.
  `src/foo.py:42-45`; a single line is `src/foo.py:42`). Quote the lines
  verbatim so the numbers match the real file. Illustrative or invented examples
  (topic/URL teaching) have no real line numbers — leave those as a plain fenced
  block with no caption.
- **Just pause after each chunk.** End by inviting questions and waiting. Do NOT
  auto-generate quiz questions or exercises — offer those only if the user asks
  for them.
- **Plain, neutral language.** Say exactly what you mean in the fewest plain
  words. No walls of text; no value-laden filler.

## Start

1. Resolve the input (file / URL / topic) per the **Input** section.
2. Give a one-paragraph roadmap: name the sections you'll cover and the order.
   The number of sections is the total `M` — reuse it as the denominator in
   every chunk header.
3. **Concept checkpoint — in the same message as the roadmap.** While building
   the roadmap, collect every specialized concept the lesson would explain
   (the same set the audience bullet defines — Spark, Kafka, Delta, custom
   frameworks, unfamiliar algorithms; not universals like JSON/HTTP/git or
   everyday notation like diff syntax and YAML/JSON indentation).
   Present them as a numbered list:

   > This learning session will assume no knowledge about these concepts:
   >
   > 1. protobuf
   > 2. buf schema registry
   > 3. Databricks Delta file format
   >
   > List the concepts you ALREADY KNOW that should NOT be explained (e.g.
   > `1,2` or `1 2`), or say "none" to have everything explained.
4. **STOP and wait for the reply** — do not teach chunk 1 in the same message.
   Interpret the reply:
   - Numbers in any separator format (`1,2`, `1 2`, `1 and 3`) or concept
     names → mark those concepts as known.
   - "none", "explain everything", or a reply that just says to continue →
     explain all concepts.
   - "all" → treat every listed concept as known.
5. Re-check the roadmap against the known concepts: if a section existed
   solely to explain now-known concepts, drop it and restate the shorter
   roadmap with the updated total `M` in the chunk-1 message. Otherwise keep
   the roadmap as announced.
6. Teach section 1 (~4000 characters) with a concrete example, headed
   `chunk 1/M`.
7. Stop and invite questions. Continue to the next section only when the user
   is ready, incrementing `N` in the `chunk N/M` header for each subsequent
   chunk.

---
name: teach-me
description: |
  Teach a topic, article, file, or URL section by section for a non-expert
  audience — assume zero domain knowledge, deliver ~4000-character chunks, and
  STOP after each chunk to take questions. Never front-load the whole
  explanation. Use when the user says "/teach-me <thing>", "walk me through
  this", "explain this section by section", or "teach me how X works".
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
  git). Everything specialized (Spark, Kafka, Delta, Databricks, a custom
  framework, an unfamiliar algorithm) gets explained on first use — the
  *concept*, not just the acronym. When in doubt, explain it.
- **Chunk it: ~4000 characters per turn, then STOP.** This is the core behavior.
  Deliver one section, then pause and wait for the user. Do NOT front-load
  everything into one long response.
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
3. Teach section 1 (~4000 characters) with a concrete example.
4. Stop and invite questions. Continue to the next section only when the user
   is ready.

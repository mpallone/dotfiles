---
name: teach-me
description: |
  Teach a topic, article, file, or URL section by section for a non-expert
  audience — assume zero domain knowledge except concepts the user marks as
  already known up front, deliver exactly one idea per chunk, end each chunk
  with an evidence trail the learner can check, and STOP after each chunk to
  take questions. Never front-load the whole explanation. Use when the user
  says "/teach-me [thing]", "walk me through this", "explain this section by
  section", or "teach me how X works".
---

# teach-me

Teach the given material to someone with no background in it: a junior engineer
fresh out of college, or a busy engineering manager who hasn't written code in
years. Teach exactly one idea at a time, and pause after each so the learner can
ask questions before you continue. Every chunk ends with an evidence trail so the
learner can verify the claims without taking your word for them.

There is no target length for a chunk. A chunk is as long as one idea takes and
no longer. The failure mode this skill exists to prevent is packing several ideas
into one turn — so when a chunk feels like it is covering ground, it is.

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
- **One idea per chunk, then STOP.** This is the core behavior. Deliver one
  section, then pause and wait for the user. Do NOT front-load everything into
  one long response. Before sending, state in ONE sentence what this chunk
  teaches. If that sentence needs an "and", names two mechanisms, or lists
  steps, it is more than one chunk — split it and send only the first piece.
- **The split test.** Ask: can this chunk be split into smaller pieces where the
  piece put in front of the learner still contains everything they need to
  understand it? If yes, split it. A split is only valid when the first piece
  stands on its own — if understanding it requires material from a later piece,
  the split was in the wrong place, not wrong to attempt.
- **Have a subagent apply the split test before every chunk.** Required, not
  optional — see **Chunk review** below. You are a poor judge of whether your own
  draft is too dense; a reader who has not been thinking about the material for
  the last ten minutes is a better one.
- **When unsure whether to split, split.** A chunk that felt too small costs one
  extra turn. One that was too big cost the learner the lesson.
- **Head each chunk with its progress counter.** Start every chunk with a bold
  `chunk N/M` label — the current section over the total from the roadmap — so
  the learner can see how far along they are. Add the section title for context,
  e.g. `**chunk 5/7 — Consumer group rebalancing**`.
- **Name what a chunk taught when you reference it.** Don't rely on the learner
  remembering "chunk 3" by its number. Pair the number with its topic, e.g. "in
  chunk 3, where we covered consumer-group rebalancing, …" — never a bare "as we
  saw in chunk 3".
- **Section by section, but atomize first.** Follow the material's own structure
  (file regions, article headings, or the natural steps of a concept) to find the
  content, then break each of those into single ideas. Headings are *author*-sized
  units: one heading routinely holds four or five distinct ideas, because the
  author was organizing for a reader who already knows the domain. Your learner
  does not. Expect `M` to be several times the source's heading count — a roadmap
  with one entry per document heading has not been atomized. Teach them in an
  order that builds: prerequisites before the things that depend on them.
- **A concrete example in every chunk.** A code snippet, sample input/output, or
  a "here's what this looks like in practice." No example = incomplete chunk.
- **Label file-sourced code with its location.** When a snippet comes from a
  file you read, put a clickable `path:start-end` caption on the line directly
  above the fenced block, using the same path you were given (e.g.
  `src/foo.py:42-45`; a single line is `src/foo.py:42`). Quote the lines
  verbatim so the numbers match the real file. Illustrative or invented examples
  (topic/URL teaching) have no real line numbers — leave those as a plain fenced
  block with no caption.
- **End every chunk with an evidence trail.** Cite where each non-obvious claim
  in the chunk can be checked. See **Evidence trail** below — this is required,
  not optional.
- **Just pause after each chunk.** End by inviting questions and waiting. Do NOT
  auto-generate quiz questions or exercises — offer those only if the user asks
  for them.
- **Plain, neutral language.** Say exactly what you mean in the fewest plain
  words. No walls of text; no value-laden filler.

## What "one idea" looks like

There is no character count in this skill, so this worked example is the
calibration. Read it before teaching.

### Too big — a plausible chunk 3

> **chunk 3/5 — Consumer groups**
>
> Kafka splits a topic into partitions, and a consumer group is a set of
> consumers that divides those partitions among itself so each message is
> processed once. Each consumer tracks how far it has read using an offset — a
> per-partition bookmark — which it commits back to an internal topic called
> `__consumer_offsets` rather than to ZooKeeper as older versions did. When a
> consumer joins or leaves, the group rebalances: partition assignments are
> recomputed and redistributed, and during that window no consumer in the group
> processes anything. If a consumer stops calling `poll()` for longer than
> `max.poll.interval.ms` (default 300000), the broker assumes it is dead and
> triggers a rebalance, which is the usual cause of the "consumer keeps getting
> kicked out" symptom.

Apply the one-sentence test: *"This chunk teaches what a consumer group is,
**and** what an offset is, **and** where offsets are stored, **and** what a
rebalance is, **and** how poll timeouts trigger one."* Five "and"s. Five chunks.

Note it does not read as outrageous — it is coherent and well-written. That is
exactly why this failure is easy to ship. Density, not sloppiness, is the
problem.

### Right — the same material, atomized

`M` goes from 5 to 9. The consumer-group heading alone becomes:

- **chunk 3/9 — What a partition is**
- **chunk 4/9 — What a consumer group is** (needs 3)
- **chunk 5/9 — What an offset is** (needs 3)
- **chunk 6/9 — Where offsets are stored** (needs 5)
- **chunk 7/9 — What a rebalance is** (needs 4)
- **chunk 8/9 — What triggers a rebalance** (needs 7)

### The self-containment check

Chunk 3 stands alone: partitions can be explained with nothing but the idea of a
topic, so the learner needs no later material to follow it.

Contrast a bad split point — leading with "Where offsets are stored." It is
short, but the learner does not yet know what an offset is, so the first piece
they see is not understandable on its own. That ordering is invalid: split
smaller, but never so that the visible piece depends on a piece not yet shown.

## Chunk review

Every chunk is reviewed by a subagent before the learner sees it. This is the
enforcement mechanism for one-idea chunks — the rules above state the standard,
this catches the drafts that miss it.

**When:** after drafting a chunk, before sending it. Every chunk, including
chunk 1.

**How:** spawn one subagent, passing the drafted chunk in full, prompted with the
split test. Ask it to assume zero domain knowledge:

> Below is a draft chunk from a lesson for someone with no background in this
> material. Can it be split into smaller pieces such that the piece shown FIRST
> still contains everything the learner needs to understand it on its own?
>
> If yes, return the split, with the first piece in full.
>
> If no, say so and name the specific dependency that blocks it — the thing the
> learner would have to already know for a smaller first piece to make sense.
> "No" is a legitimate and expected answer for a chunk that already teaches one
> idea; do not split a chunk merely because splitting is possible in principle.
>
> <draft chunk here>

**Then:**

- **Valid split returned** → send only the first piece. Hold the remainder as the
  next chunk(s) and update `M` to the new total.
- **"No" returned** → send the chunk as drafted.
- **Subagent unavailable or errored** → apply the split test yourself and send.
  Never block the lesson on the reviewer; degraded enforcement beats a stalled
  lesson.

**Do not tell the learner about the review.** It is internal machinery. The
chunk arrives; the plumbing stays out of sight.

## Evidence trail

Close every chunk with an **Evidence** block listing where each non-obvious
claim can be independently checked. Two reasons this is mandatory:

1. **The learner can verify.** They confirm what you taught without trusting
   you, and they get the primary sources for going deeper.
2. **It forces you to find the truth.** Committing to a citation means going and
   reading the source rather than producing a plausible-sounding answer.
   Hallucination survives prose; it does not survive a line number.

### Format

A short bulleted list under a bold `**Evidence**` heading. Each entry: the claim
(abbreviated), then the source.

There is no limit on the number of entries — cite every non-obvious claim the
chunk makes. Never drop a citation to keep the block short, and never let the
block's length be a reason to shorten the teaching. With one idea per chunk the
count stays small on its own, and **Skip the obvious** below keeps out the
filler.

> **Evidence**
>
> - Consumer offsets are committed to an internal topic, not ZooKeeper —
>   [Kafka docs, "Offset Tracking"](https://kafka.apache.org/documentation/#impl_offsettracking)
> - Default `max.poll.interval.ms` is 300000 — `verified: kafka-clients 3.7.0
>   ConsumerConfig.java:412`
> - Our consumers override it to 600000 — `services/ingest/consumer.yaml:23`
> - Rebalance is "stop-the-world" for the group — *inference from the protocol
>   description above; not stated in these words by the docs*

### What counts as a source

Ordered by strength — prefer the strongest available:

- **Code you read this session** — `path:start-end`, same clickable form as the
  snippet captions. Strongest: it is the running system.
- **Commands the learner can re-run** — give the exact command, e.g.
  `git log --oneline -5 -- src/foo.py` or `kafka-configs.sh --describe …`. Say
  what output to expect.
- **Primary docs / specs / source repos** — link directly to the section, not
  the doc root. Vendor docs describe intended behavior, which can differ from
  deployed behavior; when both exist, cite the code too.
- **Your own reasoning** — allowed, but label it: *inference*, *analogy*, or
  *simplification*. Never dress inference as sourced fact.

### Rules

- **Verify before citing.** Do not cite a file, line range, URL, or config value
  you have not actually read this session. If you believe a source exists but
  have not opened it, either open it or say so: "likely documented in the Kafka
  protocol guide — not verified."
- **Mark what you could not verify.** An honest "unverified" entry is worth more
  than a confident wrong one. Include it in the block rather than dropping the
  claim silently.
- **Distinguish exists-in-code from active-in-prod.** A code path can be behind
  a disabled flag. Cite the config that proves it is on, or state that you did
  not confirm the prod setting.
- **Line numbers must match the real file.** Same requirement as snippet
  captions — quote verbatim from what you read.
- **Skip the obvious.** No citations for universals (what JSON is) or for claims
  already carried by a labeled snippet in the chunk body.
- **Topic-mode teaching still cites.** When teaching from your own knowledge
  with no file to read, cite docs, specs, or standards — and label the parts
  that are your synthesis. If a topic is niche or fast-moving, web-search and
  cite what you find rather than relying on memory.

## Start

1. Resolve the input (file / URL / topic) per the **Input** section.
2. Draft a roadmap: name the sections you'll cover and the order. Atomize it per
   the **Section by section** rule — single ideas, not the source's headings.
3. **Have a subagent atomize the roadmap further — before showing it to anyone.**
   Over-packing starts here: a section that holds three ideas produces a chunk
   that holds three ideas. One subagent call per lesson, prompted:

   > Below is a lesson outline for someone with no background in this material.
   > For each section, list the distinct ideas a learner must absorb. Then return
   > a revised outline where every entry is exactly one idea that can be taught
   > on its own, in an order where nothing depends on a later entry.
   >
   > <draft roadmap here>

   Adopt its outline; `M` is its entry count. If the subagent is unavailable or
   errors, apply the split test to the outline yourself and continue — never
   block the lesson on it.
4. Present the roadmap in one paragraph. `M` is the denominator in every chunk
   header from here on.
5. **Concept checkpoint — in the same message as the roadmap.** While building
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
6. **STOP and wait for the reply** — do not teach chunk 1 in the same message.
   Interpret the reply:
   - Numbers in any separator format (`1,2`, `1 2`, `1 and 3`) or concept
     names → mark those concepts as known.
   - "none", "explain everything", or a reply that just says to continue →
     explain all concepts.
   - "all" → treat every listed concept as known.
7. Re-check the roadmap against the known concepts: if a section existed
   solely to explain now-known concepts, drop it and restate the shorter
   roadmap with the updated total `M` in the chunk-1 message. Otherwise keep
   the roadmap as announced.
8. Draft section 1 with a concrete example, headed `chunk 1/M`, and close it with
   the **Evidence** block. Run it through **Chunk review** before sending; if the
   reviewer splits it, send only the first piece and update `M`.
9. Stop and invite questions. Continue to the next section only when the user
   is ready, incrementing `N` in the `chunk N/M` header for each subsequent
   chunk. Every chunk goes through **Chunk review** before it is sent, and every
   chunk gets its own Evidence block.

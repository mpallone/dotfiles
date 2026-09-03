---
name: teach-me
description: |
  Teach a topic, article, file, or URL for a non-expert audience — assume zero
  domain knowledge except concepts the user marks as already known up front,
  split the material into ~4000-character chunks, write every chunk to its own
  markdown file under /tmp, concatenate them into one whole-lesson file, and
  hand back a clickable list of all of them at once. Each chunk ends with an
  evidence trail the learner can check. When the
  learner's questions change what the lesson should say, rewrite or insert
  chunks automatically and re-link the affected files. Use when the user says
  "/teach-me [thing]", "walk me through this", "explain this section by
  section", or "teach me how X works".
---

# teach-me

Teach the given material to someone with no background in it: a junior engineer
fresh out of college, or a busy engineering manager who hasn't written code in
years. Break it into digestible ~4000-character chunks, write each chunk to its
own markdown file, concatenate the chunks into a single whole-lesson file, and
hand the learner a clickable list of every file at once.
Every chunk ends with an evidence trail so the learner can verify the claims
without taking your word for them. The learner paces themselves by reading; you
wait for their questions. See **Delivering the lesson**.

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
- **Chunk it: ~4000 characters per chunk.** One section per chunk file. The
  limit keeps each file readable in a sitting; it is not a budget to fill —
  a section that needs 2500 characters gets 2500.
- **Write every chunk before handing over.** The whole set goes to disk in one
  turn, then you print the list and stop. Do NOT deliver chunk 1 and wait, then
  chunk 2 — the learner controls pacing by choosing what to open next.
- **Head each chunk with its progress counter.** The chunk file opens with a
  `# chunk N/M — Section title` heading — the current section over the total
  from the roadmap — so the learner can see how far along they are, e.g.
  `# chunk 5/7 — Consumer group rebalancing`.
- **Name what a chunk taught when you reference it.** Don't rely on the learner
  remembering "chunk 3" by its number. Pair the number with its topic, e.g. "in
  chunk 3, where we covered consumer-group rebalancing, …" — never a bare "as we
  saw in chunk 3".
- **Section by section.** Follow the material's own structure (file regions,
  article headings, or the natural steps of a concept). Order them so they
  build — prerequisites before the things that depend on them. A learner reading
  chunk 1 through chunk M straight through should never hit a forward
  reference.
- **A concrete example in every chunk.** A code snippet, sample input/output, or
  a "here's what this looks like in practice." No example = incomplete chunk.
- **Label file-sourced code with its location.** When a snippet comes from a
  file you read, put a `path:start-end` caption on the line directly
  above the fenced block, using the same path you were given (e.g.
  `src/foo.py:42-45`; a single line is `src/foo.py:42`). Quote the lines
  verbatim so the numbers match the real file. Illustrative or invented examples
  (topic/URL teaching) have no real line numbers — leave those as a plain fenced
  block with no caption.
- **End every chunk with an evidence trail.** Cite where each non-obvious claim
  in the chunk can be checked. See **Evidence trail** below — this is required,
  not optional.
- **Hand over, then wait.** After printing the list, invite questions and stop.
  Do NOT auto-generate quiz questions or exercises — offer those only if the
  user asks for them.
- **Plain, neutral language.** Say exactly what you mean in the fewest plain
  words. No walls of text; no value-laden filler.

## Delivering the lesson

Chunk text goes to files on disk, not into the terminal. Streaming thousands of
characters into the chat scrolls the terminal out from under the learner while
they are still reading. The files are the lesson; the terminal is an index into
them.

**Once per lesson**, before writing any chunk, create the lesson directory:

```
mkdir -p /tmp/teach-me/<topic-slug>-<YYYYMMDD-HHMM>
```

`<topic-slug>` is a short kebab-case slug of the material —
`kafka-consumer-groups`, `ingest-consumer-py`. Get the timestamp from `date`
rather than guessing it.

**Then, in one turn:**

1. **Write every chunk file** with the Write tool, to
   `/tmp/teach-me/<lesson-dir>/chunk-NN-<section-slug>.md`, with `NN`
   zero-padded (`chunk-03-rebalancing.md`). Use the Write tool, not a shell
   heredoc — heredocs mangle backticks, quotes, and `$` in code snippets.
2. **Build the whole-lesson file** — see **The whole-lesson file** below. One
   shell command, run after every chunk exists.
3. **Print the index and wait — do not open the files.** Never run `open`, an
   editor, or any other launcher on a chunk or on the whole-lesson file; the
   learner opens them themselves. Print one line per chunk: the number, the
   section title, and the absolute path (paths render as clickable links in the
   terminal), then the whole-lesson path on its own line. No summary, no
   preview of the content:

   > 7 chunks, in reading order:
   >
   > 1. **What a consumer group is** — /tmp/teach-me/kafka-20260813-1421/chunk-01-what-it-is.md
   > 2. **Partition assignment** — /tmp/teach-me/kafka-20260813-1421/chunk-02-assignment.md
   > 3. **Consumer group rebalancing** — /tmp/teach-me/kafka-20260813-1421/chunk-03-rebalancing.md
   > …
   >
   > Whole lesson in one file: /tmp/teach-me/kafka-20260813-1421/full-lesson.md
   >
   > Read them in order. Ask me anything as you go.

   Then stop and wait.

**Each file is self-contained.** It carries everything the chunk would have said
in the terminal: the `# chunk N/M — Section title` heading, the explanation, the
concrete example, and the **Evidence** block. A learner who reads only the files
misses nothing. Keep `path:start-end` captions in their usual form even though
they render as plain text rather than clickable links — they stay copy-pasteable.

**What still belongs in the terminal:** the roadmap and concept checkpoint (both
short, and the checkpoint needs a reply), the index above, revision notices, and
answers to follow-up questions. If an answer runs long enough to scroll —
roughly 1500 characters or more — write it the same way, as
`qa-NN-<question-slug>.md`, and reply with the path for the learner to open.

## The whole-lesson file

Every lesson also gets `full-lesson.md` in the lesson directory: the chunk files
concatenated in reading order, so the learner can read, search, or share the
whole lesson as one document instead of opening M files. It is for the learner
who wants the long read; the numbered chunks remain the paced path through the
material.

**It is a literal concatenation — nothing added, nothing summarized.** No new
intro, no table of contents, no editorial connective tissue between sections.
Each chunk already opens with its `# chunk N/M — Section title` heading and
closes with its **Evidence** block, so the joined file reads as a sequenced
document on its own.

**Build it with a shell command, not the Write tool.** Re-writing the prose by
hand costs a full second pass and lets the copy drift from the chunks. `cat`
cannot drift:

```bash
cd /tmp/teach-me/<lesson-dir> && for f in chunk-*.md; do cat "$f"; printf '\n\n'; done > full-lesson.md
```

The `chunk-*.md` glob sorts correctly because the numbers are zero-padded, and
it excludes `qa-NN-*.md` answer files and `full-lesson.md` itself. The blank
line between files keeps the last line of one chunk from running into the next
chunk's heading.

**It is derived, never edited.** To change what it says, edit the chunk file and
re-run the command. Never patch `full-lesson.md` directly — the next rebuild
overwrites it, and until then the chunk and the whole-lesson copy disagree.

**Rebuild it after every file change.** Any revised chunk, inserted chunk,
renumbering, or deletion makes the existing `full-lesson.md` stale. Re-run the
command as part of the same turn — see **Revising after questions**.

## Revising after questions

The lesson is written before the learner reads it, so their questions will
sometimes prove part of it wrong, thin, or missing. **Fix the files, don't just
answer in chat.** Do this on your own initiative — no need to ask permission
first.

Three cases:

- **The answer fits in chat and changes nothing.** A clarifying question the
  chunk already covers, or a tangent outside the lesson's scope. Answer it and
  leave the files alone. This is the common case — do not rewrite a chunk for
  every question.
- **A chunk is wrong, unclear, or incomplete.** Rewrite that file in place, at
  the same path, so links the learner already has keep working. Add a revision
  banner as the first line under the heading, saying what changed and why:

  ```
  > **Revised** after your question about whether rebalancing blocks producers —
  > the original said "the group stops" without scoping it to consumers.
  ```

- **The material needs a section that doesn't exist.** Write a new chunk file at
  the position where it belongs in the build order, and renumber. Renumbering is
  not optional: every chunk's `N/M` heading and filename must stay consistent
  with its real position, so inserting a chunk at position 4 of 7 means
  rewriting chunks 4–7 into `chunk-05-…` through `chunk-08-…` with updated
  headings, and deleting the old files (`rm` the stale paths so the directory
  has no duplicates). If the new material has no prerequisites in the lesson,
  append it at the end instead — cheaper and no renumbering.

**After any file change, rebuild `full-lesson.md`** with the command in **The
whole-lesson file**, in the same turn as the change. A revised chunk, an
inserted chunk, or a renumbering leaves the old concatenation stale, and a
learner reading the stale copy sees the wrong version with no sign that it is
out of date.

**Then reprint the full index** in the same format as the
initial handover, with changed and new entries marked:

> Updated — 8 chunks now:
>
> 1. **What a consumer group is** — /tmp/teach-me/kafka-20260813-1421/chunk-01-what-it-is.md
> 2. **Partition assignment** — /tmp/teach-me/kafka-20260813-1421/chunk-02-assignment.md
> 3. **Consumer group rebalancing** — /tmp/teach-me/kafka-20260813-1421/chunk-03-rebalancing.md *(revised)*
> 4. **What rebalancing blocks** — /tmp/teach-me/kafka-20260813-1421/chunk-04-what-blocks.md *(new)*
> …
>
> Whole lesson in one file: /tmp/teach-me/kafka-20260813-1421/full-lesson.md *(rebuilt)*

Reprint the whole list, not only the changed lines — the learner's earlier index
is now stale, and a partial list leaves them guessing which paths still hold.
Say in one sentence what changed before the list.

**A revised chunk keeps its Evidence block current.** If the revision rests on a
source you read to answer the question, add it. If the revision corrects a claim
you had cited, remove or fix the citation that supported the wrong version.

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
(abbreviated), then the source. Keep it tight — 2–6 entries per chunk, not one
per sentence.

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
2. Give a one-paragraph roadmap: name the sections you'll cover and the order.
   The number of sections is the total `M` — reuse it as the denominator in
   every chunk header. Do not create the lesson directory or write any files
   yet; the checkpoint reply can change the section list.
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
4. **STOP and wait for the reply** — do not write any chunk files in the same
   message. Interpret the reply:
   - Numbers in any separator format (`1,2`, `1 2`, `1 and 3`) or concept
     names → mark those concepts as known.
   - "none", "explain everything", or a reply that just says to continue →
     explain all concepts.
   - "all" → treat every listed concept as known.
5. Re-check the roadmap against the known concepts: if a section existed
   solely to explain now-known concepts, drop it and use the shorter list.
   Whatever survives sets the final `M`.
6. Create the lesson directory (`mkdir -p /tmp/teach-me/<topic-slug>-<stamp>`,
   see **Delivering the lesson**), then write all `M` chunk files — each
   ~4000 characters, with a concrete example, headed `chunk N/M`, and closed
   with its own **Evidence** block.
7. Concatenate the chunks into `full-lesson.md` per **The whole-lesson file**.
8. Print the index of all `M` files plus the `full-lesson.md` path per
   **Delivering the lesson**, say the roadmap changed if it did, invite
   questions, and stop.
9. Answer questions as they come. When a question means a chunk is wrong or a
   section is missing, fix the files, rebuild `full-lesson.md`, and reprint the
   index per **Revising after questions**.

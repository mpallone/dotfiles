---
name: mmm-deploy
description: |
  Deploy the canonical AI-tool config (context, skills, subagents) to every
  tool via `mmm deploy`, reading the config path from the MMM_CONFIG environment
  variable. Use when the user says "mmm deploy", "deploy my config/skills/
  context", "sync my AI tools", or asks to push dotfiles config out to Claude/
  Windsurf/Gemini/Codex. Stops and asks if MMM_CONFIG is unset.
---

# mmm-deploy

Run `mmm deploy` across all tools, taking the config path from `$MMM_CONFIG`.

`mmm` (marks-markdown-manager) distributes one canonical set of markdown config
to each AI tool's own directory. Context is written as merged copies; skills and
subagents are symlinked back to their sources. Repo:
`~/src/mpallone/marks-markdown-manager`.

## Precondition: MMM_CONFIG must be set

The config file is **not** auto-discovered; every `mmm` command needs
`--config <path>`. This skill takes that path from the `MMM_CONFIG` environment
variable.

**If `MMM_CONFIG` is unset or empty, stop.** Do not guess a path and do not
fall back to a hard-coded location. The script exits 3 and prints the message
below — relay it to the user and ask how to proceed:

> `MMM_CONFIG` is not set, so I don't know which mmm config to deploy. Set it
> (e.g. `export MMM_CONFIG=~/src/riot/not-used-by-data-foundations/mpallone/dotfiles/mmm.yaml`)
> and re-run, or tell me the config path to use for this run.

Only continue once you have a real path. Do not re-run the script blind hoping
the variable appears.

## How to run

Run the bundled script (one process = one approval). From the skill directory:

```bash
bash scripts/mmm_deploy.sh
```

### Preview first

Recommend a dry run before the real deploy when the user hasn't already reviewed
pending changes:

```bash
bash scripts/mmm_deploy.sh --dry-run
```

Any extra args pass straight through to `mmm deploy`, so you can also scope a
run, e.g. `bash scripts/mmm_deploy.sh --tools claude,windsurf` or
`bash scripts/mmm_deploy.sh --type skills`. With no `--tools`, it deploys to
**all** tools.

## Exit codes

- **3** — `MMM_CONFIG` unset/empty. Stop and ask the user (see above).
- **4** — `MMM_CONFIG` points at a missing file. Report the bad path.
- **5** — `mmm` not on `PATH`. Install: `uv tool install --editable
  ~/src/mpallone/marks-markdown-manager`, then ensure `~/.local/bin` is on
  `PATH`.
- **0** — success (or dry run completed).
- **anything else** — `mmm`'s own exit status, passed through. A non-zero code
  means a partial or failed deploy; report it, don't claim success.

## Why real runs pass `--yes`

`mmm deploy` prompts `[Y/n]` before overwriting a *changed* context file or
replacing a non-symlink skill/subagent destination. Run non-interactively (no
TTY), those prompts hit EOF and crash the deploy partway through. On a real run
the script adds `--yes` so the full deploy completes in one shot — matching
mmm's documented default (prompts default to yes). Dry runs never prompt, so the
script omits `--yes` there.

If the user wants to eyeball each overwrite themselves, they should run
`mmm deploy --config "$MMM_CONFIG"` directly (without `--yes`) in their own
terminal — via the `! <command>` prefix — instead of through this skill.

## After it runs

- Relay `mmm`'s per-tool output: what was written (context), what was linked
  (skills/subagents), and any `BROKEN` symlinks it flags.
- On non-zero exit, report the failing step verbatim. Never claim success.
- Reminder for the user: `mmm` reads working trees, not remotes. If they edited
  a source file, it should be committed and pushed in its source repo so the
  deployed copy isn't lost on the next pull.

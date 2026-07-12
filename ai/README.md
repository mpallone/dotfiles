# `ai/` — source of truth for my Claude context and skills

This directory is the **single source of truth** for my AI configuration. Everything
Claude should know or be able to do lives here and is distributed out to each surface
from here. The guiding intent:

> **Automate every surface that has an automatable path.** Where a surface offers no
> automation (the claude.ai app), reduce the manual step to a single drag-and-drop and
> keep even that input generated for you. The one remaining manual upload is a platform
> limitation, not a design choice.

## Layout

```
ai/
├── global-context/AGENTS.md     # global instructions (a.k.a. CLAUDE.md content)
├── skills/                      # one <name>/SKILL.md per skill
│   ├── teach-me/
│   ├── jira-sprint-cleanup/
│   ├── morning-plan/
│   ├── mmm-deploy/              # local-machine tool (needs the mmm CLI)
│   ├── update-repos/            # local-machine tool (operates on local git repos)
│   └── daily-ai-tools-digest.md # loose note, NOT a skill (no <name>/SKILL.md dir)
├── cloud-setup.sh               # Cloud Code setup script: copies AGENTS.md + skills into ~/.claude
└── scripts/package_skills.sh    # builds claude.ai-app-ready skill ZIPs
```

## How each surface gets its skills

| Surface | Mechanism | Manual step? |
| :-- | :-- | :-- |
| **Local Claude Code** (laptop) | `mmm deploy` (marks-markdown-manager) distributes context + skills to each tool's dir | none (run `mmm`) |
| **Cloud Claude Code** (claude.ai/code) | **either** the app-upload bridge (enabled app skills auto-load) **or** the `cloud-setup.sh` setup script (pulls skills **and** AGENTS.md from this repo) — see [Cloud Claude Code setup script](#cloud-claude-code-setup-script) | none |
| **claude.ai app** (regular chats) | manual ZIP upload under Settings; the ZIPs are auto-built for you (see below) | one upload per changed skill |

### Why the app is the odd one out

The claude.ai **app** has **no public API** for uploading custom skills — the only way
in is a manual ZIP upload in Settings. The Developer-Platform Skills API
(`POST /v1/skills`) is a *different* surface: skills uploaded there are consumed only
through the Messages API and are **not available in the app or in Claude Code**. So we
don't upload via that API — it would go where none of my tools read.

**The one useful bridge:** a skill uploaded to the claude.ai **app** *also* auto-loads
into **cloud Claude Code** sessions. So a single app upload covers both regular chats
and cloud Code.

## Automation: the app ZIPs

`ai/scripts/package_skills.sh` builds a validated ZIP for each **app-portable** skill
(`teach-me`, `jira-sprint-cleanup`) and drops them in `dist/`. The
`.github/workflows/package-skills.yml` Action runs it on every push that touches a skill
and publishes the ZIPs to a rolling **`skills-latest`** GitHub Release. To refresh the
app after changing a skill: grab the current ZIP from that release and re-upload it under
**claude.ai → Settings → Skills** (with "Code execution and file creation" enabled).

Validation mirrors the app's rules: `name` lowercase-hyphenated ≤64 chars with no
reserved words (`claude`/`anthropic`), `description` non-empty ≤1024 chars with no XML
tags. `mmm-deploy` and `update-repos` are **excluded** — they're local-machine tools that
can't run in the app/cloud sandbox (they'd load but fail if invoked).

## Cloud Claude Code setup script

`ai/cloud-setup.sh` is a **second, independent** way to get this repo's config into
cloud sessions. A cloud session clones only the *project* repo, so `~/.claude` is
absent; the script clones this dotfiles repo and copies:

- `ai/global-context/AGENTS.md` → `~/.claude/CLAUDE.md`
- everything under `ai/skills/` → `~/.claude/skills/`

Wire it up **once per environment**: paste this bootstrap into the environment's
**Setup script** field (claude.ai/code → environment settings):

```bash
#!/bin/bash
git clone --depth 1 https://github.com/mpallone/dotfiles.git /tmp/dotfiles || true
[ -f /tmp/dotfiles/ai/cloud-setup.sh ] && bash /tmp/dotfiles/ai/cloud-setup.sh || true
```

- **Prerequisite:** the environment's network policy must allow `github.com` (the
  **Trusted** policy). Under **None**, the clone fails (the script still exits 0, so the
  session starts, just without the sync). `git` is pre-installed.
- **Refresh caveat:** setup scripts run on the FIRST session, then the filesystem is
  snapshotted and the script is SKIPPED on later sessions — so `~/.claude` is frozen
  until the cache rebuilds (edit the setup script or allowed hosts, or ~7-day expiry).
  To force a refresh after pushing dotfiles changes, re-save the setup script in the UI.

### Redundancy — intentional, and it can drift

This path **overlaps** the claude.ai-app zip path: enabled app skills already auto-load
into cloud sessions, and this script *also* copies skills in. Both are on by choice.
Consequences accepted:

- **They can drift.** The app serves whatever zip you last uploaded; the script serves
  this repo's HEAD as of the last snapshot. The same skill can differ between the two.
- **A skill may show up from both sources** in a cloud session (app-provided **and** the
  `~/.claude/skills/` copy). Expected and tolerated.
- The script's edge over the zip path: it also brings **AGENTS.md** (global context, which
  the zip/bridge does not) and ships **all** skills — including `morning-plan` and the
  local-only `mmm-deploy` / `update-repos` — not just the app-portable subset.

## Known limitations / follow-ups

- **Global context (`global-context/AGENTS.md`)**: distributed by `mmm` locally, pulled
  into cloud Code by `cloud-setup.sh` (above), and pasted by hand into claude.ai custom
  instructions for app chats (no upload API for that surface).
- **`jira-sprint-cleanup`** needs the Atlassian connector enabled in whatever chat runs it.
- **`daily-ai-tools-digest.md`** is a loose note, not a skill; nothing packages or ships it.

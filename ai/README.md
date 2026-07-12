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
│   ├── mmm-deploy/              # local-machine tool (needs the mmm CLI)
│   ├── update-repos/            # local-machine tool (operates on local git repos)
│   └── daily-ai-tools-digest.md # loose note, NOT a skill (no <name>/SKILL.md dir)
├── scripts/package_skills.sh    # builds claude.ai-app-ready skill ZIPs
└── .claude-plugin/plugin.json   # makes ai/ a Claude Code plugin ("mpallone-skills")
```

The repo root also holds `.claude-plugin/marketplace.json`, which turns this repo into
a Claude Code plugin **marketplace** named `mpallone-dotfiles`.

## How each surface gets its skills

| Surface | Mechanism | Manual step? |
| :-- | :-- | :-- |
| **Local Claude Code** (laptop) | `mmm deploy` (marks-markdown-manager) distributes context + skills to each tool's dir; or install this marketplace | none (run `mmm`) |
| **Cloud Claude Code** (claude.ai/code) | declare this marketplace + plugin in a work repo's `.claude/settings.json` (auto-installs at session start), and/or the app-upload bridge below | none |
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

## Installing the marketplace (Claude Code)

```
# once, on your laptop:
/plugin marketplace add mpallone/dotfiles
/plugin install mpallone-skills@mpallone-dotfiles
```

For cloud Code, add to a work repo's `.claude/settings.json` so sessions auto-install it
(requires the Trusted network policy so github.com is reachable):

```json
{
  "extraKnownMarketplaces": {
    "mpallone-dotfiles": { "source": { "source": "github", "repo": "mpallone/dotfiles" } }
  },
  "enabledPlugins": { "mpallone-skills@mpallone-dotfiles": true }
}
```

## Known limitations / follow-ups

- **Global context (`global-context/AGENTS.md`)** is distributed by `mmm` locally and can
  be pasted into claude.ai custom instructions for app chats, but has **no automated path
  into cloud Code** now that the old setup-script approach is retired. Options if it starts
  to matter: a per-work-repo `CLAUDE.md`, or a minimal cloud setup script.
- **`jira-sprint-cleanup`** needs the Atlassian connector enabled in whatever chat runs it.
- **`daily-ai-tools-digest.md`** is a loose note, not a skill; nothing packages or ships it.

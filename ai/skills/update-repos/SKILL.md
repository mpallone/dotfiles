---
name: update-repos
description: |
  Update every git repository beneath the current directory: detect each repo's
  primary branch (main/master/develop), switch to it, and pull. Repos that can't
  be safely updated (uncommitted changes, no remote, merge conflicts, detached
  HEAD) are skipped and reported. Use when the user asks to "update all my repos",
  "pull latest everywhere", or "sync repos under this folder".
---

# update-repos

Update all git repos under a directory in one pass: switch each to its primary
branch and fast-forward pull. Unsafe repos are skipped and reported, never
blocking the run.

## How to run

Run the bundled script once (one process = one approval, no per-command Enter
prompts). From the skill directory:

```bash
python scripts/update_repos.py
```

Default root is the current working directory. Options:

- `--root DIR` — search a different base directory (e.g. `--root ~/src/riot`).
- `--dry-run` — report what *would* happen; performs no checkout or pull.

**Recommend a `--dry-run` first** when pointing it at an unfamiliar tree, then
re-run without the flag.

## Behavior

- **Discovery:** recursive; any directory containing `.git` is treated as a repo,
  and the walk does not descend into a repo's own subdirectories.
- **Primary branch:** prefers `origin/HEAD`; if unset, runs
  `git remote set-head origin --auto`; falls back to the first existing of
  `main` > `master` > `develop`.
- **Always lands on primary:** switches to the primary branch even from a clean
  feature branch, then `git pull --ff-only`.
- **Skips (with reason), never aborts:** uncommitted changes, no remote, no
  detectable primary branch, failed checkout, or a non-fast-forward/conflicting
  pull. The script exits 0 even when repos are skipped.
- **Non-interactive:** git runs with `GIT_TERMINAL_PROMPT=0` and ssh
  `BatchMode=yes`, so auth/host-key issues fail fast instead of hanging.

After it runs, relay the summary table and counts line to the user, and call out
any skipped repos that need manual attention (e.g. uncommitted changes).

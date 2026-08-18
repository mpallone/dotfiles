#!/usr/bin/env bash
# Copy the current Claude Code session's name (the one set by /rename) to the
# macOS clipboard, and print it.
#
# Claude Code writes live session state to ~/.claude/sessions/<pid>.json and
# exports CLAUDE_PID into the shell it spawns. That env var is the only reliable
# way to pick the right file when several sessions share a working directory, so
# this only works from inside a Claude Code session -- the Bash tool, a `!`
# prefixed prompt line, or a slash command. A detached terminal has no CLAUDE_PID.
#
# Exit codes: 0 copied, 1 no session name available.

set -euo pipefail

if [ -z "${CLAUDE_PID:-}" ]; then
  echo "CLAUDE_PID is unset. Run this from inside a Claude Code session." >&2
  exit 1
fi

state="$HOME/.claude/sessions/${CLAUDE_PID}.json"

if [ ! -f "$state" ]; then
  echo "No session state file at $state" >&2
  exit 1
fi

name=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("name") or "", end="")' "$state")

if [ -z "$name" ]; then
  echo "This session has no name yet. Set one with /rename." >&2
  exit 1
fi

# Capture pbcopy's status explicitly: inside `if ! cmd`, $? reads 0, which would
# make the script report a failure and still exit 0.
set +e
printf '%s' "$name" | pbcopy
rc=$?
set -e

if [ "$rc" -ne 0 ]; then
  echo "pbcopy failed (exit $rc); clipboard NOT updated. The session name is: $name" >&2
  echo "If Claude Code's sandbox is enabled, add this script's path to" >&2
  echo "sandbox.excludedCommands in ~/.claude/settings.json -- the sandbox blocks" >&2
  echo "the pasteboard service and pbcopy fails without printing anything." >&2
  exit "$rc"
fi

echo "Copied to clipboard: $name"

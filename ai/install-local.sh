#!/usr/bin/env bash
# Install this repo's Claude Code slash commands onto a local machine.
#
# `mmm` (marks-markdown-manager) distributes context, skills, and subagents -- but
# NOT commands. This script covers that gap. It symlinks every file in ai/commands/
# into ~/.claude/commands/, so edits in this repo are live immediately with no
# redeploy step, the same way mmm treats skills.
#
# Safe to re-run. A target that is already the correct symlink is left alone;
# anything else at a target path is reported and skipped, never overwritten.
#
# Usage: bash ai/install-local.sh

set -euo pipefail

ai_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
src_dir="$ai_dir/commands"
dest_dir="$HOME/.claude/commands"

if [ ! -d "$src_dir" ]; then
  echo "No commands directory at $src_dir" >&2
  exit 1
fi

mkdir -p "$dest_dir"

linked=0
skipped=0

for src in "$src_dir"/*; do
  [ -e "$src" ] || continue
  dest="$dest_dir/$(basename "$src")"

  if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
    echo "ok        $dest"
    continue
  fi

  if [ -e "$dest" ] || [ -L "$dest" ]; then
    echo "SKIPPED   $dest exists and is not a link to $src" >&2
    skipped=$((skipped + 1))
    continue
  fi

  ln -s "$src" "$dest"
  echo "linked    $dest -> $src"
  linked=$((linked + 1))
done

echo
echo "$linked linked, $skipped skipped."

if [ "$skipped" -gt 0 ]; then
  echo "Resolve the skipped paths by hand, then re-run." >&2
fi

cat <<'NOTE'

One manual step remains, because it lives in settings.json rather than here:
/copy-name shells out to pbcopy, and Claude Code's sandbox blocks the macOS
pasteboard service. Add the script to sandbox.excludedCommands in
~/.claude/settings.json:

  "sandbox": {
    "excludedCommands": ["~/.claude/commands/copy-session-name.sh"]
  }

That setting is backed up separately by the backup-claude-settings skill in the
Riot dotfiles repo. Without it, /copy-name prints the session name but does not
copy it.
NOTE

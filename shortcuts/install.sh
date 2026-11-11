#!/bin/bash
set -eu

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
launcher="$HOME/.local/bin/new-codex-session"

mkdir -p "$HOME/.local/bin"
if [ -e "$launcher" ] && [ ! -L "$launcher" ]; then
  printf 'Refusing to replace an existing file: %s\n' "$launcher" >&2
  exit 1
fi
ln -sfn "$script_dir/new-codex-session.sh" "$launcher"
printf 'Linked %s -> %s\n' "$launcher" "$script_dir/new-codex-session.sh"

# macOS requires a signed file before Shortcuts will offer to import it.
shortcut_dir="$(mktemp -d "${TMPDIR:-/tmp}/codex-shortcut.XXXXXX")"
shortcut_file="$shortcut_dir/New Codex Session.shortcut"
/usr/bin/shortcuts sign --mode anyone \
  --input "$script_dir/New Codex Session.shortcut" \
  --output "$shortcut_file"
/usr/bin/open "$shortcut_file"
printf 'Opened %s. Click Add Shortcut, then configure its keyboard shortcut.\n' "$shortcut_file"

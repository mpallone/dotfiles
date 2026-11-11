#!/bin/bash
#
# install.sh — install the herdr "new Codex tab" key for the current user.
#
#   herdr/codex-tab.sh  ->  ~/.local/bin/herdr-codex-tab   symlinked
#   herdr/config.toml   ->  ~/.config/herdr/config.toml    copied, or appended
#
# config.toml is copied rather than symlinked because herdr writes to that file
# itself. Verified on 2026-11-11 with herdr 0.9.5: dismissing the first-run
# screen added `onboarding = false`. A symlink would push machine-local state
# into this checkout.
#
# An existing config.toml is never replaced. The script appends only the
# marked `[[keys.command]]` block and saves a timestamped backup first. It
# does not edit an existing `[keys]` table, so a different prefix stays as is.
#
# Idempotent. Does not install herdr, Codex, or jq; see INSTALL_PROMPT.md.
#
# Usage:  bash herdr/install.sh
set -eu

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
launcher="$HOME/.local/bin/herdr-codex-tab"
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/herdr"
config="${HERDR_CONFIG_PATH:-$config_dir/config.toml}"
marker="herdr-codex-tab"

chmod +x "$script_dir/codex-tab.sh"
mkdir -p "$HOME/.local/bin" "$(dirname "$config")"
if [ -e "$launcher" ] && [ ! -L "$launcher" ]; then
  printf 'Refusing to replace an existing file: %s\n' "$launcher" >&2
  exit 1
fi
ln -sfn "$script_dir/codex-tab.sh" "$launcher"
printf '[ok]   linked %s -> %s\n' "$launcher" "$script_dir/codex-tab.sh"

if [ ! -e "$config" ]; then
  cp "$script_dir/config.toml" "$config"
  printf '[ok]   copied config to %s\n' "$config"
elif grep -q "$marker" "$config"; then
  printf '[skip] %s already has the Codex tab key\n' "$config"
else
  backup="$config.bak-$(date +%Y%m%d-%H%M%S)"
  cp "$config" "$backup"
  {
    printf '\n'
    sed -n '/^# BEGIN codex-tab keybinding/,/^# END codex-tab keybinding/p' "$script_dir/config.toml"
  } >>"$config"
  grep -q "$marker" "$config" || {
    printf 'Appending the key block to %s failed; restore %s\n' "$config" "$backup" >&2
    exit 1
  }
  printf '[ok]   appended the Codex tab key to %s (backup: %s)\n' "$config" "$backup"
  printf '[note] the existing [keys] table was left alone; this repo uses prefix = "ctrl+s"\n'
fi

for tool in herdr codex jq; do
  command -v "$tool" >/dev/null 2>&1 ||
    printf '[warn] %s is not on PATH; the key will not work until it is installed\n' "$tool" >&2
done

# Running servers and attached clients keep the old keys until they reload.
if command -v herdr >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  herdr session list --json 2>/dev/null |
    jq -r '.sessions[] | select(.running) | .name' |
    while IFS= read -r session; do
      if herdr --session "$session" server reload-config >/dev/null 2>&1; then
        printf '[ok]   reloaded config in running herdr session "%s"\n' "$session"
      else
        printf '[warn] could not reload herdr session "%s"; press prefix+shift+r in it\n' "$session" >&2
      fi
    done
fi

printf '\nPress the herdr prefix, then Shift+C, to open a new Codex tab.\n'
printf 'Check it without a keyboard: bash %s/test-codex-key.sh\n' "$script_dir"

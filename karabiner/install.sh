#!/usr/bin/env bash
#
# install.sh — restore the Karabiner-Elements setup into ~/.config/karabiner.
#
# Maps Keyboardio Model 100 shortcuts through Karabiner-Elements:
#   F18 -> open a new iTerm tab and run codex
#   F19 -> open a new plain iTerm tab
# See README.md in this directory for the manual steps (Chrysalis, driver
# approval, macOS permissions) that this script cannot do for you.
#
#   assets/complex_modifications/butterfly-claude.json  ->  symlinked
#   assets/complex_modifications/f19-terminal-tab.json  ->  symlinked
#   scripts/codex-tab.sh                                ->  symlinked
#   scripts/terminal-tab.sh                             ->  symlinked
#   karabiner.json                                      ->  COPIED (see below)
#
# Design notes:
#
#   * The asset JSON and the shell script are symlinked because Karabiner only
#     ever reads/executes them, so edits in this repo go live immediately.
#
#   * karabiner.json is COPIED, not symlinked. Karabiner rewrites that file
#     itself (atomic temp-file + rename), which replaces a symlink with a
#     regular file. Verified on 2026-09-07 with Karabiner 16.3.0: symlinking it
#     and running `karabiner_cli --select-profile` turned the symlink back into
#     a plain file, silently detaching it from this repo.
#
#   * Because it is a copy, this script refuses to overwrite an existing
#     karabiner.json unless you pass --force. On a machine that already has
#     other Karabiner rules, blindly copying would destroy them; merge the F18
#     and F19 rules in by hand instead.
#
#   * After changing Karabiner settings via the GUI, re-snapshot with:
#         cp ~/.config/karabiner/karabiner.json <this-repo>/karabiner/karabiner.json
#
# Idempotent. Prints [ok]/[warn]/[skip] per step so nothing fails silently.
#
# Usage:  bash karabiner/install.sh [--force]
#
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.config/karabiner"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

ok()   { echo "[ok]   $*"; }
warn() { echo "[warn] $*" >&2; }
skip() { echo "[skip] $*"; }

mkdir -p "$DEST/assets/complex_modifications" "$DEST/scripts"

link() {
  src="$1"; dst="$2"
  if [ ! -e "$src" ]; then warn "missing source: $src"; return 1; fi
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    skip "already linked: $dst"; return 0
  fi
  rm -f "$dst"
  ln -s "$src" "$dst" && ok "linked $dst -> $src"
}

link "$SCRIPT_DIR/assets/complex_modifications/butterfly-claude.json" \
     "$DEST/assets/complex_modifications/butterfly-claude.json"
link "$SCRIPT_DIR/assets/complex_modifications/f19-terminal-tab.json" \
     "$DEST/assets/complex_modifications/f19-terminal-tab.json"
link "$SCRIPT_DIR/scripts/codex-tab.sh" "$DEST/scripts/codex-tab.sh"
link "$SCRIPT_DIR/scripts/terminal-tab.sh" "$DEST/scripts/terminal-tab.sh"

chmod +x "$SCRIPT_DIR/scripts/codex-tab.sh" "$SCRIPT_DIR/scripts/terminal-tab.sh" 2>/dev/null && \
  ok "tab scripts are executable"

if [ -e "$DEST/karabiner.json" ] && [ "$FORCE" -eq 0 ]; then
  warn "$DEST/karabiner.json already exists; NOT overwriting."
  warn "Merge the F18 and F19 rules into"
  warn "profiles[0].complex_modifications.rules by hand, or re-run with --force"
  warn "to replace it wholesale (destroys any other rules on this machine)."
else
  cp "$SCRIPT_DIR/karabiner.json" "$DEST/karabiner.json" && ok "copied karabiner.json"
fi

echo
echo "Karabiner reloads config automatically on change."
echo "Manual steps this script cannot do -- see karabiner/README.md:"
echo "  1. brew install --cask karabiner-elements  (needs a real TTY for sudo)"
echo "  2. Approve the driver extension in System Settings"
echo "  3. Grant Input Monitoring + Accessibility"
echo "  4. Accept the Automation prompt on the first mapped-key press"
echo "  5. Chrysalis: butterfly = raw key code 109 (F18); Any = 110 (F19)"

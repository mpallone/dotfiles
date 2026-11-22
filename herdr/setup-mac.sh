#!/bin/bash
#
# setup-mac.sh — one command that sets up "a key opens a new Codex tab in
# herdr" on a Mac. It installs what is missing, binds both keys, and tests one.
#
#   1. Homebrew packages, only when missing: herdr, Codex, jq, tmux, iTerm2
#   2. herdr/install.sh          ctrl+s then Shift+C, inside herdr
#   3. herdr/test-codex-key.sh   presses that key under tmux and checks the tab
#   4. hotkeys/install.sh        butterfly key (F18), from any app. The same
#                                helper also reserves F3 (Mission Control) and
#                                F4 (Spotlight) systemwide.
#
# Steps only a person can do are listed at the end, and only the ones still
# open: installing Homebrew or Apple's Command Line Tools, signing in to Codex,
# dismissing herdr's first-run screen, mapping the butterfly key in Chrysalis,
# and approving the macOS prompt that lets Codex Hotkey control iTerm.
#
# Safe to rerun; present tools and installed keys are skipped. A failed step is
# reported and the remaining independent steps still run.
#
# Usage:  bash herdr/setup-mac.sh [--skip-butterfly]
#   --skip-butterfly  Install only the in-herdr key. Use it on a Mac without
#                     the Keyboardio keyboard, where a login agent is not
#                     allowed, or where F3 and F4 must keep their usual jobs.
# Exit:   0 when every attempted step succeeded, 1 otherwise.
#
# Example:
#   $ bash herdr/setup-mac.sh
#   ...
#   [ok]   PASS: C-s then C opened tab w1:t2 "Codex"; herdr detected codex in w1:p2
#   [ok]   butterfly helper is running: registered systemwide F18
set -u

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$script_dir/.." && pwd)"
PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH

skip_butterfly=0
case "${1:-}" in
  "") ;;
  --skip-butterfly) skip_butterfly=1 ;;
  *)
    printf 'Usage: bash herdr/setup-mac.sh [--skip-butterfly]\n' >&2
    exit 2
    ;;
esac

failures=0
need_brew=0
todo=""
ok() { printf '[ok]   %s\n' "$*"; }
skip() { printf '[skip] %s\n' "$*"; }
warn() { printf '[warn] %s\n' "$*" >&2; }
fail() {
  printf '[fail] %s\n' "$*" >&2
  failures=$((failures + 1))
}
add_todo() {
  todo="${todo}  - $*
"
}

# finish: print the open manual steps and exit with the overall result.
finish() {
  if [ "$need_brew" -eq 1 ]; then
    add_todo "Install Homebrew from https://brew.sh, then rerun this script. It installs what is missing."
  fi
  printf '\n'
  if [ -n "$todo" ]; then
    printf 'Left for you to do by hand:\n%s\n' "$todo"
  fi
  if [ "$failures" -gt 0 ]; then
    printf 'Finished with %s failed step(s); see the [fail] lines above.\n' "$failures" >&2
    exit 1
  fi
  printf 'Setup finished with no failed steps.\n'
  exit 0
}

# brew_install NAME CHECK_COMMAND BREW_ARGUMENTS...
# Installs NAME with Homebrew unless CHECK_COMMAND already succeeds.
# Returns 0 when NAME is usable afterwards, 1 otherwise.
# Example: brew_install tmux "command -v tmux" tmux
brew_install() {
  local name="$1" check="$2"
  shift 2
  if eval "$check" >/dev/null 2>&1; then
    skip "$name is already installed"
    return 0
  fi
  if ! command -v brew >/dev/null 2>&1; then
    fail "$name is missing and Homebrew is not installed, so it cannot be installed here."
    need_brew=1
    return 1
  fi
  printf '[..]   installing %s: brew install %s\n' "$name" "$*"
  if brew install "$@" && eval "$check" >/dev/null 2>&1; then
    ok "installed $name"
    return 0
  fi
  fail "brew install $* did not leave a working $name."
  return 1
}

[ "$(uname -s)" = "Darwin" ] || {
  printf '[fail] This script is for macOS; this machine reports %s. See herdr/INSTALL_PROMPT.md.\n' "$(uname -s)" >&2
  exit 1
}

printf '== Tools ==\n'
have_herdr=0
have_codex=0
brew_install herdr "command -v herdr" herdr && have_herdr=1
brew_install jq "command -v jq" jq
brew_install tmux "command -v tmux" tmux
# A `codex` alias or function defined in the login shell's startup files counts:
# the launchers type `codex` into a shell instead of executing a binary.
brew_install Codex "command -v codex || \"\$SHELL\" -lc 'type codex'" --cask codex && have_codex=1

printf '\n== Key inside herdr: prefix, then Shift+C ==\n'
config="${HERDR_CONFIG_PATH:-${XDG_CONFIG_HOME:-$HOME/.config}/herdr/config.toml}"
if [ "$have_herdr" -eq 1 ] && bash "$script_dir/install.sh"; then
  # The test types the chord through tmux, which needs the prefix in tmux
  # notation. Only a single ctrl+letter prefix is translated here.
  prefix_line="$(grep -E '^[[:space:]]*prefix[[:space:]]*=' "$config" 2>/dev/null | head -n 1)"
  prefix_key=""
  if [ -z "$prefix_line" ]; then
    prefix_key="C-b" # herdr's default
  else
    prefix_key="$(printf '%s\n' "$prefix_line" | sed -n 's/^[^=]*=[[:space:]]*"ctrl+\([a-z]\)"[[:space:]]*$/C-\1/p')"
  fi
  if [ -z "$prefix_key" ]; then
    warn "Could not translate this herdr prefix for the test: $prefix_line"
    add_todo "Run the key test by hand with your prefix in tmux notation: PREFIX_KEY=<key> bash herdr/test-codex-key.sh"
  elif ! command -v tmux >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
    warn "Skipped the key test because tmux or jq is missing."
  elif [ "$have_codex" -ne 1 ]; then
    warn "Skipped the key test because Codex is missing."
  elif result="$(PREFIX_KEY="$prefix_key" bash "$script_dir/test-codex-key.sh" 2>&1)"; then
    ok "$result"
  else
    fail "The in-herdr key test failed:"
    printf '%s\n' "$result" >&2
  fi
  if ! grep -Eq '^onboarding[[:space:]]*=[[:space:]]*false' "$config" 2>/dev/null; then
    add_todo "Start herdr in iTerm and dismiss its first-run screen and the settings screen after it. They swallow key chords until dismissed."
  fi
else
  fail "The in-herdr key was not installed."
fi

printf '\n== Butterfly key (F18) from any app ==\n'
if [ "$skip_butterfly" -eq 1 ]; then
  skip "butterfly key skipped on request"
elif [ ! -x /usr/bin/jq ]; then
  # shortcuts/new-codex-session.sh calls /usr/bin/jq by absolute path.
  fail "The butterfly launcher needs /usr/bin/jq, which macOS 15 and later include. This Mac runs $(sw_vers -productVersion 2>/dev/null || echo an unknown version)."
elif ! xcode-select -p >/dev/null 2>&1 || ! xcrun --find swiftc >/dev/null 2>&1; then
  xcode-select --install >/dev/null 2>&1 || true
  fail "Apple's Command Line Tools are missing; they compile the butterfly helper."
  add_todo "Finish the Command Line Tools installer that just opened (or run: xcode-select --install), then rerun this script."
elif [ "$have_herdr" -ne 1 ]; then
  fail "The butterfly key was not installed because herdr is missing."
else
  brew_install iTerm2 "[ -d /Applications/iTerm.app ] || [ -d \"\$HOME/Applications/iTerm.app\" ]" --cask iterm2
  # The butterfly launcher searches ~/.local/bin and /opt/homebrew/bin only.
  # Intel Homebrew installs to /usr/local/bin, so give it a link it can find.
  herdr_path="$(command -v herdr)"
  case "$herdr_path" in
    "$HOME/.local/bin/herdr" | /opt/homebrew/bin/herdr) ;;
    *)
      mkdir -p "$HOME/.local/bin"
      if [ ! -e "$HOME/.local/bin/herdr" ] && ln -s "$herdr_path" "$HOME/.local/bin/herdr"; then
        ok "linked ~/.local/bin/herdr -> $herdr_path so the butterfly launcher can find it"
      fi
      ;;
  esac

  log_file="$HOME/Library/Logs/CodexHotkey.log"
  lines_before=0
  [ -f "$log_file" ] && lines_before="$(wc -l <"$log_file" | tr -d ' ')"
  if bash "$repo_dir/hotkeys/install.sh"; then
    # The helper starts in the background; only lines newer than this run count.
    registered=0
    attempt=0
    while [ "$attempt" -lt 20 ]; do
      if tail -n "+$((lines_before + 1))" "$log_file" 2>/dev/null | grep -q 'registered systemwide F18'; then
        registered=1
        break
      fi
      attempt=$((attempt + 1))
      sleep 0.5
    done
    if [ "$registered" -eq 1 ]; then
      ok "butterfly helper is running: registered systemwide F18"
      add_todo "In Chrysalis, set the butterfly key on Layer 0 to raw key code 109 (F18), if it is not already."
      add_todo "Press the butterfly key once and allow \"Codex Hotkey\" to control iTerm when macOS asks."
      add_todo "The same helper maps F3 to Mission Control and F4 to Spotlight. F4 needs \"Codex Hotkey\" enabled under Privacy & Security > Accessibility; see hotkeys/README.md."
    else
      fail "The butterfly helper did not report 'registered systemwide F18' within 10 seconds. New lines in $log_file:"
      tail -n "+$((lines_before + 1))" "$log_file" >&2 2>/dev/null || true
    fi
  else
    fail "hotkeys/install.sh failed; its output is above."
  fi
fi

if [ "$have_codex" -eq 1 ] && command -v codex >/dev/null 2>&1 && ! codex login status >/dev/null 2>&1; then
  add_todo "Codex reports no sign-in. Run codex once and sign in. Ignore this on a machine that uses a custom model provider."
fi
finish

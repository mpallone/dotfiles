#!/bin/bash
#
# test-codex-key.sh — press the Codex tab key in a real herdr client and check
# that a Codex tab opens. Lets an agent prove the key without a keyboard.
#
# How: tmux holds a terminal for a herdr client attached to a throwaway named
# session, tmux types the key chord into it, and the herdr CLI is polled until
# a tab labelled "Codex" hosts a detected Codex agent. The default herdr
# session and its tabs are not touched. tmux runs as a private server, so an
# existing tmux server is not touched either. The throwaway session, its Codex
# process, and the private tmux server are removed on exit.
#
# The test reads a temporary copy of the installed config.toml with first-run
# onboarding turned off; the onboarding screen would swallow the key chord.
# The installed file is not modified.
#
# Inputs (environment, tmux key names):
#   PREFIX_KEY  herdr prefix. Default "C-s" (ctrl+s, this repo's prefix).
#   CHORD_KEY   key after the prefix. Default "C" (Shift+C).
#   KEEP=1      leave the session running for inspection; prints how to attach.
# Output: "PASS ..." and exit 0, or "FAIL ..." plus the client screen, exit 1.
#
# Example:
#   $ bash herdr/test-codex-key.sh
#   PASS: C-s then C opened tab w1:t2 "Codex"; herdr detected codex in w1:p2
set -eu

PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH
prefix_key="${PREFIX_KEY:-C-s}"
chord_key="${CHORD_KEY:-C}"
installed_config="${HERDR_CONFIG_PATH:-${XDG_CONFIG_HOME:-$HOME/.config}/herdr/config.toml}"
session="codex-key-test-$$"

for tool in herdr tmux jq; do
  command -v "$tool" >/dev/null 2>&1 || { printf 'FAIL: %s is not installed or is missing from PATH.\n' "$tool"; exit 1; }
done
[ -f "$installed_config" ] || { printf 'FAIL: %s does not exist. Run herdr/install.sh first.\n' "$installed_config"; exit 1; }
grep -q 'herdr-codex-tab' "$installed_config" || { printf 'FAIL: %s has no Codex tab key. Run herdr/install.sh first.\n' "$installed_config"; exit 1; }
[ -x "$HOME/.local/bin/herdr-codex-tab" ] || { printf 'FAIL: ~/.local/bin/herdr-codex-tab is missing. Run herdr/install.sh first.\n'; exit 1; }

work_dir="$(mktemp -d "${TMPDIR:-/tmp}/codex-key-test.XXXXXX")"
test_config="$work_dir/config.toml"
{ printf 'onboarding = false\n'; grep -v '^onboarding[[:space:]]*=' "$installed_config"; } >"$test_config"
# A shell inside herdr carries HERDR_ENV=1, which makes herdr refuse to start a
# nested client, and pane variables that aim the CLI at the caller's session.
# Dropping them lets the test run from inside herdr as well as outside it.
for var in $(env | sed -n 's/^\(HERDR_[A-Za-z0-9_]*\)=.*/\1/p'); do
  unset "$var"
done
export HERDR_CONFIG_PATH="$test_config"

# Private tmux server: it inherits the cleaned environment above. A tmux server
# that is already running would hand the client its own, older environment.
tmx() { tmux -L "$session" "$@"; }

cleanup() {
  if [ "${KEEP:-0}" = 1 ]; then
    printf 'Kept for inspection: tmux -L %s attach   (config: %s)\n' "$session" "$test_config"
    return
  fi
  tmx kill-server 2>/dev/null || true
  rm -f "${TMUX_TMPDIR:-/tmp}/tmux-$(id -u)/$session" # tmux leaves its socket file behind
  herdr session stop "$session" >/dev/null 2>&1 || true
  herdr session delete "$session" >/dev/null 2>&1 || true
  rm -rf "$work_dir"
}
trap cleanup EXIT

fail() {
  printf 'FAIL: %s\n' "$1"
  printf -- '--- herdr client screen ---\n'
  tmx capture-pane -t "$session" -p 2>/dev/null || printf '(no client screen)\n'
  exit 1
}

# -c "$work_dir": the first workspace opens in an empty directory, not a repo.
tmx new-session -d -s "$session" -x 160 -y 45 -c "$work_dir" "herdr --session $session"

attempt=0
until herdr --session "$session" workspace list 2>/dev/null | jq -e '.result.workspaces | length > 0' >/dev/null; do
  attempt=$((attempt + 1))
  [ "$attempt" -lt 60 ] || fail "herdr did not start a workspace within 15 seconds."
  sleep 0.25
done
sleep 1 # let the client finish its first draw before it receives keys

tmx send-keys -t "$session" "$prefix_key"
sleep 0.3
tmx send-keys -t "$session" "$chord_key"

attempt=0
while :; do
  tab=$(herdr --session "$session" tab list 2>/dev/null |
    jq -r '.result.tabs[]? | select(.label == "Codex") | .tab_id' | head -n 1)
  agent_pane=""
  if [ -n "$tab" ]; then
    agent_pane=$(herdr --session "$session" agent list 2>/dev/null |
      jq -r --arg tab "$tab" '.result.agents[]? | select(.agent == "codex" and .tab_id == $tab) | .pane_id' | head -n 1)
  fi
  [ -z "$agent_pane" ] || break
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 180 ]; then
    [ -n "$tab" ] || fail "$prefix_key then $chord_key did not open a tab labelled Codex within 45 seconds."
    fail "Tab $tab opened, but herdr did not detect Codex in it within 45 seconds."
  fi
  sleep 0.25
done

printf 'PASS: %s then %s opened tab %s "Codex"; herdr detected codex in %s\n' "$prefix_key" "$chord_key" "$tab" "$agent_pane"

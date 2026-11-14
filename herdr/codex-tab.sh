#!/bin/sh
#
# codex-tab.sh — open a new herdr tab and start Codex in it.
#
# Bound to prefix+shift+c in config.toml. Herdr runs custom command keys
# detached with stdout and stderr discarded, so stderr alone would be invisible
# on a key press. Each failure is therefore also appended to
# ~/.config/herdr/codex-tab.log, sent as a herdr toast (herdr's default
# `[ui.toast] delivery = "off"` hides those), and, where osascript exists,
# shown as a macOS notification.
#
# Inputs (herdr sets these for custom command keys; panes inherit the socket):
#   HERDR_BIN_PATH             herdr binary that fired the key. Default: PATH.
#   HERDR_SOCKET_PATH          Session to act on. Default: the default session.
#   HERDR_ACTIVE_WORKSPACE_ID  Workspace that gets the tab. Default: active one.
# Output: the new pane ID on stdout, for example "w1:p3".
# Exit:   0 once herdr detects Codex in the new pane, 1 on any failure.
#
# Example, from a shell inside any herdr pane:
#   $ ~/.local/bin/herdr-codex-tab
#   w1:p3
set -eu

PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"
export PATH

herdr="${HERDR_BIN_PATH:-}"
[ -n "$herdr" ] || herdr=$(command -v herdr || true)
log_file="${XDG_CONFIG_HOME:-$HOME/.config}/herdr/codex-tab.log"

fail() {
  printf 'herdr-codex-tab: %s\n' "$1" >&2
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >>"$log_file" 2>/dev/null || true
  [ -z "$herdr" ] || "$herdr" notification show "New Codex tab failed" --body "$1" >/dev/null 2>&1 || true
  if command -v osascript >/dev/null 2>&1; then
    osascript - "$1" <<'APPLESCRIPT' >/dev/null 2>&1 || true
on run arguments
  display notification (item 1 of arguments) with title "New Codex tab failed"
end run
APPLESCRIPT
  fi
  exit 1
}

[ -n "$herdr" ] || fail "herdr is not installed or is missing from PATH."
command -v jq >/dev/null 2>&1 || fail "jq is not installed or is missing from PATH."

# A herdr server with no workspace cannot hold a tab, so create a workspace
# then; its root pane takes the place of the new tab's.
if [ -n "${HERDR_ACTIVE_WORKSPACE_ID:-}" ]; then
  created=$("$herdr" tab create --workspace "$HERDR_ACTIVE_WORKSPACE_ID" --label Codex --focus 2>&1) ||
    fail "Could not create a herdr tab: $created"
elif created=$("$herdr" tab create --label Codex --focus 2>&1); then
  :
else
  created=$("$herdr" workspace create --label Codex --focus 2>&1) ||
    fail "Could not create a herdr tab or workspace: $created"
fi
pane_id=$(printf '%s' "$created" | jq -er '.result.root_pane.pane_id') ||
  fail "herdr did not return the new pane ID: $created"

# `pane run` types into the pane's interactive shell, so a `codex` shell alias
# or function applies exactly as it does when typed by hand.
"$herdr" pane run "$pane_id" codex >/dev/null ||
  fail "Could not start Codex in $pane_id."

attempt=0
while [ "$attempt" -lt 120 ]; do
  if agent=$("$herdr" agent get "$pane_id" 2>/dev/null) &&
    printf '%s' "$agent" | jq -e '.result.agent.agent == "codex"' >/dev/null; then
    printf '%s\n' "$pane_id"
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep 0.25
done
fail "Codex was not detected in $pane_id within 30 seconds. Check that tab for startup errors."

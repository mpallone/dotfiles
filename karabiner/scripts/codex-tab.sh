#!/bin/sh
set -eu

PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export PATH
unset HERDR_SOCKET_PATH HERDR_WORKSPACE_ID HERDR_TAB_ID HERDR_PANE_ID

fail() {
  printf '%s\n' "$1" >&2
  /usr/bin/osascript - "$1" <<'EOF' >/dev/null 2>&1 || true
on run arguments
  display notification (item 1 of arguments) with title "F18 Codex"
end run
EOF
  exit 1
}

herdr=$(command -v herdr) || fail "herdr is not installed or is missing from PATH."
lock_file="${TMPDIR:-/tmp}/codex-herdr-$(id -u).lock"
attempt=0
until /usr/bin/shlock -f "$lock_file" -p "$$"; do
  attempt=$((attempt + 1))
  [ "$attempt" -lt 160 ] || fail "Another F18 launch is still running. Try again shortly."
  sleep 0.25
done
trap 'rm -f "$lock_file"' EXIT
trap 'exit 1' HUP INT TERM

client_ttys=$(/bin/ps -axww -o tty=,args= | /usr/bin/awk '
  $1 != "??" && $2 ~ /(^|\/)herdr$/ &&
  (NF == 2 ||
   (NF == 4 && $3 == "--session" && $4 == "default") ||
   (NF == 5 && $3 == "session" && $4 == "attach" && $5 == "default")) {
    print "/dev/" $1
  }
')

/usr/bin/osascript - "$client_ttys" "$herdr" <<'EOF' || fail "Could not open herdr in iTerm. Check the macOS Automation permission."
on run arguments
  set clientTtys to paragraphs of (item 1 of arguments)
  set launchCommand to (quoted form of (item 2 of arguments)) & " --session default"
  tell application "iTerm"
    activate
    repeat with terminalWindow in windows
      repeat with terminalTab in tabs of terminalWindow
        repeat with terminalSession in sessions of terminalTab
          if (tty of terminalSession) is in clientTtys then
            select terminalWindow
            select terminalTab
            select terminalSession
            return
          end if
        end repeat
      end repeat
    end repeat
    if (count of windows) = 0 then
      create window with default profile
    else
      tell current window to create tab with default profile
    end if
    tell current session of current window to write text launchCommand
  end tell
end run
EOF

attempt=0
until workspaces=$("$herdr" --session default workspace list 2>/dev/null); do
  attempt=$((attempt + 1))
  [ "$attempt" -lt 60 ] || fail "herdr did not become ready within 15 seconds. Check its iTerm tab."
  sleep 0.25
done

workspace_id=$(printf '%s' "$workspaces" | /usr/bin/jq -r '.result.workspaces | (map(select(.focused)) + .)[0].workspace_id // empty')
if [ -n "$workspace_id" ]; then
  created=$("$herdr" --session default tab create --workspace "$workspace_id" --label Codex --focus 2>&1) || fail "Could not create a herdr tab: $created"
else
  created=$("$herdr" --session default workspace create --label Codex --focus 2>&1) || fail "Could not create a herdr workspace: $created"
fi
pane_id=$(printf '%s' "$created" | /usr/bin/jq -er '.result.root_pane.pane_id') || fail "herdr did not return the new pane ID."
"$herdr" --session default pane run "$pane_id" codex >/dev/null || fail "Could not start Codex in $pane_id. Check the selected herdr tab."

attempt=0
while [ "$attempt" -lt 120 ]; do
  if agent=$("$herdr" --session default agent get "$pane_id" 2>/dev/null) &&
    printf '%s' "$agent" | /usr/bin/jq -e '.result.agent.agent == "codex"' >/dev/null; then
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep 0.25
done
fail "Codex was not detected within 30 seconds. Check the selected herdr tab for startup errors."

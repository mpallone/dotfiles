#!/bin/bash
set -eu

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$script_dir/.." && pwd)"
app="$HOME/Applications/Codex Hotkey.app"
label="com.mpallone.codex-hotkey"
agent="$HOME/Library/LaunchAgents/$label.plist"
domain="gui/$(id -u)"
log_file="$HOME/Library/Logs/CodexHotkey.log"
launcher="$HOME/.local/bin/new-codex-session"

if [ -e "$launcher" ] && [ ! -L "$launcher" ]; then
  printf 'Refusing to replace an existing file: %s\n' "$launcher" >&2
  exit 1
fi

# Compile before replacing the installed helper, so a build failure preserves it.
build_dir="$(mktemp -d "${TMPDIR:-/tmp}/codex-hotkey.XXXXXX")"
trap 'rm -rf "$build_dir"' EXIT
/usr/bin/xcrun swiftc -O "$script_dir/codex-hotkey.swift" -o "$build_dir/codex-hotkey"

# bootout also handles an already-running copy; bootstrap below reports failures.
/bin/launchctl bootout "$domain/$label" >/dev/null 2>&1 || true
mkdir -p "$app/Contents/MacOS" "$HOME/.local/bin" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cp "$build_dir/codex-hotkey" "$app/Contents/MacOS/codex-hotkey"
cp "$script_dir/Info.plist" "$app/Contents/Info.plist"
/usr/bin/codesign --force --sign - --identifier "$label" "$app"
ln -sfn "$repo_dir/shortcuts/new-codex-session.sh" "$launcher"

agent_build="$build_dir/$label.plist"
/usr/bin/plutil -create xml1 "$agent_build"
/usr/bin/plutil -insert Label -string "$label" "$agent_build"
/usr/bin/plutil -insert ProgramArguments -json '[]' "$agent_build"
/usr/bin/plutil -insert ProgramArguments.0 -string "$app/Contents/MacOS/codex-hotkey" "$agent_build"
/usr/bin/plutil -insert RunAtLoad -bool YES "$agent_build"
/usr/bin/plutil -insert KeepAlive -bool YES "$agent_build"
/usr/bin/plutil -insert ThrottleInterval -integer 10 "$agent_build"
/usr/bin/plutil -insert StandardOutPath -string "$log_file" "$agent_build"
/usr/bin/plutil -insert StandardErrorPath -string "$log_file" "$agent_build"
cp "$agent_build" "$agent"
/bin/launchctl bootstrap "$domain" "$agent"
printf 'Installed Codex Hotkey and enabled it at login. Log: %s\n' "$log_file"

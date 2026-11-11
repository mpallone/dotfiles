#!/bin/bash
set -eu

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$script_dir/.." && pwd)"

link() {
  if [ -e "$2" ] && [ ! -L "$2" ]; then
    printf 'Refusing to replace an existing file or directory: %s\n' "$2" >&2
    exit 1
  fi
  ln -sfn "$1" "$2"
}

mkdir -p "$HOME/.local/bin" "$HOME/Library/Services"
link "$repo_dir/shortcuts/new-codex-session.sh" "$HOME/.local/bin/new-codex-session"
link "$script_dir/Launch Codex Session.workflow" "$HOME/Library/Services/Launch Codex Session.workflow"

# Keep F18 free of the extra modifier that appeared in the Shortcuts binding.
binding="$(cat "$script_dir/F18-binding.plist")"
/usr/bin/defaults write pbs NSServicesStatus -dict-add \
  '"com.mpallone.codex-session-quick-action - Launch Codex Session - runWorkflowAsService"' \
  "$binding"
/System/Library/CoreServices/pbs -update
printf 'Installed Launch Codex Session and assigned F18.\n'

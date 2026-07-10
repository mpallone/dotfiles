#!/usr/bin/env bash
#
# mmm_deploy.sh — deploy canonical AI-tool config to all tools via `mmm deploy`,
# reading the config path from the MMM_CONFIG environment variable.
#
# Exit codes:
#   0  deploy succeeded (or dry-run completed)
#   3  MMM_CONFIG unset/empty — caller must ask the user how to proceed
#   4  MMM_CONFIG points at a path that does not exist / is not a file
#   5  `mmm` is not on PATH
#   *  any other code is mmm's own exit status, passed through unchanged
#
# Any arguments are forwarded to `mmm deploy` (e.g. --dry-run, --tools claude,
# --type skills). On a real (non-dry-run) run the script adds --yes so mmm's
# [Y/n] overwrite/replace prompts don't stall a non-interactive invocation.
# macOS ships bash 3.2, so this stays 3.2-compatible.

set -u

# --- Gate 1: MMM_CONFIG must be set and non-empty ---------------------------
if [ -z "${MMM_CONFIG:-}" ]; then
  cat >&2 <<'EOF'
ERROR: MMM_CONFIG is not set, so I don't know which mmm config to deploy.

Set it and re-run, e.g.:
  export MMM_CONFIG=~/src/riot/not-used-by-data-foundations/mpallone/dotfiles/mmm.yaml

Or tell me the config path to use for this run.
EOF
  exit 3
fi

# --- Gate 2: the config file must exist -------------------------------------
if [ ! -f "$MMM_CONFIG" ]; then
  echo "ERROR: MMM_CONFIG points at '$MMM_CONFIG', which is not an existing file." >&2
  exit 4
fi

# --- Gate 3: mmm must be installed ------------------------------------------
if ! command -v mmm >/dev/null 2>&1; then
  cat >&2 <<'EOF'
ERROR: `mmm` is not on PATH.

Install it (editable, so repo changes are live):
  uv tool install --editable ~/src/mpallone/marks-markdown-manager
Then ensure ~/.local/bin is on your PATH.
EOF
  exit 5
fi

# --- Decide whether this is a dry run ---------------------------------------
# Dry runs never prompt, so --yes is unnecessary (and we don't add it).
dry_run="no"
for arg in "$@"; do
  if [ "$arg" = "--dry-run" ]; then
    dry_run="yes"
    break
  fi
done

echo "Using MMM_CONFIG: $MMM_CONFIG"

if [ "$dry_run" = "yes" ]; then
  echo "Dry run — no files will be written or linked."
  mmm deploy --config "$MMM_CONFIG" "$@"
  exit $?
fi

echo "Real deploy to all tools. Overwrites/replaces are auto-confirmed (--yes)."
mmm deploy --config "$MMM_CONFIG" --yes "$@"
exit $?

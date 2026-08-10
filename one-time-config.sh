#!/bin/bash
git config --global core.editor "vim"
git config --global push.default current
git config --global merge.conflictstyle diff3
git config --global user.name "Mark Pallone"
git config --global user.email "mark.c.pallone@gmail.com"
#                               ^ FILL THIS IN

# CLI tools
if command -v brew &> /dev/null; then
  brew install cloc
else
  echo "Error: Homebrew not found; cannot install cloc. Install brew first: https://brew.sh" >&2
fi

# GUI apps
if command -v brew &> /dev/null; then
  brew install --cask mos
else
  echo "Error: Homebrew not found; cannot install mos. Install brew first: https://brew.sh" >&2
fi

# Claude Code status line (macOS only)
#
# Symlinks ai/statusline.py into ~/.claude and points Claude Code's statusLine
# setting at it. The symlink means edits to the repo copy are live immediately --
# no redeploy -- so THIS CLONE MUST LIVE AT A STABLE PATH. Moving or deleting it
# breaks the status line. (This is the first part of this script that depends on
# where the repo is checked out; everything above is location-independent.)
#
# Safe to re-run: ln -sfn replaces whatever is there, and the settings.json patch
# rewrites a single key to the same value.
STATUSLINE_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/ai/statusline.py"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "Note: not macOS; skipping Claude Code status line." >&2
elif [ ! -f "$STATUSLINE_SRC" ]; then
  echo "Error: status line script not found at $STATUSLINE_SRC; skipping." >&2
else
  # Prefer Apple's system python3 (always present on macOS, no venv surprises).
  if [ -x /usr/bin/python3 ]; then
    STATUSLINE_PY=/usr/bin/python3
  else
    STATUSLINE_PY="$(command -v python3 2>/dev/null)"
  fi

  if [ -z "$STATUSLINE_PY" ]; then
    echo "Error: python3 not found; skipping Claude Code status line." >&2
  else
    mkdir -p "$HOME/.claude"
    # -f replaces an existing real file; -n avoids linking INTO the old symlink's
    # target directory when re-running.
    ln -sfn "$STATUSLINE_SRC" "$HOME/.claude/statusline.py"

    # Add ONLY the statusLine key, preserving every other setting. Written to a
    # temp file in the same directory and os.replace'd so a crash mid-write can
    # never leave a truncated settings.json (which would silently disable ALL
    # settings from that file).
    "$STATUSLINE_PY" - "$STATUSLINE_PY" <<'PY'
import json, os, sys, tempfile

interpreter = sys.argv[1]
path = os.path.expanduser("~/.claude/settings.json")
command = "%s %s/.claude/statusline.py" % (interpreter, os.path.expanduser("~"))

data = {}
if os.path.exists(path):
    try:
        with open(path) as handle:
            data = json.load(handle)
    except ValueError as error:
        sys.exit(
            "Error: %s is not valid JSON (%s); leaving it alone. "
            "Fix it by hand, then re-run this script." % (path, error)
        )
    if not isinstance(data, dict):
        sys.exit("Error: %s is not a JSON object; leaving it alone." % path)

data["statusLine"] = {"type": "command", "command": command}

directory = os.path.dirname(path)
descriptor, temporary = tempfile.mkstemp(dir=directory, prefix=".settings.json.")
try:
    with os.fdopen(descriptor, "w") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)
except BaseException:
    if os.path.exists(temporary):
        os.unlink(temporary)
    raise

print("Claude Code status line installed: %s" % command)
PY
  fi
fi


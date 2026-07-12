#!/usr/bin/env bash
#
# cloud-setup.sh — install personal Claude config into ~/.claude for
# Claude Code on the web (claude.ai/code).
#
# A web session clones only the project repo, so ~/.claude from your laptop
# is absent. This mirrors this dotfiles repo's ai/ tree into ~/.claude so
# your global instructions and skills are present in every cloud session:
#
#   ai/global-context/AGENTS.md  ->  ~/.claude/CLAUDE.md   (CC reads CLAUDE.md)
#   ai/skills/<entry>            ->  ~/.claude/skills/<entry>
#
# Invoked by the environment "Setup script" via a bootstrap that clones this
# repo first (see ai/README.md).
#
# This is a SECOND, independent path to get skills into cloud sessions,
# redundant with the claude.ai-app zip upload (whose enabled skills also load
# into cloud sessions). The two can drift; see ai/README.md.
#
# Design: copies (not symlinks) because the cloud VM is snapshotted and
# throwaway; always exits 0 so a failure never blocks session start, but
# prints [ok]/[warn] per step so nothing fails silently. Idempotent.
#
# Usage (from a checkout of this repo):  bash ai/cloud-setup.sh
#
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # this is ai/
SKILLS_SRC="$SCRIPT_DIR/skills"
CONTEXT_SRC="$SCRIPT_DIR/global-context/AGENTS.md"

CLAUDE_DIR="$HOME/.claude"
SKILLS_DST="$CLAUDE_DIR/skills"
CONTEXT_DST="$CLAUDE_DIR/CLAUDE.md"

ok()   { echo "[cloud-setup] [ok]   $*"; }
warn() { echo "[cloud-setup] [warn] $*" >&2; }

mkdir -p "$SKILLS_DST"

# --- Global instructions: AGENTS.md -> ~/.claude/CLAUDE.md -----------------
if [ -f "$CONTEXT_SRC" ]; then
  if cp "$CONTEXT_SRC" "$CONTEXT_DST"; then
    ok "global context -> $CONTEXT_DST"
  else
    warn "failed to copy $CONTEXT_SRC -> $CONTEXT_DST"
  fi
else
  warn "global context not found at $CONTEXT_SRC (skipped)"
fi

# --- Skills: everything under ai/skills/ -> ~/.claude/skills/ --------------
if [ -d "$SKILLS_SRC" ]; then
  if cp -a "$SKILLS_SRC/." "$SKILLS_DST/"; then
    ok "skills -> $SKILLS_DST"
  else
    warn "failed to copy skills from $SKILLS_SRC"
  fi
else
  warn "skills dir not found at $SKILLS_SRC (skipped)"
fi

echo "[cloud-setup] done"
exit 0

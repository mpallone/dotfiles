#!/usr/bin/env bash
#
# package_skills.sh — build claude.ai-app-ready ZIPs from this repo's skills.
#
# WHY THIS EXISTS: the claude.ai app (regular chats) has no public API for
# uploading custom skills — the only way in is a manual ZIP upload under
# Settings. There is no automating that final drag-and-drop. What we CAN
# automate is the tedious, error-prone part: building a valid, up-to-date ZIP
# for each skill and validating it against the app's rules. A GitHub Action
# runs this on every push and publishes the ZIPs to a release, so the current
# zips always exist and are always valid; the human just downloads + uploads.
# (One app upload also auto-loads the skill into cloud Claude Code sessions.)
#
# Only APP_PORTABLE skills are packaged. mmm-deploy and update-repos are
# local-machine tools (they need the mmm CLI / your local git repos) and would
# not function in the claude.ai sandbox, so they are intentionally excluded.
# The loose ai/skills/daily-ai-tools-digest.md is not a skill directory and is
# ignored by everything.
#
# Validation mirrors the claude.ai custom-skill rules:
#   name:        lowercase letters/numbers/hyphens, <= 64 chars, not containing
#                the reserved words "claude" or "anthropic"
#   description: non-empty, <= 1024 chars, no XML tags (no "<" or ">")
#
# Exit codes:
#   0  every portable skill validated and zipped
#   1  at least one portable skill failed validation or zipping (CI should fail
#      loudly so bad frontmatter never ships)
#
# Output dir defaults to <repo>/dist; override with the DIST_DIR env var.
# macOS ships bash 3.2, so this stays 3.2-compatible (POSIX `case` tests, no
# associative arrays, no `mapfile`).
#
# Usage (from anywhere):  bash ai/scripts/package_skills.sh
#
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # ai/scripts
AI_DIR="$(dirname "$SCRIPT_DIR")"                            # ai
REPO_ROOT="$(dirname "$AI_DIR")"                             # repo root
SKILLS_DIR="$AI_DIR/skills"
DIST_DIR="${DIST_DIR:-$REPO_ROOT/dist}"

# Skills that make sense on the claude.ai app / cloud Code (space-separated).
# Override with the APP_PORTABLE env var to re-scope or to test validation.
APP_PORTABLE="${APP_PORTABLE:-teach-me jira-sprint-cleanup}"

ok()   { echo "[package-skills] [ok]   $*"; }
warn() { echo "[package-skills] [warn] $*" >&2; }
err()  { echo "[package-skills] [err]  $*" >&2; }

failures=0

# --- Preconditions ----------------------------------------------------------
if ! command -v zip >/dev/null 2>&1; then
  err "the 'zip' command is not on PATH; cannot build ZIPs."
  exit 1
fi
if [ ! -d "$SKILLS_DIR" ]; then
  err "skills dir not found at $SKILLS_DIR"
  exit 1
fi

mkdir -p "$DIST_DIR"

# --- Extract a single frontmatter field from a SKILL.md ---------------------
# Handles both inline (`name: foo`) and YAML block scalars (`description: |`)
# by collecting indented continuation lines. Prints the raw value on stdout.
frontmatter_field() {
  # $1 = SKILL.md path, $2 = field name (name|description)
  awk -v field="$2" '
    /^---[ \t]*$/ { fence++; if (fence == 1) { infm = 1; next } else { exit } }
    infm != 1 { next }
    collecting == 1 {
      if ($0 ~ /^[ \t]+/) { line = $0; sub(/^[ \t]+/, "", line); val = val line " "; next }
      collecting = 0
    }
    {
      if ($0 ~ "^" field ":[ \t]*[|>]") { collecting = 1; next }
      if ($0 ~ "^" field ":[ \t]*") { val = $0; sub("^" field ":[ \t]*", "", val); next }
    }
    END { sub(/[ \t]+$/, "", val); print val }
  ' "$1"
}

# --- Validate + zip one skill -----------------------------------------------
package_one() {
  # $1 = skill name (== directory name under ai/skills/)
  name="$1"
  dir="$SKILLS_DIR/$name"

  if [ ! -f "$dir/SKILL.md" ]; then
    err "$name: no SKILL.md at $dir/SKILL.md"
    failures=$((failures + 1))
    return
  fi

  fm_name="$(frontmatter_field "$dir/SKILL.md" name)"
  fm_desc="$(frontmatter_field "$dir/SKILL.md" description)"

  # name: matches the directory, valid charset, length, no reserved words
  if [ "$fm_name" != "$name" ]; then
    err "$name: frontmatter name '$fm_name' does not match directory name."
    failures=$((failures + 1)); return
  fi
  case "$fm_name" in
    *[!a-z0-9-]*) err "$name: name must be lowercase letters/numbers/hyphens."; failures=$((failures + 1)); return ;;
  esac
  case "$fm_name" in
    *claude*|*anthropic*) err "$name: name contains a reserved word (claude/anthropic)."; failures=$((failures + 1)); return ;;
  esac
  if [ "${#fm_name}" -gt 64 ]; then
    err "$name: name exceeds 64 characters."; failures=$((failures + 1)); return
  fi

  # description: non-empty, <= 1024 chars, no XML tags
  if [ -z "$fm_desc" ]; then
    err "$name: description is empty."; failures=$((failures + 1)); return
  fi
  case "$fm_desc" in
    *"<"*|*">"*) err "$name: description contains an XML tag (< or >), which claude.ai rejects."; failures=$((failures + 1)); return ;;
  esac
  if [ "${#fm_desc}" -gt 1024 ]; then
    err "$name: description exceeds 1024 characters (${#fm_desc})."; failures=$((failures + 1)); return
  fi

  # Zip the skill folder so the archive has <name>/SKILL.md at top level.
  rm -f "$DIST_DIR/$name.zip"
  if ( cd "$SKILLS_DIR" && zip -q -r "$DIST_DIR/$name.zip" "$name" ); then
    ok "$name -> $DIST_DIR/$name.zip"
  else
    err "$name: zip failed."; failures=$((failures + 1)); return
  fi
}

# --- Package every portable skill -------------------------------------------
for skill in $APP_PORTABLE; do
  package_one "$skill"
done

# --- Report skills present but intentionally not packaged -------------------
for entry in "$SKILLS_DIR"/*/; do
  [ -d "$entry" ] || continue
  base="$(basename "$entry")"
  case " $APP_PORTABLE " in
    *" $base "*) : ;;                                   # already packaged
    *) warn "$base: present but not app-portable (skipped)." ;;
  esac
done

echo "[package-skills] done ($failures failure(s))"
[ "$failures" -eq 0 ] || exit 1
exit 0

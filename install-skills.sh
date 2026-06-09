#!/usr/bin/env bash
# Installs Claude Code skills from skills/ into ~/.claude/skills/
# Each skill is a folder under skills/ containing a SKILL.md file.
# Usage: ./install-skills.sh [--check]

set -euo pipefail

SKILLS_DIR="$(cd "$(dirname "$0")/skills" && pwd)"
DEST_DIR="$HOME/.claude/skills"
CHECK_ONLY=false

if [[ "${1:-}" == "--check" ]]; then
  CHECK_ONLY=true
fi

# Files that install flat into ~/.claude/ (not as a skill folder)
GLOBAL_FILES=(
  "profile.md"
)

# Maps ClawHub folder name → Claude Code skill name when they differ.
claude_skill_name() {
  case "$1" in
    job-application-manager) echo "application-manager" ;;
    interview-prep) echo "interview-prep" ;;
    *) echo "$1" ;;
  esac
}

stale=()
installed=()
skipped=()

echo "offerplus-cli skill installer"
echo "Source : $SKILLS_DIR"
echo "Dest   : $DEST_DIR"
echo ""

# Skill folders — each must contain a SKILL.md
for skill_dir in "$SKILLS_DIR"/*/; do
  skill_name="$(basename "$skill_dir")"
  claude_name="$(claude_skill_name "$skill_name")"
  src="$skill_dir/SKILL.md"
  dest_dir="$DEST_DIR/$claude_name"
  dest="$dest_dir/SKILL.md"

  if [[ ! -f "$src" ]]; then
    echo "  MISSING  $skill_name/SKILL.md"
    continue
  fi

  # Remove legacy README.md if present (SKILL.md is canonical)
  if [[ -f "$dest_dir/README.md" && "$CHECK_ONLY" == false ]]; then
    rm "$dest_dir/README.md"
  fi

  if [[ -f "$dest" ]]; then
    if diff -q "$src" "$dest" > /dev/null 2>&1; then
      skipped+=("$skill_name (up to date)")
    else
      stale+=("$skill_name")
      if [[ "$CHECK_ONLY" == false ]]; then
        mkdir -p "$dest_dir"
        cp "$src" "$dest"
        installed+=("$skill_name")
      fi
    fi
  else
    stale+=("$skill_name (not installed)")
    if [[ "$CHECK_ONLY" == false ]]; then
      mkdir -p "$dest_dir"
      cp "$src" "$dest"
      installed+=("$skill_name")
    fi
  fi
done

# Global files — install flat into ~/.claude/
for file in "${GLOBAL_FILES[@]}"; do
  src="$SKILLS_DIR/$file"
  dest="$HOME/.claude/$file"

  if [[ ! -f "$src" ]]; then
    echo "  MISSING  $file (expected at $src)"
    continue
  fi

  if [[ -f "$dest" ]]; then
    if diff -q "$src" "$dest" > /dev/null 2>&1; then
      skipped+=("$file (up to date)")
    else
      stale+=("$file")
      if [[ "$CHECK_ONLY" == false ]]; then
        cp "$src" "$dest"
        installed+=("$file")
      fi
    fi
  else
    stale+=("$file (not installed)")
    if [[ "$CHECK_ONLY" == false ]]; then
      cp "$src" "$dest"
      installed+=("$file")
    fi
  fi
done

if [[ "$CHECK_ONLY" == true ]]; then
  if [[ ${#stale[@]} -eq 0 ]]; then
    echo "  All skills are up to date."
  else
    echo "  Stale or missing (run without --check to install):"
    for s in "${stale[@]}"; do echo "    - $s"; done
    exit 1
  fi
else
  if [[ ${#installed[@]} -gt 0 ]]; then
    echo "  Installed:"
    for s in "${installed[@]}"; do echo "    + $s"; done
  fi
  if [[ ${#skipped[@]} -gt 0 ]]; then
    echo "  Up to date:"
    for s in "${skipped[@]}"; do echo "    · $s"; done
  fi
  echo ""
  echo "Done. Restart Claude Code to pick up changes."
fi

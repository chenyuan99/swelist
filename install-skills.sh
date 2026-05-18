#!/usr/bin/env bash
# Installs Claude Code skills from skills/ into ~/.claude/skills/
# Usage: ./install-skills.sh [--check]

set -euo pipefail

SKILLS_DIR="$(cd "$(dirname "$0")/skills" && pwd)"
DEST_DIR="$HOME/.claude/skills"
CHECK_ONLY=false

if [[ "${1:-}" == "--check" ]]; then
  CHECK_ONLY=true
fi

# Skills that install as a single README.md inside a named folder
SKILL_FILES=(
  "application-manager.md"
)

# Files that install flat into ~/.claude/ (not as a skill folder)
GLOBAL_FILES=(
  "profile.md"
)

stale=()
installed=()
skipped=()

echo "offerplus-cli skill installer"
echo "Source : $SKILLS_DIR"
echo "Dest   : $DEST_DIR"
echo ""

for file in "${SKILL_FILES[@]}"; do
  src="$SKILLS_DIR/$file"
  skill_name="${file%.md}"
  dest_dir="$DEST_DIR/$skill_name"
  dest="$dest_dir/SKILL.md"

  if [[ ! -f "$src" ]]; then
    echo "  MISSING  $file (expected at $src)"
    continue
  fi

  # Remove legacy README.md if present (SKILL.md is now canonical)
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

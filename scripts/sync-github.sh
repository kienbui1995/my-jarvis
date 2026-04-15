#!/usr/bin/env bash
set -euo pipefail

# Sync MY JARVIS to public GitHub repo, excluding internal ops files.
# Community edition = full personal AI assistant (all intelligence included).
#
# Usage:
#   ./scripts/sync-github.sh              # Sync to github/main
#   ./scripts/sync-github.sh --dry-run    # Preview exclusions
#
# Setup (one-time):
#   git remote add github git@github.com:YOUR_USER/my-jarvis.git

IGNORE_FILE=".github-sync-ignore"
REMOTE="github"
BRANCH="main"
SYNC_BRANCH="_github-sync"

if ! git remote get-url "$REMOTE" &>/dev/null; then
    echo "❌ Remote '$REMOTE' not found. Run:"
    echo "   git remote add github git@github.com:YOUR_USER/my-jarvis.git"
    exit 1
fi

[[ ! -f "$IGNORE_FILE" ]] && echo "❌ $IGNORE_FILE not found" && exit 1

# Parse ignore patterns
EXCLUDES=()
while IFS= read -r line; do
    line="${line%%#*}"
    line="$(echo "$line" | xargs)"
    [[ -z "$line" ]] && continue
    EXCLUDES+=("$line")
done < "$IGNORE_FILE"

echo "📋 Excluding ${#EXCLUDES[@]} internal patterns:"
for p in "${EXCLUDES[@]}"; do echo "   🔒 $p"; done

[[ "${1:-}" == "--dry-run" ]] && echo "🔍 Dry run — no changes." && exit 0

# Create sync branch
git branch -D "$SYNC_BRANCH" 2>/dev/null || true
git checkout -b "$SYNC_BRANCH" "$BRANCH"

# Remove internal files
for pattern in "${EXCLUDES[@]}"; do
    if [[ -e "$pattern" ]]; then
        git rm -rf --cached "$pattern" >/dev/null 2>&1 || true
        rm -rf "$pattern" 2>/dev/null || true
        echo "   🗑️  $pattern"
    fi
done

git add -A
git commit --allow-empty -m "sync: community edition" >/dev/null 2>&1 || true

echo "🚀 Pushing to $REMOTE/$BRANCH..."
git push "$REMOTE" "$SYNC_BRANCH:$BRANCH" --force
git push "$REMOTE" --tags --force 2>/dev/null || true

git checkout "$BRANCH"
git branch -D "$SYNC_BRANCH"

echo "✅ Synced to GitHub — full Community edition (excluding ${#EXCLUDES[@]} internal files)"

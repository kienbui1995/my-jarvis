#!/usr/bin/env bash
set -euo pipefail

# Sync MY JARVIS to public GitHub repo, excluding private files.
#
# Usage:
#   ./scripts/sync-github.sh              # Sync current main to github/main
#   ./scripts/sync-github.sh --dry-run    # Show what would be excluded
#
# Setup (one-time):
#   git remote add github git@github.com:YOUR_USER/my-jarvis.git

IGNORE_FILE=".github-sync-ignore"
REMOTE="github"
BRANCH="main"
SYNC_BRANCH="_github-sync"

# Check remote exists
if ! git remote get-url "$REMOTE" &>/dev/null; then
    echo "❌ Remote '$REMOTE' not found. Set up with:"
    echo "   git remote add github git@github.com:YOUR_USER/my-jarvis.git"
    exit 1
fi

# Read ignore patterns
if [[ ! -f "$IGNORE_FILE" ]]; then
    echo "❌ $IGNORE_FILE not found"
    exit 1
fi

EXCLUDES=()
while IFS= read -r line; do
    line="${line%%#*}"        # strip comments
    line="${line// /}"        # strip whitespace
    [[ -z "$line" ]] && continue
    EXCLUDES+=("$line")
done < "$IGNORE_FILE"

echo "📋 Excluding ${#EXCLUDES[@]} patterns from GitHub sync:"
for p in "${EXCLUDES[@]}"; do echo "   - $p"; done

if [[ "${1:-}" == "--dry-run" ]]; then
    echo "🔍 Dry run — no changes made."
    exit 0
fi

# Create temporary sync branch from current main
git branch -D "$SYNC_BRANCH" 2>/dev/null || true
git checkout -b "$SYNC_BRANCH" "$BRANCH"

# Remove private files
for pattern in "${EXCLUDES[@]}"; do
    if [[ -e "$pattern" ]]; then
        git rm -rf --cached "$pattern" >/dev/null 2>&1 || true
        rm -rf "$pattern" 2>/dev/null || true
        echo "   🗑️  Removed: $pattern"
    fi
done

# Commit the filtered state
git add -A
git commit --allow-empty -m "sync: filtered for public GitHub" >/dev/null 2>&1 || true

# Force push to GitHub
echo "🚀 Pushing to $REMOTE/$BRANCH..."
git push "$REMOTE" "$SYNC_BRANCH:$BRANCH" --force

# Push tags too
git push "$REMOTE" --tags --force 2>/dev/null || true

# Switch back to main and cleanup
git checkout "$BRANCH"
git branch -D "$SYNC_BRANCH"

echo "✅ Synced to GitHub (excluding ${#EXCLUDES[@]} private patterns)"

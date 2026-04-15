#!/usr/bin/env bash
set -euo pipefail

# Sync MY JARVIS to public GitHub repo.
# Strategy: Open Core — replace private modules with stubs.
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

echo "📋 Open Core sync — ${#EXCLUDES[@]} private patterns:"
for p in "${EXCLUDES[@]}"; do echo "   🔒 $p"; done

[[ "${1:-}" == "--dry-run" ]] && echo "🔍 Dry run — no changes." && exit 0

# Create sync branch
git branch -D "$SYNC_BRANCH" 2>/dev/null || true
git checkout -b "$SYNC_BRANCH" "$BRANCH"

# Remove private files
for pattern in "${EXCLUDES[@]}"; do
    if [[ -e "$pattern" ]]; then
        git rm -rf --cached "$pattern" >/dev/null 2>&1 || true
        rm -rf "$pattern" 2>/dev/null || true
    fi
done

# Generate stubs for private Python modules so imports don't break
_stub_dir() {
    local dir="$1" msg="$2"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        cat > "$dir/__init__.py" << PYEOF
"""$msg

This module is part of MY JARVIS Pro (proprietary).
The open-source version includes the framework and tools.
See: https://github.com/YOUR_USER/my-jarvis
"""
PYEOF
    fi
}

_stub_file() {
    local file="$1" msg="$2"
    local dir
    dir="$(dirname "$file")"
    mkdir -p "$dir"
    cat > "$file" << PYEOF
"""$msg — stub for open-source version.

Full implementation available in MY JARVIS Pro.
"""
PYEOF
}

# Stub: agent/nodes/
_stub_dir "backend/agent/nodes" "Agent intelligence pipeline (router, planner, evaluator)"
for node in router agent_loop delegate evaluate post_process plan_execute response multi_agent; do
    _stub_file "backend/agent/nodes/${node}.py" "Agent node: ${node}"
done
# Minimal router stub so graph.py can import
cat > backend/agent/nodes/router.py << 'PYEOF'
"""Router node — stub for open-source version."""
from agent.state import AgentState

async def router_node(state: AgentState) -> dict:
    return {"intent": "general_chat", "complexity": "simple", "selected_model": "gemini-2.0-flash"}
PYEOF

cat > backend/agent/nodes/post_process.py << 'PYEOF'
"""Post-process node — stub for open-source version."""
from agent.state import AgentState

async def post_process_node(state: AgentState) -> dict:
    return {}
PYEOF

# Stub: memory/
_stub_dir "backend/memory" "Memory intelligence (consolidation, skills, preferences)"
for mod in consolidation context_builder conversation_memory extraction knowledge_graph preference_learning service skill_learning user_profile; do
    _stub_file "backend/memory/${mod}.py" "Memory module: ${mod}"
done

# Stub: services/handlers/
_stub_dir "backend/services/handlers" "Proactive trigger handlers"

# Stub: llm/router.py
_stub_file "backend/llm/router.py" "Smart LLM model routing"
cat > backend/llm/router.py << 'PYEOF'
"""LLM Router — stub. Always returns default model."""

def select_model(complexity: str = "simple", budget: float = 0.10) -> str:
    return "gemini-2.0-flash"
PYEOF

# Stub: core/injection.py
cat > backend/core/injection.py << 'PYEOF'
"""Injection detection — stub."""

def scan_injection(text: str) -> tuple[float, str]:
    return 0.0, ""

def should_block(score: float) -> bool:
    return False
PYEOF

git add -A
git commit --allow-empty -m "sync: open-core filtered for public GitHub" >/dev/null 2>&1 || true

echo "🚀 Pushing to $REMOTE/$BRANCH..."
git push "$REMOTE" "$SYNC_BRANCH:$BRANCH" --force
git push "$REMOTE" --tags --force 2>/dev/null || true

git checkout "$BRANCH"
git branch -D "$SYNC_BRANCH"

echo "✅ Synced to GitHub (Open Core: framework public, intelligence private)"

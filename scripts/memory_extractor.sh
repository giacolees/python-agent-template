#!/usr/bin/env bash
# Advisory-only pre-commit hook: extracts one durable piece of project
# knowledge (a decision, convention, or gotcha) from the staged diff via
# the Claude Code CLI and appends it to the shared agent memory store
# (.agent-memory/). Never blocks the commit (always exits 0) and skips
# silently when the CLI is unavailable, in CI, or opted out -- mirrors
# scripts/commit_advisor.sh.
set -euo pipefail

if [[ -n "${SKIP_AGENT_MEMORY:-}" ]] || [[ -n "${CI:-}" ]]; then
  exit 0
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "[agent-memory] claude CLI not found on PATH, skipping memory extraction." >&2
  exit 0
fi

diff=$(git diff --cached)

if [[ -z "$diff" ]]; then
  exit 0
fi

prompt=$(cat <<EOF
Extract one durable piece of project knowledge from this diff - a
decision, convention, or gotcha a future contributor would need to know.
Reply with just that one sentence, or reply exactly NONE if nothing
durable is here.

Diff (may be truncated):
---
${diff:0:8000}
---
EOF
)

extracted=$(claude -p "$prompt" 2>/dev/null | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | head -1)

if [[ -z "$extracted" ]] || [[ "$extracted" == "NONE" ]]; then
  exit 0
fi

# HEAD is the parent commit, since this hook runs before the commit being
# made exists yet -- "pending" covers the very first commit in a repo.
commit_sha=$(git rev-parse --short HEAD 2>/dev/null || echo "pending")
author=$(git config user.name || echo "unknown")

echo "[agent-memory] Remembering: ${extracted}" >&2
uv run python -m python_agent_template.memory remember "$extracted" --commit "$commit_sha" --author "$author" >&2 || true
git add .agent-memory/memories.jsonl .agent-memory/INDEX.md || true

exit 0

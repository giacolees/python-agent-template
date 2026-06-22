#!/usr/bin/env bash
# Advisory-only pre-commit hook: asks the Claude Code CLI whether the
# staged diff is a commit worth making, and suggests a commit message.
# Never blocks the commit (always exits 0) and skips silently when the
# CLI is unavailable or in CI, since this is a local developer aid, not
# a correctness gate.
set -euo pipefail

if [[ -n "${SKIP_AI_COMMIT_ADVISOR:-}" ]] || [[ -n "${CI:-}" ]]; then
  exit 0
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "[commit-advisor] claude CLI not found on PATH, skipping AI commit review." >&2
  exit 0
fi

diff=$(git diff --cached)

if [[ -z "$diff" ]]; then
  exit 0
fi

prompt=$(cat <<EOF
You are reviewing a staged git diff before a commit. Be concise (under
8 lines total).

1. State whether this is a commit worth making as-is - flag it if it
   looks like an empty/no-op change, debug leftovers, or something that
   should be split or squashed with other work. One line.
2. Suggest a commit message: a subject line under 70 characters, and
   optionally a 1-2 sentence body, focused on *why* the change was made
   rather than *what* changed.

Diff (may be truncated):
---
${diff:0:8000}
---
EOF
)

echo "----- AI commit advisor -----" >&2
claude -p "$prompt" 2>&1 | sed 's/^/[commit-advisor] /' >&2 || true
echo "------------------------------" >&2

exit 0

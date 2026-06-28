#!/usr/bin/env bash
# Provider-agnostic core of compaction memory. Reads a transcript excerpt on
# stdin, asks the selected extractor for durable insights, and stores them in
# the LOCAL agent-memory store. Advisory only: always exits 0; never blocks
# compaction. Mirrors scripts/memory_extractor.sh.
set -euo pipefail

if [[ -n "${SKIP_COMPACTION_MEMORY:-}" ]] || [[ -n "${CI:-}" ]]; then
  exit 0
fi

transcript=$(cat)
if [[ -z "${transcript//[[:space:]]/}" ]]; then
  exit 0
fi

extractor_name="${AGENT_MEMORY_EXTRACTOR:-claude}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
extractor="${script_dir}/extractors/${extractor_name}.sh"

if [[ ! -x "$extractor" ]]; then
  echo "[compaction-memory] extractor '${extractor_name}' not found, skipping." >&2
  exit 0
fi

prompt=$(cat <<EOF
Extract up to 5 atomic, durable findings from this agent session -- decisions
made, gotchas hit, or non-obvious facts a future session would need. One
finding per line, no numbering or bullets. If nothing durable, output nothing.

Session transcript (may be truncated):
---
${transcript:0:12000}
---
EOF
)

insights=$(
  printf '%s' "$prompt" | "$extractor" 2>/dev/null \
    | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
    | grep -viE '^none$' \
    | grep -v '^$' \
    || true
)

if [[ -z "$insights" ]]; then
  exit 0
fi

printf '%s\n' "$insights" | uv run python -m memory remember-insights --local >&2 || true
exit 0

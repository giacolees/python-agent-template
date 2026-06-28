#!/usr/bin/env bash
# Claude Code PreCompact hook adapter. Reads the hook payload on stdin,
# flattens the recent transcript to plain text, and feeds it to the
# provider-agnostic compaction-memory core. Advisory only: always exits 0.
#
# Assumes the Claude Code transcript is JSONL where each line may carry a
# `message.content` that is a string or a list of `{type:"text", text:...}`
# blocks. Unrecognised lines are ignored, so a schema drift degrades to a
# silent no-op rather than an error.
set -euo pipefail

payload=$(cat)
transcript_path=$(
  printf '%s' "$payload" \
    | python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("transcript_path", ""))
except Exception:
    print("")' 2>/dev/null || true
)

if [[ -z "$transcript_path" ]] || [[ ! -f "$transcript_path" ]]; then
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 - "$transcript_path" <<'PY' | "${script_dir}/../compaction_memory.sh" || true
import json
import sys

path = sys.argv[1]
lines: list[str] = []
with open(path, encoding="utf-8") as handle:
    for raw in handle:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        message = obj.get("message") if isinstance(obj, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = " ".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        if text.strip():
            lines.append(text.strip())

print("\n".join(lines[-80:]))
PY
exit 0

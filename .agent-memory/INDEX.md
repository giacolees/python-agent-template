# Shared Agent Memory

Generated from `.agent-memory/memories.jsonl` — do not edit by hand.

- **2026-06-28** (`54debb314a386debd13ca71ab2cb19f9cf28ebe4`, giacolees <gektheplayer@gmail.com>): The memory system's runtime deps (mem0ai, faiss-cpu, fastembed) live in the optional 'memory' dependency-group in pyproject.toml, which a plain 'uv sync' skips. Running 'uv run python -m memory recall/remember' without them fails with ModuleNotFoundError: No module named 'mem0'. Fix: run 'uv sync --group memory' before using the memory CLI.

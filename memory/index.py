"""Markdown index generation for shared agent memory.

`.agent-memory/INDEX.md` is fully regenerated from `memories.jsonl` on
every write — never hand-edited — so that `CLAUDE.md` can point agents
at a single, always-current file to read at session start.
"""

from pathlib import Path

from memory.records import MemoryRecord

_INDEX_HEADER = (
    "# Shared Agent Memory\n\nGenerated from `.agent-memory/memories.jsonl` — do not edit by hand."
)


def render_index(records: list[MemoryRecord]) -> str:
    """Render memory records as a markdown index.

    Parameters
    ----------
    records : list[MemoryRecord]
        Records in the order they should appear in the output.

    Returns
    -------
    str
        Full markdown document text, ending in a newline.
    """
    lines = [_INDEX_HEADER, ""]
    for record in records:
        date = record.created_at[:10]
        lines.append(f"- **{date}** (`{record.commit}`, {record.author}): {record.text}")
    lines.append("")
    return "\n".join(lines)


def write_index(index_path: Path, records: list[MemoryRecord]) -> None:
    """Render and write the markdown index to disk.

    Parameters
    ----------
    index_path : Path
        Path to `INDEX.md`.
    records : list[MemoryRecord]
        Records in the order they should appear in the output.

    Returns
    -------
    None
    """
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(render_index(records), encoding="utf-8")

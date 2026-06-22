"""Plain-text JSONL storage for shared agent memory records.

`memories.jsonl` is the committed source of truth for shared agent
memory: one JSON object per line, append-only, so that concurrent
additions on different branches merge cleanly as plain text. The local
FAISS search index (see `python_agent_template.memory.client`) is a derived
cache rebuilt from this file, never the other way around.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel


class MemoryRecord(BaseModel):
    """A single shared memory entry.

    Parameters
    ----------
    id : str
        Unique identifier for the memory.
    text : str
        The durable knowledge text.
    commit : str
        Short SHA of the commit that produced this memory.
    author : str
        Git `user.name` of whoever made the commit.
    created_at : str
        ISO 8601 UTC timestamp of when the memory was created.
    """

    id: str
    text: str
    commit: str
    author: str
    created_at: str


def create_memory_record(text: str, commit: str, author: str) -> MemoryRecord:
    """Build a new `MemoryRecord` with a generated id and timestamp.

    Parameters
    ----------
    text : str
        The durable knowledge text to store.
    commit : str
        Short SHA of the commit this memory is attributed to.
    author : str
        Git `user.name` of whoever made the commit.

    Returns
    -------
    MemoryRecord
        A new record with a freshly generated `id` and `created_at`.
    """
    return MemoryRecord(
        id=str(uuid.uuid4()),
        text=text,
        commit=commit,
        author=author,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def read_memories(memories_path: Path) -> list[MemoryRecord]:
    """Read all memory records from a JSONL file.

    Parameters
    ----------
    memories_path : Path
        Path to the `memories.jsonl` file.

    Returns
    -------
    list[MemoryRecord]
        All records in file order. Empty list if the file does not exist.
    """
    if not memories_path.exists():
        return []

    records: list[MemoryRecord] = []
    with memories_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            records.append(MemoryRecord.model_validate_json(stripped))
    return records


def append_memory(memories_path: Path, record: MemoryRecord) -> None:
    """Append a single memory record as one JSON line.

    Creates the parent directory if it does not exist yet (first write
    to a fresh `.agent-memory/` directory).

    Parameters
    ----------
    memories_path : Path
        Path to the `memories.jsonl` file.
    record : MemoryRecord
        The record to append.

    Returns
    -------
    None
    """
    memories_path.parent.mkdir(parents=True, exist_ok=True)
    with memories_path.open("a", encoding="utf-8") as handle:
        handle.write(record.model_dump_json())
        handle.write("\n")

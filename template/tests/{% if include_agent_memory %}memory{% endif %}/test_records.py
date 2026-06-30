"""Tests for memory.records."""

from pathlib import Path

from memory.records import (
    append_memory,
    create_memory_record,
    read_memories,
)


def test_read_memories_returns_empty_list_when_file_missing(tmp_path: Path) -> None:
    """read_memories returns [] for a path that does not exist yet."""
    missing = tmp_path / "memories.jsonl"

    assert read_memories(missing) == []


def test_append_memory_then_read_memories_roundtrips(tmp_path: Path) -> None:
    """A record written by append_memory is read back unchanged."""
    memories_path = tmp_path / "memories.jsonl"
    record = create_memory_record(
        text="Use FAISS for local search", commit="abc1234", author="{{ author }}"
    )

    append_memory(memories_path, record)
    records = read_memories(memories_path)

    assert records == [record]


def test_append_memory_appends_without_overwriting(tmp_path: Path) -> None:
    """A second append_memory call adds a line rather than replacing the file."""
    memories_path = tmp_path / "memories.jsonl"
    first = create_memory_record(text="first", commit="a", author="x")
    second = create_memory_record(text="second", commit="b", author="y")

    append_memory(memories_path, first)
    append_memory(memories_path, second)

    assert read_memories(memories_path) == [first, second]


def test_append_memory_creates_parent_directory(tmp_path: Path) -> None:
    """append_memory creates the .agent-memory directory on first use."""
    memories_path = tmp_path / "nested" / "memories.jsonl"
    record = create_memory_record(text="text", commit="a", author="x")

    append_memory(memories_path, record)

    assert read_memories(memories_path) == [record]


def test_create_memory_record_generates_unique_ids() -> None:
    """Two records created with identical inputs still get distinct ids."""
    first = create_memory_record(text="t", commit="c", author="a")
    second = create_memory_record(text="t", commit="c", author="a")

    assert first.id != second.id

"""Tests for memory.client."""

from pathlib import Path

from mem0.embeddings.mock import MockEmbeddings

from memory.client import (
    add_to_cache,
    build_memory_client,
    is_cache_stale,
    read_cache_marker,
    rebuild_cache,
    search_memories,
    write_cache_marker,
)
from memory.records import create_memory_record

_MOCK_DIMS = 10


def test_build_memory_client_add_then_search_finds_the_memory(tmp_path: Path) -> None:
    """A record added via add_to_cache is found by a matching search."""
    memory = build_memory_client(tmp_path, MockEmbeddings(), _MOCK_DIMS)
    record = create_memory_record(
        text="Always run migrations before deploying", commit="abc1234", author="x"
    )

    add_to_cache(memory, record)
    results = search_memories(memory, "migrations", top_k=5)

    assert len(results) == 1
    assert results[0]["memory"] == record.text


def test_search_memories_respects_top_k(tmp_path: Path) -> None:
    """search_memories caps the number of returned results at top_k."""
    memory = build_memory_client(tmp_path, MockEmbeddings(), _MOCK_DIMS)
    for i in range(3):
        add_to_cache(memory, create_memory_record(text=f"fact {i}", commit="a", author="x"))

    results = search_memories(memory, "fact", top_k=2)

    assert len(results) == 2


def test_read_cache_marker_defaults_to_zero_when_missing(tmp_path: Path) -> None:
    """read_cache_marker returns 0 for a cache directory with no marker yet."""
    assert read_cache_marker(tmp_path) == 0


def test_cache_marker_round_trips(tmp_path: Path) -> None:
    """write_cache_marker then read_cache_marker returns the same value."""
    write_cache_marker(tmp_path, 3)

    assert read_cache_marker(tmp_path) == 3


def test_is_cache_stale_true_when_marker_behind_current_count(tmp_path: Path) -> None:
    """The cache is stale when memories.jsonl has grown since the last build."""
    write_cache_marker(tmp_path, 1)

    assert is_cache_stale(tmp_path, 2) is True


def test_is_cache_stale_false_when_marker_matches(tmp_path: Path) -> None:
    """The cache is not stale when the marker matches the current count."""
    write_cache_marker(tmp_path, 2)

    assert is_cache_stale(tmp_path, 2) is False


def test_rebuild_cache_indexes_every_record_and_writes_marker(tmp_path: Path) -> None:
    """rebuild_cache replays every record and records the new line count."""
    records = [
        create_memory_record(text="first fact", commit="a", author="x"),
        create_memory_record(text="second fact", commit="b", author="y"),
    ]

    memory = rebuild_cache(records, tmp_path, MockEmbeddings(), _MOCK_DIMS)
    results = search_memories(memory, "fact", top_k=5)

    assert {result["memory"] for result in results} == {"first fact", "second fact"}
    assert read_cache_marker(tmp_path) == 2


def test_rebuild_cache_clears_previous_contents(tmp_path: Path) -> None:
    """Rebuilding with a smaller record set does not leave stale entries behind."""
    first_batch = [create_memory_record(text="stale fact", commit="a", author="x")]
    rebuild_cache(first_batch, tmp_path, MockEmbeddings(), _MOCK_DIMS)

    second_batch = [create_memory_record(text="fresh fact", commit="b", author="y")]
    memory = rebuild_cache(second_batch, tmp_path, MockEmbeddings(), _MOCK_DIMS)
    results = search_memories(memory, "fact", top_k=5)

    assert {result["memory"] for result in results} == {"fresh fact"}

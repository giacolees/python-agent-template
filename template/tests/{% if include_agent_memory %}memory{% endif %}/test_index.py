"""Tests for memory.index."""

from pathlib import Path

from memory.index import render_index, write_index
from memory.records import MemoryRecord


def _record(text: str, created_at: str) -> MemoryRecord:
    return MemoryRecord(
        id="id1", text=text, commit="abc1234", author="alice", created_at=created_at
    )


def test_render_index_with_no_records_has_header_only() -> None:
    """An empty record list still produces a valid, non-empty index."""
    output = render_index([])

    assert "# Shared Agent Memory" in output
    assert "do not edit by hand" in output


def test_render_index_includes_date_commit_author_and_text() -> None:
    """Each record's date, commit, author, and text appear in the output."""
    record = _record("Use FAISS for local search", "2026-06-22T10:00:00+00:00")

    output = render_index([record])

    assert "2026-06-22" in output
    assert "abc1234" in output
    assert "alice" in output
    assert "Use FAISS for local search" in output


def test_render_index_lists_records_in_given_order() -> None:
    """render_index does not reorder records; caller controls ordering."""
    first = _record("first fact", "2026-06-22T10:00:00+00:00")
    second = _record("second fact", "2026-06-23T10:00:00+00:00")

    output = render_index([first, second])

    assert output.index("first fact") < output.index("second fact")


def test_write_index_writes_rendered_content_to_disk(tmp_path: Path) -> None:
    """write_index persists exactly what render_index produces."""
    record = _record("text", "2026-06-22T10:00:00+00:00")
    index_path = tmp_path / "INDEX.md"

    write_index(index_path, [record])

    assert index_path.read_text(encoding="utf-8") == render_index([record])

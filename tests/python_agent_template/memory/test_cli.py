"""Tests for python_agent_template.memory.cli."""

from pathlib import Path

from mem0.embeddings.base import EmbeddingBase
from mem0.embeddings.mock import MockEmbeddings

from python_agent_template.memory.cli import rebuild_index, recall, remember
from python_agent_template.memory.records import append_memory, create_memory_record

_MOCK_DIMS = 10


def _mock_embedder() -> EmbeddingBase:
    return MockEmbeddings()


def test_remember_appends_record_and_writes_index(tmp_path: Path) -> None:
    """Remember writes both memories.jsonl and INDEX.md with the new text."""
    memory_dir = tmp_path / ".agent-memory"

    remember(
        "Use FAISS for local search",
        commit="abc1234",
        author="giacolees",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    index_text = (memory_dir / "INDEX.md").read_text(encoding="utf-8")
    memories_text = (memory_dir / "memories.jsonl").read_text(encoding="utf-8")

    assert "Use FAISS for local search" in index_text
    assert "abc1234" in memories_text


def test_remember_then_recall_finds_the_memory(tmp_path: Path) -> None:
    """A memory written by remember is immediately found by recall."""
    memory_dir = tmp_path / ".agent-memory"
    remember(
        "Always run migrations before deploying",
        commit="abc1234",
        author="giacolees",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    results = recall(
        "migrations",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    assert any("migrations" in result["memory"] for result in results)


def test_recall_rebuilds_stale_cache_after_external_jsonl_append(tmp_path: Path) -> None:
    """Recall picks up a memory appended directly to the JSONL (e.g. via git pull)."""
    memory_dir = tmp_path / ".agent-memory"
    remember(
        "first memory",
        commit="a",
        author="x",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    pulled_record = create_memory_record(text="second memory from teammate", commit="b", author="y")
    append_memory(memory_dir / "memories.jsonl", pulled_record)

    results = recall(
        "teammate",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    assert any("teammate" in result["memory"] for result in results)


def test_remember_rebuilds_stale_cache_after_external_jsonl_append(tmp_path: Path) -> None:
    """Remember picks up a teammate's pulled memory that was never locally embedded.

    Regression test: if memories.jsonl gains a record via something other
    than local `remember` (e.g. a `git pull`) before the cache is rebuilt,
    a subsequent `remember` call must not write a cache marker that makes
    the cache look fresh while silently orphaning that pulled record.
    """
    memory_dir = tmp_path / ".agent-memory"
    remember(
        "first memory",
        commit="a",
        author="x",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    pulled_record = create_memory_record(text="second memory from teammate", commit="b", author="y")
    append_memory(memory_dir / "memories.jsonl", pulled_record)

    remember(
        "third memory",
        commit="c",
        author="z",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    results = recall(
        "memory",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
        top_k=10,
    )

    found_texts = {result["memory"] for result in results}
    assert "first memory" in found_texts
    assert "second memory from teammate" in found_texts
    assert "third memory" in found_texts


def test_rebuild_index_rebuilds_cache_from_all_records(tmp_path: Path) -> None:
    """rebuild_index produces a cache that recall can search successfully."""
    memory_dir = tmp_path / ".agent-memory"
    remember(
        "some memory",
        commit="a",
        author="x",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    rebuild_index(memory_dir=memory_dir, embedder_factory=_mock_embedder, embedding_dims=_MOCK_DIMS)
    results = recall(
        "memory",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    assert len(results) == 1

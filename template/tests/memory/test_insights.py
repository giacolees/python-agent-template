"""Tests for memory.insights."""

from pathlib import Path

from mem0.embeddings.base import EmbeddingBase
from mem0.embeddings.mock import MockEmbeddings
from memory.insights import store_insights

_MOCK_DIMS = 10


def _mock_embedder() -> EmbeddingBase:
    return MockEmbeddings()


def test_store_insights_writes_each_finding_to_local_store(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".agent-memory"

    stored = store_insights(
        ["Prefer FAISS for local search", "Run migrations before deploy"],
        commit="abc1234",
        author="{{ author }}",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    local_memories = (memory_dir / "local" / "memories.jsonl").read_text(encoding="utf-8")
    assert stored == ["Prefer FAISS for local search", "Run migrations before deploy"]
    assert "Prefer FAISS for local search" in local_memories
    assert "Run migrations before deploy" in local_memories
    assert not (memory_dir / "memories.jsonl").exists()  # shared store untouched


def test_store_insights_skips_blanks_and_caps_at_max(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".agent-memory"

    stored = store_insights(
        ["  ", "a", "", "b", "c", "d", "e", "f"],
        commit="c",
        author="x",
        max_findings=3,
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    assert stored == ["a", "b", "c"]


def test_store_insights_derives_commit_and_author_when_omitted(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".agent-memory"

    stored = store_insights(
        ["Use the git-derived defaults"],
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    local_memories = (memory_dir / "local" / "memories.jsonl").read_text(encoding="utf-8")
    assert stored == ["Use the git-derived defaults"]
    assert "Use the git-derived defaults" in local_memories


def test_store_insights_empty_input_writes_nothing(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".agent-memory"

    stored = store_insights(
        ["", "   "],
        commit="c",
        author="x",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    assert stored == []
    assert not (memory_dir / "local" / "memories.jsonl").exists()

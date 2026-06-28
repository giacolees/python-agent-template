"""Local mem0-backed vector store for shared agent memory search.

mem0's `Memory.add()` normally calls an LLM internally to extract facts
from raw text before storing them. That path needs an API key. This
module never uses it: callers extract durable knowledge themselves (the
`claude` CLI, via `scripts/memory_extractor.sh`) and call `add_to_cache`
with already-clean text, which stores it with `infer=False` — skipping
mem0's internal LLM step entirely. mem0 therefore only needs a local
embedder (`fastembed`) and a local vector store (`faiss-cpu`); no API
key is required anywhere in this module.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any

os.environ.setdefault("MEM0_TELEMETRY", "False")

from mem0 import Memory  # noqa: E402
from mem0.configs.embeddings.base import BaseEmbedderConfig  # noqa: E402
from mem0.embeddings.base import EmbeddingBase  # noqa: E402
from mem0.embeddings.fastembed import FastEmbedEmbedding  # noqa: E402

from memory.records import MemoryRecord  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_AGENT_ID = "{{ project_slug }}"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMS = 384  # output dimension of DEFAULT_EMBEDDING_MODEL
DEFAULT_TOP_K = 5
_COLLECTION_NAME = "memory"
_CACHE_MARKER_FILENAME = "line_count"
# mem0's EmbedderConfig/LlmConfig provider validators have no no-op option, and
# the OpenAI client raises at construction without a key. This placeholder
# satisfies Memory.from_config() harmlessly; the real embedder is swapped in
# immediately after in build_memory_client, and the llm is never invoked
# because all callers use infer=False.
_PLACEHOLDER_PROVIDER_CONFIG: dict[str, Any] = {
    "provider": "openai",
    "config": {"api_key": "unused-placeholder"},
}


def build_real_embedder() -> EmbeddingBase:
    """Construct the production fastembed embedder.

    Downloads the model on first use (one-time, ~130MB); subsequent calls
    use the local cache. Not used in automated tests — see
    `mem0.embeddings.mock.MockEmbeddings` instead.

    Returns
    -------
    EmbeddingBase
        A local, ONNX-based embedder requiring no API key.
    """
    config = BaseEmbedderConfig(model=DEFAULT_EMBEDDING_MODEL, embedding_dims=EMBEDDING_DIMS)
    return FastEmbedEmbedding(config)


def build_memory_client(cache_dir: Path, embedder: EmbeddingBase, dims: int) -> Memory:
    """Build a mem0 `Memory` client backed by a local FAISS index.

    Parameters
    ----------
    cache_dir : Path
        Directory for the local FAISS index files.
    embedder : EmbeddingBase
        Embedder instance to use for `.add()`/`.search()`. Injected by the
        caller so tests can supply `MockEmbeddings` instead of downloading
        a real model.
    dims : int
        Output dimension of `embedder`. Must match what `embedder`
        actually produces, or similarity search results are meaningless.

    Returns
    -------
    Memory
        A configured mem0 client with `embedder` installed.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "vector_store": {
            "provider": "faiss",
            "config": {
                "path": str(cache_dir),
                "collection_name": _COLLECTION_NAME,
                "embedding_model_dims": dims,
            },
        },
        "embedder": _PLACEHOLDER_PROVIDER_CONFIG,
        "llm": _PLACEHOLDER_PROVIDER_CONFIG,
    }
    memory = Memory.from_config(config)
    memory.embedding_model = embedder
    return memory


def add_to_cache(memory: Memory, record: MemoryRecord) -> None:
    """Embed and index a single memory record.

    Parameters
    ----------
    memory : Memory
        A client built by `build_memory_client`.
    record : MemoryRecord
        The record to index.

    Returns
    -------
    None
    """
    memory.add(
        record.text,
        infer=False,
        agent_id=DEFAULT_AGENT_ID,
        metadata={"memory_id": record.id, "commit": record.commit},
    )


def search_memories(memory: Memory, query: str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
    """Search indexed memories by semantic similarity.

    Parameters
    ----------
    memory : Memory
        A client built by `build_memory_client`.
    query : str
        Free-text search query.
    top_k : int, optional
        Maximum number of results, by default `DEFAULT_TOP_K`.

    Returns
    -------
    list[dict[str, Any]]
        mem0 search result dicts, each with at least `memory`, `score`,
        and `metadata` keys.
    """
    response = memory.search(query, filters={"agent_id": DEFAULT_AGENT_ID}, top_k=top_k)
    results: list[dict[str, Any]] = response["results"]
    return results


def read_cache_marker(cache_dir: Path) -> int:
    """Read the line count the local cache was last built from.

    Parameters
    ----------
    cache_dir : Path
        The cache directory.

    Returns
    -------
    int
        Recorded line count, or 0 if no marker exists yet.
    """
    marker_path = cache_dir / _CACHE_MARKER_FILENAME
    if not marker_path.exists():
        return 0
    return int(marker_path.read_text(encoding="utf-8").strip())


def write_cache_marker(cache_dir: Path, line_count: int) -> None:
    """Record the line count the local cache was built from.

    Parameters
    ----------
    cache_dir : Path
        The cache directory.
    line_count : int
        Number of records the cache reflects.

    Returns
    -------
    None
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / _CACHE_MARKER_FILENAME).write_text(str(line_count), encoding="utf-8")


def is_cache_stale(cache_dir: Path, current_line_count: int) -> bool:
    """Check whether the local FAISS cache is behind `memories.jsonl`.

    Parameters
    ----------
    cache_dir : Path
        The cache directory.
    current_line_count : int
        Current number of records in `memories.jsonl`.

    Returns
    -------
    bool
        True if the cache should be rebuilt before searching.
    """
    return read_cache_marker(cache_dir) != current_line_count


def rebuild_cache(
    records: list[MemoryRecord], cache_dir: Path, embedder: EmbeddingBase, dims: int
) -> Memory:
    """Rebuild the local FAISS cache from scratch.

    Parameters
    ----------
    records : list[MemoryRecord]
        All records to index, in any order.
    cache_dir : Path
        The cache directory. Removed and recreated.
    embedder : EmbeddingBase
        Embedder instance to use (see `build_memory_client`).
    dims : int
        Output dimension of `embedder`.

    Returns
    -------
    Memory
        A freshly built client with every record indexed.
    """
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    memory = build_memory_client(cache_dir, embedder, dims)
    for record in records:
        add_to_cache(memory, record)
    write_cache_marker(cache_dir, len(records))
    return memory

"""Command-line interface for shared agent memory.

Provides the `remember` / `recall` / `rebuild-index` subcommands run via
`python -m python_agent_template.memory` — by the pre-commit hook
(`scripts/memory_extractor.sh`) for writes, and by agents directly for
explicit semantic search.
"""

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mem0.embeddings.base import EmbeddingBase

from python_agent_template.logging_config import configure_logging
from python_agent_template.memory.client import (
    DEFAULT_TOP_K,
    EMBEDDING_DIMS,
    add_to_cache,
    build_memory_client,
    build_real_embedder,
    is_cache_stale,
    rebuild_cache,
    search_memories,
    write_cache_marker,
)
from python_agent_template.memory.index import write_index
from python_agent_template.memory.records import append_memory, create_memory_record, read_memories

DEFAULT_MEMORY_DIR = Path(".agent-memory")
_MEMORIES_FILENAME = "memories.jsonl"
_INDEX_FILENAME = "INDEX.md"
_CACHE_DIRNAME = ".cache"


def _paths(memory_dir: Path) -> tuple[Path, Path, Path]:
    """Resolve the memories/index/cache paths under a memory directory.

    Parameters
    ----------
    memory_dir : Path
        Root directory for shared agent memory (normally `.agent-memory`).

    Returns
    -------
    tuple[Path, Path, Path]
        `(memories_path, index_path, cache_dir)`.
    """
    return (
        memory_dir / _MEMORIES_FILENAME,
        memory_dir / _INDEX_FILENAME,
        memory_dir / _CACHE_DIRNAME,
    )


def remember(
    text: str,
    commit: str,
    author: str,
    memory_dir: Path = DEFAULT_MEMORY_DIR,
    embedder_factory: Callable[[], EmbeddingBase] = build_real_embedder,
    embedding_dims: int = EMBEDDING_DIMS,
) -> None:
    """Append a new shared memory and update the index and local cache.

    Parameters
    ----------
    text : str
        Durable knowledge text to remember.
    commit : str
        Short SHA of the commit this memory is attributed to.
    author : str
        Git `user.name` of whoever made the commit.
    memory_dir : Path, optional
        Root directory for shared agent memory, by default
        `DEFAULT_MEMORY_DIR`.
    embedder_factory : Callable[[], EmbeddingBase], optional
        Factory for the embedder to use, by default `build_real_embedder`.
        Tests inject a factory returning `MockEmbeddings` instead.
    embedding_dims : int, optional
        Output dimension of the embedder returned by `embedder_factory`,
        by default `EMBEDDING_DIMS`.

    Returns
    -------
    None
    """
    memories_path, index_path, cache_dir = _paths(memory_dir)

    pre_existing_records = read_memories(memories_path)
    was_stale = is_cache_stale(cache_dir, len(pre_existing_records))

    record = create_memory_record(text=text, commit=commit, author=author)
    append_memory(memories_path, record)

    records = read_memories(memories_path)
    write_index(index_path, records)

    embedder = embedder_factory()
    if was_stale:
        # The cache was already behind memories.jsonl before this record was
        # appended (e.g. a `git pull` brought in teammates' memories that
        # were never locally embedded). Rebuild from every record —
        # including the one just appended — so none are silently dropped
        # from the search cache. rebuild_cache writes the correct marker.
        rebuild_cache(records, cache_dir, embedder, embedding_dims)
    else:
        memory = build_memory_client(cache_dir, embedder, embedding_dims)
        add_to_cache(memory, record)
        write_cache_marker(cache_dir, len(records))


def recall(
    query: str,
    memory_dir: Path = DEFAULT_MEMORY_DIR,
    top_k: int = DEFAULT_TOP_K,
    embedder_factory: Callable[[], EmbeddingBase] = build_real_embedder,
    embedding_dims: int = EMBEDDING_DIMS,
) -> list[dict[str, Any]]:
    """Search shared memory, rebuilding the local cache first if stale.

    Parameters
    ----------
    query : str
        Free-text search query.
    memory_dir : Path, optional
        Root directory for shared agent memory, by default
        `DEFAULT_MEMORY_DIR`.
    top_k : int, optional
        Maximum number of results, by default `DEFAULT_TOP_K`.
    embedder_factory : Callable[[], EmbeddingBase], optional
        Factory for the embedder to use, by default `build_real_embedder`.
    embedding_dims : int, optional
        Output dimension of the embedder returned by `embedder_factory`,
        by default `EMBEDDING_DIMS`.

    Returns
    -------
    list[dict[str, Any]]
        mem0 search result dicts (see `python_agent_template.memory.client.search_memories`).
    """
    memories_path, _, cache_dir = _paths(memory_dir)
    records = read_memories(memories_path)
    embedder = embedder_factory()

    if is_cache_stale(cache_dir, len(records)):
        memory = rebuild_cache(records, cache_dir, embedder, embedding_dims)
    else:
        memory = build_memory_client(cache_dir, embedder, embedding_dims)

    return search_memories(memory, query, top_k=top_k)


def rebuild_index(
    memory_dir: Path = DEFAULT_MEMORY_DIR,
    embedder_factory: Callable[[], EmbeddingBase] = build_real_embedder,
    embedding_dims: int = EMBEDDING_DIMS,
) -> None:
    """Force a full rebuild of the local FAISS cache.

    An escape hatch for a corrupted/stale local cache; `recall` and
    `remember` already rebuild automatically when needed.

    Parameters
    ----------
    memory_dir : Path, optional
        Root directory for shared agent memory, by default
        `DEFAULT_MEMORY_DIR`.
    embedder_factory : Callable[[], EmbeddingBase], optional
        Factory for the embedder to use, by default `build_real_embedder`.
    embedding_dims : int, optional
        Output dimension of the embedder returned by `embedder_factory`,
        by default `EMBEDDING_DIMS`.

    Returns
    -------
    None
    """
    memories_path, _, cache_dir = _paths(memory_dir)
    records = read_memories(memories_path)
    embedder = embedder_factory()
    rebuild_cache(records, cache_dir, embedder, embedding_dims)


def main() -> None:
    """CLI entry point for `python -m python_agent_template.memory`.

    Returns
    -------
    None
    """
    configure_logging()
    parser = argparse.ArgumentParser(prog="python_agent_template.memory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    remember_parser = subparsers.add_parser("remember")
    remember_parser.add_argument("text")
    remember_parser.add_argument("--commit", required=True)
    remember_parser.add_argument("--author", required=True)

    recall_parser = subparsers.add_parser("recall")
    recall_parser.add_argument("query")
    recall_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)

    subparsers.add_parser("rebuild-index")

    args = parser.parse_args()

    if args.command == "remember":
        remember(args.text, args.commit, args.author)
    elif args.command == "recall":
        for result in recall(args.query, top_k=args.top_k):
            print(f"- ({result['score']:.2f}) {result['memory']}")
    elif args.command == "rebuild-index":
        rebuild_index()

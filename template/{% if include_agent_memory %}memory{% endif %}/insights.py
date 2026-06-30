"""Persist durable session insights into the local agent-memory store.

Shared core used by both the `remember-insights` CLI subcommand and the
`memory.mcp_server` MCP tool. Judging which findings are insightful is the
caller's job; this module only stores already-chosen findings, reusing the
existing `memory.cli.remember` write path so embedding/index/cache behaviour
is identical to every other write.
"""

import subprocess
from collections.abc import Callable, Iterable
from pathlib import Path

from mem0.embeddings.base import EmbeddingBase

from memory.cli import DEFAULT_MEMORY_DIR, _resolve_memory_dir, remember
from memory.client import EMBEDDING_DIMS, build_real_embedder

_MAX_FINDINGS = 5


def _default_commit() -> str:
    """Return the short HEAD sha, or ``"compaction"`` outside a git repo.

    Returns
    -------
    str
        The attribution tag stored with each insight record.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or "compaction"
    except (subprocess.SubprocessError, OSError):
        return "compaction"


def _default_author() -> str:
    """Return git ``user.name``, or ``"agent-session"`` when unset.

    Returns
    -------
    str
        The author attributed to each insight record.
    """
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or "agent-session"
    except (subprocess.SubprocessError, OSError):
        return "agent-session"


def store_insights(
    findings: Iterable[str],
    *,
    local: bool = True,
    max_findings: int = _MAX_FINDINGS,
    commit: str | None = None,
    author: str | None = None,
    memory_dir: Path = DEFAULT_MEMORY_DIR,
    embedder_factory: Callable[[], EmbeddingBase] = build_real_embedder,
    embedding_dims: int = EMBEDDING_DIMS,
) -> list[str]:
    """Persist up to ``max_findings`` insight strings to the memory store.

    Parameters
    ----------
    findings : Iterable[str]
        Candidate insight strings; blank entries are skipped.
    local : bool, optional
        Write to the gitignored local store, by default ``True``.
    max_findings : int, optional
        Maximum number of findings to store, by default ``5``.
    commit : str | None, optional
        Attribution tag; derived from git HEAD when ``None``.
    author : str | None, optional
        Author name; derived from git config when ``None``.
    memory_dir : Path, optional
        Root memory directory, by default ``DEFAULT_MEMORY_DIR``.
    embedder_factory : Callable[[], EmbeddingBase], optional
        Embedder factory, by default ``build_real_embedder``.
    embedding_dims : int, optional
        Embedder output dimension, by default ``EMBEDDING_DIMS``.

    Returns
    -------
    list[str]
        The findings actually stored, in order.
    """
    stripped = [finding.strip() for finding in findings if finding and finding.strip()]
    cleaned = stripped[:max_findings]
    if not cleaned:
        return []

    target_dir = _resolve_memory_dir(local, memory_dir)
    resolved_commit = commit if commit is not None else _default_commit()
    resolved_author = author if author is not None else _default_author()

    for finding in cleaned:
        remember(
            finding,
            commit=resolved_commit,
            author=resolved_author,
            memory_dir=target_dir,
            embedder_factory=embedder_factory,
            embedding_dims=embedding_dims,
        )
    return cleaned

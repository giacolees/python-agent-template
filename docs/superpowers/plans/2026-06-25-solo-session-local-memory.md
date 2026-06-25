# Solo-session local memory store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an agent capture durable knowledge live during a solo session, in a gitignored local store, without touching the shared git-tracked memory that's only written by the commit-time hook.

**Architecture:** Reuse the existing `remember`/`recall`/`rebuild_index` functions and `MemoryRecord`/cache machinery in `python_agent_template.memory` unchanged — they already take a `memory_dir` parameter. Add a second root path (`.agent-memory/local/`), a `--local` CLI flag that points `remember`/`rebuild-index` at it, and merge logic in `recall` so reads always see both stores.

**Tech Stack:** Python 3.12, mem0 (`Memory`, `MockEmbeddings` in tests), pytest, argparse.

## Global Constraints

- Imperative-mood, present-tense, no-trailing-period commit messages (`.agentrules/NAMING_CONVENTIONS.md` §5), e.g. `Add local memory store merge to recall`.
- New `src/` code ships with tests in the mirrored `tests/` path in the same commit (`.agentrules/COLLABORATION.md` §8).
- Run `uv run ruff check . && uv run ruff format --check . && uv run mypy src tests && uv run pytest` before each commit — don't rely on CI to catch the first round of issues.
- NumPy-style docstrings, type hints on every function, no magic numbers, no generic `except Exception` (`.agentrules/CODING_STANDARDS.md`).
- The shared store's write path (`scripts/memory_extractor.sh` → `remember()` with no `--local`) must remain byte-for-byte unchanged in behavior.

---

### Task 1: Merge local-store results into `recall`

**Files:**
- Modify: `src/python_agent_template/memory/cli.py`
- Test: `tests/python_agent_template/memory/test_cli.py`

**Interfaces:**
- Consumes: `_paths(memory_dir)` (existing, returns `(memories_path, index_path, cache_dir)`), `read_memories`, `is_cache_stale`, `rebuild_cache`, `build_memory_client`, `search_memories` — all existing, unchanged signatures.
- Produces: `_LOCAL_DIRNAME: str` module constant, `_local_dir(memory_dir: Path) -> Path`, `_search_store(memory_dir: Path, query: str, top_k: int, embedder: EmbeddingBase, embedding_dims: int) -> list[dict[str, Any]]`. `recall()`'s public signature is unchanged; Task 2 consumes `_local_dir`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/python_agent_template/memory/test_cli.py`:

```python
def test_recall_merges_shared_and_local_results(tmp_path: Path) -> None:
    """Recall surfaces memories from both the shared and local stores."""
    memory_dir = tmp_path / ".agent-memory"
    local_dir = memory_dir / "local"

    remember(
        "shared fact about migrations",
        commit="abc1234",
        author="x",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )
    remember(
        "local fact about migrations",
        commit="pending",
        author="x",
        memory_dir=local_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    results = recall(
        "migrations",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    found_texts = {result["memory"] for result in results}
    assert found_texts == {"shared fact about migrations", "local fact about migrations"}


def test_recall_without_local_store_returns_shared_only(tmp_path: Path) -> None:
    """Recall behaves exactly as before when no local store has ever been written."""
    memory_dir = tmp_path / ".agent-memory"
    remember(
        "shared only fact",
        commit="abc1234",
        author="x",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    results = recall(
        "fact",
        memory_dir=memory_dir,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    assert {result["memory"] for result in results} == {"shared only fact"}


def test_recall_caps_merged_results_at_top_k(tmp_path: Path) -> None:
    """Merging shared and local results still respects top_k overall."""
    memory_dir = tmp_path / ".agent-memory"
    local_dir = memory_dir / "local"

    for i in range(3):
        remember(
            f"shared fact {i}",
            commit="a",
            author="x",
            memory_dir=memory_dir,
            embedder_factory=_mock_embedder,
            embedding_dims=_MOCK_DIMS,
        )
    for i in range(3):
        remember(
            f"local fact {i}",
            commit="pending",
            author="x",
            memory_dir=local_dir,
            embedder_factory=_mock_embedder,
            embedding_dims=_MOCK_DIMS,
        )

    results = recall(
        "fact",
        memory_dir=memory_dir,
        top_k=2,
        embedder_factory=_mock_embedder,
        embedding_dims=_MOCK_DIMS,
    )

    assert len(results) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/python_agent_template/memory/test_cli.py -k "merges_shared_and_local or without_local_store or caps_merged" -v`
Expected: the first two FAIL with `AssertionError` (no local-store results merged in — `test_recall_without_local_store_returns_shared_only` should already PASS since it matches today's behavior, confirming the no-local-store path is untouched). The `caps_merged` test FAILS because today's `recall` never sees the local store at all, so `len(results)` reflects only the shared store's 3 records capped at top_k=2 — re-check after Step 1 that this one isn't accidentally passing for the wrong reason; if it already passes, that's fine (shared-only already respects top_k), the merge test is what proves the real gap.

- [ ] **Step 3: Implement local-store merge in `recall`**

In `src/python_agent_template/memory/cli.py`, add module-level constants/helpers near `_CACHE_DIRNAME` (after the existing `_paths` function):

```python
_LOCAL_DIRNAME = "local"


def _local_dir(memory_dir: Path) -> Path:
    """Path to the gitignored local store nested under a shared memory dir.

    Parameters
    ----------
    memory_dir : Path
        Root directory for the shared memory store.

    Returns
    -------
    Path
        `memory_dir / "local"`.
    """
    return memory_dir / _LOCAL_DIRNAME


def _search_store(
    memory_dir: Path,
    query: str,
    top_k: int,
    embedder: EmbeddingBase,
    embedding_dims: int,
) -> list[dict[str, Any]]:
    """Search a single memory store, rebuilding its cache first if stale.

    Parameters
    ----------
    memory_dir : Path
        Root directory for the store to search (shared or local).
    query : str
        Free-text search query.
    top_k : int
        Maximum number of results to return from this store.
    embedder : EmbeddingBase
        Embedder instance to use, shared across stores in one `recall` call.
    embedding_dims : int
        Output dimension of `embedder`.

    Returns
    -------
    list[dict[str, Any]]
        mem0 search result dicts from this store only.
    """
    memories_path, _, cache_dir = _paths(memory_dir)
    records = read_memories(memories_path)

    if is_cache_stale(cache_dir, len(records)):
        memory = rebuild_cache(records, cache_dir, embedder, embedding_dims)
    else:
        memory = build_memory_client(cache_dir, embedder, embedding_dims)

    return search_memories(memory, query, top_k=top_k)
```

Replace the body of `recall` (keep its signature and docstring, but update the docstring's `Returns` section to note the merge) with:

```python
    embedder = embedder_factory()
    results = _search_store(memory_dir, query, top_k, embedder, embedding_dims)

    local_dir = _local_dir(memory_dir)
    local_memories_path, _, _ = _paths(local_dir)
    if local_memories_path.exists():
        local_results = _search_store(local_dir, query, top_k, embedder, embedding_dims)
        results = sorted(results + local_results, key=lambda result: result["score"], reverse=True)[:top_k]

    return results
```

Update the `recall` docstring's `Returns` section to:

```
    Returns
    -------
    list[dict[str, Any]]
        mem0 search result dicts (see `python_agent_template.memory.client.search_memories`),
        merged across the shared store and the local store (if one exists under
        `memory_dir / "local"`), sorted by score, and capped at `top_k` overall.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/python_agent_template/memory/test_cli.py -v`
Expected: PASS — all tests in the file, including the three new ones and every pre-existing test (`test_remember_appends_record_and_writes_index`, `test_remember_then_recall_finds_the_memory`, `test_recall_rebuilds_stale_cache_after_external_jsonl_append`, `test_remember_rebuilds_stale_cache_after_external_jsonl_append`, `test_rebuild_index_rebuilds_cache_from_all_records`).

- [ ] **Step 5: Lint, format, and type-check**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src tests`
Expected: no errors. If `ruff format` reports a diff, run `uv run ruff format .` and re-check.

- [ ] **Step 6: Commit**

```bash
git add src/python_agent_template/memory/cli.py tests/python_agent_template/memory/test_cli.py
git commit -m "Merge local-store results into recall"
```

---

### Task 2: Add `--local` flag to the `remember` and `rebuild-index` CLI commands

**Files:**
- Modify: `src/python_agent_template/memory/cli.py`
- Test: `tests/python_agent_template/memory/test_cli.py`

**Interfaces:**
- Consumes: `_local_dir(memory_dir: Path) -> Path` (from Task 1), `DEFAULT_MEMORY_DIR: Path` (existing).
- Produces: `_resolve_memory_dir(local: bool, memory_dir: Path = DEFAULT_MEMORY_DIR) -> Path`, used by `main()`'s `remember`/`rebuild-index` dispatch.

- [ ] **Step 1: Write the failing tests**

Add to `tests/python_agent_template/memory/test_cli.py`:

```python
from python_agent_template.memory.cli import DEFAULT_MEMORY_DIR, _resolve_memory_dir


def test_resolve_memory_dir_local_flag_selects_local_subdir() -> None:
    """--local resolves to the gitignored local store nested under the shared dir."""
    assert _resolve_memory_dir(local=True) == DEFAULT_MEMORY_DIR / "local"


def test_resolve_memory_dir_default_selects_shared_dir() -> None:
    """Without --local, the CLI targets the shared store as before."""
    assert _resolve_memory_dir(local=False) == DEFAULT_MEMORY_DIR
```

(Add the `_resolve_memory_dir` import to the existing `from python_agent_template.memory.cli import ...` line at the top of the file rather than a second import line, if one already exists — check the current imports and merge into the single import statement.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/python_agent_template/memory/test_cli.py -k resolve_memory_dir -v`
Expected: FAIL with `ImportError: cannot import name '_resolve_memory_dir'`.

- [ ] **Step 3: Implement `_resolve_memory_dir` and wire the CLI flags**

In `src/python_agent_template/memory/cli.py`, add right after `_local_dir`:

```python
def _resolve_memory_dir(local: bool, memory_dir: Path = DEFAULT_MEMORY_DIR) -> Path:
    """Resolve the CLI's target memory directory, honoring `--local`.

    Parameters
    ----------
    local : bool
        Whether `--local` was passed.
    memory_dir : Path, optional
        Root directory for the shared memory store, by default `DEFAULT_MEMORY_DIR`.

    Returns
    -------
    Path
        `_local_dir(memory_dir)` if `local`, else `memory_dir` unchanged.
    """
    return _local_dir(memory_dir) if local else memory_dir
```

In `main()`, change the `remember_parser` block to:

```python
    remember_parser = subparsers.add_parser("remember")
    remember_parser.add_argument("text")
    remember_parser.add_argument("--commit", required=True)
    remember_parser.add_argument("--author", required=True)
    remember_parser.add_argument(
        "--local",
        action="store_true",
        help="Write to the gitignored local store instead of the shared, git-tracked one.",
    )
```

Change the `rebuild-index` subparser registration from `subparsers.add_parser("rebuild-index")` to:

```python
    rebuild_index_parser = subparsers.add_parser("rebuild-index")
    rebuild_index_parser.add_argument(
        "--local",
        action="store_true",
        help="Rebuild the local store's cache instead of the shared one's.",
    )
```

Change the dispatch block to:

```python
    if args.command == "remember":
        remember(args.text, args.commit, args.author, memory_dir=_resolve_memory_dir(args.local))
    elif args.command == "recall":
        for result in recall(args.query, top_k=args.top_k):
            print(f"- ({result['score']:.2f}) {result['memory']}")
    elif args.command == "rebuild-index":
        rebuild_index(memory_dir=_resolve_memory_dir(args.local))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/python_agent_template/memory/test_cli.py -v`
Expected: PASS — full file, including the two new tests.

- [ ] **Step 5: Lint, format, and type-check**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src tests`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/python_agent_template/memory/cli.py tests/python_agent_template/memory/test_cli.py
git commit -m "Add --local flag to remember and rebuild-index CLI commands"
```

---

### Task 3: Gitignore the local store and document solo-session usage

**Files:**
- Modify: `.gitignore`
- Modify: `.agentrules/COLLABORATION.md`

**Interfaces:**
- Consumes: nothing from earlier tasks (pure docs/config; depends on Tasks 1–2 existing so the documented command actually works).
- Produces: nothing consumed by later tasks — this is the last task in the plan.

- [ ] **Step 1: Gitignore the local store**

In `.gitignore`, find:

```
# Shared agent memory — local derived cache, never committed
.agent-memory/.cache/
```

Replace with:

```
# Shared agent memory — local derived cache, never committed
.agent-memory/.cache/
# Solo-session local memory store — gitignored, never shared with teammates
.agent-memory/local/
```

- [ ] **Step 2: Verify the ignore rule**

Run: `mkdir -p .agent-memory/local && touch .agent-memory/local/memories.jsonl && git check-ignore -v .agent-memory/local/memories.jsonl`
Expected: prints the matching `.gitignore` line and path (confirms the rule matches), then clean up: `rm -rf .agent-memory/local` (only if `.agent-memory/` didn't already exist before this step from earlier manual testing — if it did, just remove the `local` subdirectory, not the whole tree).

- [ ] **Step 3: Document solo-session usage**

In `.agentrules/COLLABORATION.md`, in section `## 9. Shared agent memory`, after the existing bullet that ends with `Set SKIP_AGENT_MEMORY=1 to opt a commit out of memory extraction, mirroring SKIP_AI_COMMIT_ADVISOR for the commit advisor.`, add a new bullet:

```
- In a normal, non-shared session (solo exploration, debugging, a scratch
  branch nobody else is working from), call
  `uv run python -m python_agent_template.memory remember "<fact>" --commit
  <short-sha-or-"pending"> --author <name> --local` proactively as durable
  knowledge surfaces, instead of waiting for the next commit. This writes to
  `.agent-memory/local/` — a gitignored store that's never shared with
  teammates. `recall` always searches both the shared and local stores and
  merges the results, so nothing written with `--local` is invisible to
  later `recall` calls in the same checkout. The commit hook remains the
  only path that writes to the shared, git-tracked store.
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore .agentrules/COLLABORATION.md
git commit -m "Document and gitignore the solo-session local memory store"
```

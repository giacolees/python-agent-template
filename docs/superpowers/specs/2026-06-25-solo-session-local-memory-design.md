# Solo-session local memory store

## Problem

Shared agent memory (`.agent-memory/memories.jsonl`) is only written by the
pre-commit hook (`scripts/memory_extractor.sh`), once per commit. That's the
right cadence for durable, team-visible knowledge — it goes through a real
commit and (implicitly) review.

But in a normal, non-shared session — solo exploration, debugging, a scratch
branch nobody else is working from — waiting for a commit to capture
anything an agent learns is too coarse. mem0's typical usage pattern is
continuous: add memories as you go, not batched at commit time. There's
currently no path for that which doesn't pollute the shared, git-tracked
store.

## Design

Two parallel stores under `.agent-memory/`:

- `.agent-memory/memories.jsonl` + `INDEX.md` — existing shared store,
  git-tracked, written only by the pre-commit hook. Unchanged.
- `.agent-memory/local/memories.jsonl` + `local/INDEX.md` +
  `local/.cache/` — new local store, entirely gitignored. Written live,
  mid-session, by the agent calling the CLI directly whenever something is
  worth remembering for itself but isn't (yet, or ever) meant for
  teammates.

Both stores reuse the exact same `remember`/`recall`/`rebuild_index`
functions and `MemoryRecord`/cache machinery already in
`python_agent_template.memory` — they already take a `memory_dir`
parameter, so this is a second root path, not new infrastructure.

### CLI changes

`python -m python_agent_template.memory`:

- `remember --local`: writes to `.agent-memory/local/` instead of
  `.agent-memory/`. The pre-commit hook never passes this flag, so the
  shared write path is unchanged.
- `rebuild-index --local`: rebuilds the local store's cache, for symmetry
  and debugging.
- `recall`: automatically searches both stores when the local one exists,
  merges results by score, and truncates to `top_k` overall. No flag —
  recall should surface everything the agent knows, not just the
  git-shared subset. When the local store doesn't exist (no solo session
  has ever run there), behavior is identical to today.

### Documentation

`.agentrules/COLLABORATION.md` §9 gets a new bullet: during a normal solo
session, call `remember --local "<fact>"` proactively as durable knowledge
surfaces, instead of relying solely on the commit hook. The commit hook
remains the only path that writes to the shared store.

`.gitignore` gets `.agent-memory/local/` (mirroring the existing
`.agent-memory/.cache/` entry).

## Out of scope

- No new mode-detection mechanism (env var/branch heuristics) — the agent
  decides per-session and passes `--local` explicitly, per user direction.
- No change to the pre-commit hook or shared-store write path.
- No UI/CLI for promoting a local memory into the shared store — manual
  for now (an agent can just re-`remember` the same text without
  `--local`).

## Testing

- `recall()` merge behavior: shared-only, local-only, both-present, and
  neither-present cases.
- `remember(..., local=True)` writes to the local dir and never touches
  `.agent-memory/memories.jsonl`.
- `rebuild_index(..., local=True)` rebuilds only the local cache.
- CLI argument parsing for the new `--local` flags.

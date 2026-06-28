# python-agent-template

Reusable Python project scaffold with AI-agent tooling baked in: coding
standards, shared agent memory, and an AI commit advisor — ready to clone
as a starting point for new projects.

## Using this as a template

To start a new project from this baseline:

```bash
gh repo create <new-project-name> --template giacolees/python-agent-template --private
git clone https://github.com/<you>/<new-project-name>
cd <new-project-name>
```

Without `gh`, use GitHub's "Use this template" button on the repo page, or
clone directly and re-point the remote:

```bash
git clone https://github.com/giacolees/python-agent-template <new-project-name>
cd <new-project-name>
git remote set-url origin https://github.com/<you>/<new-project-name>
```

Either way, follow up with the [Setup](#setup) steps below, then add your
project code under `src/`.

## Project layout

- `src/` — your application source code (empty by default; reserved for project files).
- `memory/` — reusable agent-memory tooling (CLI + mem0-backed store) shared across projects.
- `tests/` — Pytest suite.
- `configs/` — YAML configuration (hyperparameters, thresholds, hardware targets).
- `deployment/` — Dockerfiles and Kubernetes manifests.
- `.agentrules/` — coding standards binding for all agent-generated code (see
  [Agent rules](#agent-rules) below).
- `.agent-memory/` — shared, git-tracked agent memory (see
  [Shared agent memory](#shared-agent-memory) below).
- `data/` — local data directory (gitignored; do not commit raw data).

## Setup

```bash
uv sync --all-groups
uv run pre-commit install
```

## Linting, type-checking & tests

```bash
uv run ruff check .          # lint, including naming conventions (pep8-naming)
uv run ruff format .         # format
uv run mypy memory tests     # strict static type checking
uv run pytest                # tests + coverage
```

## Configuration

Application settings (hardware target, example feature flags, paths) live in `configs/*.yaml`
and are loaded via `memory.config.load_config`, never hardcoded in
source. See `configs/default.yaml` for the schema.

## Agent rules

Rules in `.agentrules/` are binding for all code, configs, and commits in
this repo — for humans and AI agents alike:

- [CODING_STANDARDS.md](.agentrules/CODING_STANDARDS.md) — type hints,
  docstrings, no magic numbers, error handling, modularity.
- [NAMING_CONVENTIONS.md](.agentrules/NAMING_CONVENTIONS.md) — identifiers,
  test files, configs, deployment artifacts, branches and commits.
- [COLLABORATION.md](.agentrules/COLLABORATION.md) — branching, worktrees,
  commits, pull requests, code review, configuration & secrets,
  dependencies, testing, and working with AI agents.

## Shared agent memory

A pre-commit hook (`scripts/memory_extractor.sh`) extracts durable
project knowledge from each commit's diff via the `claude` CLI and
appends it to `.agent-memory/memories.jsonl`, regenerating
`.agent-memory/INDEX.md`. `CLAUDE.md` points agents at that index so
shared knowledge is available at the start of every session. Query it
directly with:

```bash
uv run python -m memory recall "<query>"
```

See [.agentrules/COLLABORATION.md](.agentrules/COLLABORATION.md) §9 for
details, including the `SKIP_AGENT_MEMORY` opt-out.

For a normal, non-shared session (solo exploration, debugging, a scratch
branch), write live to a gitignored local store instead of waiting for a
commit:

```bash
uv run python -m memory remember "<fact>" --commit pending --author <name> --local
```

`recall` always searches both the shared and local stores and merges the
results, so nothing written with `--local` is invisible to later `recall`
calls in the same checkout.

### Compaction insights (local)

At each context compaction, a Claude Code `PreCompact` hook
(`scripts/hooks/precompact_claude.sh`) extracts up to five durable findings
from the session and stores them in the **local** memory store via
`python -m memory remember-insights --local`. Extraction is provider-neutral:

- **Swap the extraction LLM** with `AGENT_MEMORY_EXTRACTOR` (default `claude`;
  ships `codex` and `gemini` drivers under `scripts/extractors/`). Add a
  provider by dropping a `scripts/extractors/<name>.sh` that reads a prompt on
  stdin and prints one finding per line.
- **Other agent runtimes** can use the same capability via the MCP server
  (`.mcp.json` registers `agent-memory`, exposing `remember_insights` and
  `recall`). Wire a non-Claude runtime's compaction/session-end event to
  `scripts/compaction_memory.sh` (transcript text on stdin).
- **Opt out** for a session with `SKIP_COMPACTION_MEMORY=1`.

## AI commit advisor

A pre-commit hook (`scripts/commit_advisor.sh`) calls the Claude Code CLI on
the staged diff before each commit. It is advisory only — it never blocks the
commit — and prints:

1. Whether the change looks worth committing as-is (flags no-op/debug/
   should-be-split diffs).
2. A suggested commit message.

It skips silently if the `claude` CLI isn't installed, in CI (`$CI` set), or
if you set `SKIP_AI_COMMIT_ADVISOR=1` for a given commit.

## Releasing

A workflow (`.github/workflows/release.yml`) watches every push to `main`.
When the `version` field in `pyproject.toml` changes, it re-runs the full
lint/type-check/test gate, then tags the commit `v<version>` and publishes
a GitHub Release with auto-generated notes. Pushes that don't change the
version are a no-op for this workflow.

To cut a release: bump `version` in `pyproject.toml` in a normal PR.
Merging that PR to `main` is what ships the release — there's no separate
manual step.

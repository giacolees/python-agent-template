# python-agent-template

Reusable Python project scaffold with AI-agent tooling baked in: coding
standards, shared agent memory, and an AI commit advisor — ready to clone
as a starting point for new projects.

## Project layout

- `src/` — application source code.
- `tests/` — Pytest suite mirroring `src/`.
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
uv run mypy src tests        # strict static type checking
uv run pytest                # tests + coverage
```

## Configuration

Application settings (hardware target, example feature flags, paths) live in `configs/*.yaml`
and are loaded via `python_agent_template.config.load_config`, never hardcoded in
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
uv run python -m python_agent_template.memory recall "<query>"
```

See [.agentrules/COLLABORATION.md](.agentrules/COLLABORATION.md) §9 for
details, including the `SKIP_AGENT_MEMORY` opt-out.

## AI commit advisor

A pre-commit hook (`scripts/commit_advisor.sh`) calls the Claude Code CLI on
the staged diff before each commit. It is advisory only — it never blocks the
commit — and prints:

1. Whether the change looks worth committing as-is (flags no-op/debug/
   should-be-split diffs).
2. A suggested commit message.

It skips silently if the `claude` CLI isn't installed, in CI (`$CI` set), or
if you set `SKIP_AI_COMMIT_ADVISOR=1` for a given commit.

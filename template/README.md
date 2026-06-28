# {{ project_name }}

{{ description }}

## Project layout

- `src/{{ project_slug }}/` — your application source code.
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

> **Troubleshooting:** if `pre-commit install` fails with `Cowardly
> refusing to install hooks with core.hooksPath set`, your global git
> config redirects all hooks to a directory outside this repo (e.g. a
> tool like tokensave that sets `core.hooksPath` for its own
> `post-checkout`/`post-commit` hooks). Since git only reads hooks from
> `core.hooksPath` when it's set — never falling back to `.git/hooks/`
> — this silently disables every project's pre-commit hooks (including
> `commit_advisor.sh` and `memory_extractor.sh`) until it's resolved.
> Fix by adding a `pre-commit` dispatcher script to that global hooks
> directory that delegates to `pre-commit run --hook-stage pre-commit`
> for repos with a `.pre-commit-config.yaml`, or by unsetting
> `core.hooksPath` (`git config --global --unset core.hooksPath`) if
> you don't need whatever it was set up for.

## Linting, type-checking & tests

```bash
uv run ruff check .          # lint, including naming conventions (pep8-naming)
uv run ruff format .         # format
uv run mypy memory tests     # strict static type checking
uv run pytest                # tests + coverage
```

## Configuration

Application settings live in `configs/*.yaml` and are loaded via
`memory.config.load_config`, never hardcoded in source. See
`configs/default.yaml` for the schema.

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

## AI commit advisor

A pre-commit hook (`scripts/commit_advisor.sh`) calls the Claude Code CLI on
the staged diff before each commit. It is advisory only — it never blocks the
commit — and prints a suggested commit message.

{% if include_release_workflow %}
## Releasing

Bump `version` in `pyproject.toml` in a PR. Merging to `main` automatically
tags the commit and publishes a GitHub Release with auto-generated notes.

{% endif %}
---

*Scaffolded from [python-agent-template](https://github.com/giacolees/python-agent-template).
Pull future template updates with `uvx copier update`.*

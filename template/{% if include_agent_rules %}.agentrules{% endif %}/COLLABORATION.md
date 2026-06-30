# Collaboration Practices — {{ project_name }}

Common practices for working together in this repo — for humans and AI
agents alike. Pairs with [CODING_STANDARDS.md](CODING_STANDARDS.md) (what
the code must look like) and [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md)
(what things are called).

## 1. Branching

- Never commit directly to `main`/`master`; always work on a branch.
  CI triggers on pushes to either name, but the current default branch
  in this repo is `master` — target that one for PRs unless told the
  default has changed.
- Branch naming follows [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) §5:
  `<type>/<short-description>` (`feat/...`, `fix/...`, `chore/...`,
  `docs/...`, `refactor/...`, `test/...`).
- Keep branches scoped to one logical change. Rebase on the target branch
  before opening a PR rather than merging it in.

## 2. Worktrees

- Use a `git worktree` (not a second clone, not switching branches
  in-place) whenever work needs isolation from the current workspace:
  parallel feature branches, an agent-driven task running alongside
  interactive work, or executing a written implementation plan that
  shouldn't touch uncommitted changes already in the main checkout.
- Create worktrees as sibling directories outside the repo, named after
  the branch: `../{{ project_slug }}.<branch-name>/` (e.g.
  `../{{ project_slug }}.feat-multi-target-tracker/`). Don't nest a worktree
  inside the repo itself — it complicates `.gitignore` and tooling that
  walks the tree.
- Each worktree gets its own virtual environment (`uv sync`) — dependency
  state is not shared across worktrees.
- Remove a worktree (`git worktree remove <path>`) once its branch is
  merged or abandoned. Don't leave stale worktrees around; run
  `git worktree list` periodically to check for leftovers.
- Never run two worktrees against the same branch at once — checking out
  a branch already in use by another worktree fails by design, and is a
  sign work should be sequenced instead of parallelized.

## 3. Commits

- Commit messages follow [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) §5
  (imperative mood, focused on *why*).
- Before committing, the AI commit advisor (`scripts/commit_advisor.sh`,
  wired into `.pre-commit-config.yaml`) reviews the staged diff and prints
  a worth-it verdict plus a suggested message. It is advisory only — read
  it, but use your own judgment on whether to act on it.
- Keep commits small and reviewable. Squash exploratory/fixup commits
  before opening a PR; don't squash after a PR has reviewers attached
  unless asked.
- Never use `--no-verify` to skip hooks; if a hook fails, fix the cause.

## 4. Pull requests

- Every change lands via PR, even small ones — there is no direct-push
  workflow on shared branches.
- PR descriptions must follow the structure outlined in
  [PR_TEMPLATE.md](PR_TEMPLATE.md) (Summary and Verification sections).
- PR description states *why* the change is needed, not just what
  changed (the diff already shows what changed).
- All CI checks (ruff lint, ruff format, mypy, pytest) must pass before
  merge. Do not merge with a known-failing or skipped check.
- Prefer one focused PR per concern over one large PR bundling unrelated
  changes, so review and rollback stay cheap.

## 5. Code review

- Treat review feedback as a request to verify and discuss, not to
  blindly implement — if a suggestion seems technically off, say so with
  reasoning rather than applying it silently.
- Reviewers check against [CODING_STANDARDS.md](CODING_STANDARDS.md) and
  [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) explicitly: type hints,
  NumPy docstrings, no magic numbers, no generic `except Exception`, no
  `print()`-based logging, single-responsibility functions.
- Approve only what you've actually read. "LGTM" on an unread diff
  defeats the purpose of review.

## 6. Configuration & secrets

- New hyperparameters, thresholds, or hardware targets go into
  `configs/*.yaml` and the corresponding Pydantic model in
  `memory.config`, not into source as literals.
- Never commit `.env`, credentials, or API keys. Add new required
  environment variables to `.env.example` (placeholder values only).
- The `detect-secrets` pre-commit hook scans staged diffs against
  `.secrets.baseline` as a backstop. If it flags a genuine secret, remove
  it from the diff rather than baselining it; only re-run
  `detect-secrets scan --baseline .secrets.baseline` to update the
  baseline for confirmed false positives.

## 7. Dependencies

- When `pyproject.toml` dependencies change, run `uv lock` (or
  `uv sync`) and commit the updated `uv.lock` in the same commit —
  never let the lockfile drift from `pyproject.toml`.

## 8. Testing

- New `src/` code ships with tests in the mirrored `tests/` path (see
  [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) §2) in the same PR, not
  as a follow-up.
- Run the exact CI sequence locally before pushing — don't rely on CI to
  catch the first round of issues:
  `uv run ruff check . && uv run ruff format --check . && uv run mypy src tests && uv run pytest`
- `pytest` runs with coverage enabled (`--cov=src`, see `pyproject.toml`).
  New code should not drop overall coverage; if a change can't be
  meaningfully unit-tested (e.g. it's pure I/O glue), say so in the PR
  description rather than leaving it silently uncovered.

{% if include_agent_memory %}## 9. Shared agent memory

- `.agent-memory/memories.jsonl` is a git-tracked, append-only log of
  durable project knowledge (decisions, conventions, gotchas) contributed
  automatically by a pre-commit hook (`scripts/memory_extractor.sh`),
  which asks the `claude` CLI to extract one sentence of durable
  knowledge from each commit's diff, or nothing if there isn't any.
- `.agent-memory/INDEX.md` is regenerated from `memories.jsonl` on every
  write and is referenced from `CLAUDE.md` so agents see it automatically
  at the start of a session.
- `.agent-memory/.cache/` (the local FAISS search index) is gitignored —
  it's a derived artifact rebuilt from `memories.jsonl`, never committed,
  so concurrent memory additions on different branches never produce
  binary merge conflicts.
- Query shared memory directly with
  `uv run python -m memory recall "<query>"`.
- Set `SKIP_AGENT_MEMORY=1` to opt a commit out of memory extraction,
  mirroring `SKIP_AI_COMMIT_ADVISOR` for the commit advisor.
- In a normal, non-shared session (solo exploration, debugging, a scratch
  branch nobody else is working from), call
  `uv run python -m memory remember "<fact>" --commit
  <short-sha-or-"pending"> --author <name> --local` proactively as durable
  knowledge surfaces, instead of waiting for the next commit. This writes to
  `.agent-memory/local/` — a gitignored store that's never shared with
  teammates. `recall` always searches both the shared and local stores and
  merges the results, so nothing written with `--local` is invisible to
  later `recall` calls in the same checkout. The commit hook remains the
  only path that writes to the shared, git-tracked store.
{% if include_compaction_memory %}- Session insights are captured automatically at each compaction into the
  local (gitignored) store. Swap the extractor with `AGENT_MEMORY_EXTRACTOR`
  or opt out with `SKIP_COMPACTION_MEMORY=1`. See the README "Compaction
  insights (local)" subsection.
{% endif %}
{% endif %}## {% if include_agent_memory %}10{% else %}9{% endif %}. Working with AI agents

- Agents (Claude Code or otherwise) follow every rule in this directory
  exactly as a human contributor would — there is no relaxed standard for
  agent-generated code.
- Agents must not bypass hooks, force-push, or merge without the explicit
  authorization scope the user gave for that action.
- When an agent's change is ambiguous in scope, it should ask rather than
  guess — especially for anything hard to reverse (schema changes, deleted
  files, force operations).

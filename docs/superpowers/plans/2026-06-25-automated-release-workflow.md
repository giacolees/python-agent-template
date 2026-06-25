# Automated Release Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a GitHub Actions workflow that tags and publishes a GitHub Release whenever a version bump in `pyproject.toml` lands on `main`.

**Architecture:** A single new workflow, `.github/workflows/release.yml`, triggered on `push` to `main`. It reads the version from `pyproject.toml` with `grep`/`sed` (no new Python dependency), compares it to the latest existing tag (treating "no tags" as `v0.0.0`), and — only if the version changed — re-runs the same lint/type-check/test gate `ci.yml` runs, then tags the commit `v<version>` and creates a GitHub Release with `gh release create --generate-notes`. No new `src/` code; this is pure CI configuration plus a README doc update, matching how the existing `## Shared agent memory` and `## AI commit advisor` sections document the project's other automation hooks.

**Tech Stack:** GitHub Actions, bash (`grep`/`sed`/`git`), `gh` CLI (preinstalled on `ubuntu-latest` runners), the existing `uv`-based lint/test toolchain.

## Global Constraints

- Imperative-mood, present-tense, no-trailing-period commit messages (`.agentrules/NAMING_CONVENTIONS.md` §5).
- Never commit directly to `main`; this work lands via PR (`.agentrules/COLLABORATION.md`).
- The release job's gate must run the exact same command sequence as `ci.yml`: `uv sync --all-groups`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src tests`, `uv run pytest` (spec: "runs the same sequence `ci.yml` runs").
- Trigger is `push` to `main` only — no PR-time dry-run, per spec's "Trigger scope: main-only" decision.
- Tag format is `v<version>` (e.g. `v0.1.0`); release notes are GitHub's auto-generated notes via `--generate-notes`, no `CHANGELOG.md` (spec: "Out of scope" section).
- The job needs `contents: write` permission on the default `GITHUB_TOKEN` — no new secrets (spec).
- If the version is unchanged from the latest tag, the job must exit successfully with no tag/release created — this is the normal case for most pushes to `main`, not a failure (spec, step 1).

---

### Task 1: Add the release workflow and document it in the README

**Files:**
- Create: `.github/workflows/release.yml`
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing from other tasks — this is the only task in the plan.
- Produces: nothing consumed elsewhere — this is the only task in the plan.

- [ ] **Step 1: Write the workflow file**

Create `.github/workflows/release.yml` with this exact content:

```yaml
name: Release

on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Read current version
        id: current
        run: |
          VERSION=$(grep -m1 '^version = ' pyproject.toml | sed -E 's/version = "(.*)"/\1/')
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"

      - name: Read latest released version
        id: latest
        run: |
          LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
          echo "version=${LATEST_TAG#v}" >> "$GITHUB_OUTPUT"

      - name: Check whether the version changed
        id: check
        run: |
          if [ "${{ steps.current.outputs.version }}" = "${{ steps.latest.outputs.version }}" ]; then
            echo "changed=false" >> "$GITHUB_OUTPUT"
          else
            echo "changed=true" >> "$GITHUB_OUTPUT"
          fi

      - name: Install uv
        if: steps.check.outputs.changed == 'true'
        uses: astral-sh/setup-uv@v3

      - name: Set up Python
        if: steps.check.outputs.changed == 'true'
        run: uv python install

      - name: Install dependencies
        if: steps.check.outputs.changed == 'true'
        run: uv sync --all-groups

      - name: Lint with ruff
        if: steps.check.outputs.changed == 'true'
        run: uv run ruff check .

      - name: Check formatting with ruff
        if: steps.check.outputs.changed == 'true'
        run: uv run ruff format --check .

      - name: Type-check with mypy
        if: steps.check.outputs.changed == 'true'
        run: uv run mypy src tests

      - name: Run tests
        if: steps.check.outputs.changed == 'true'
        run: uv run pytest

      - name: Tag and create release
        if: steps.check.outputs.changed == 'true'
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          TAG="v${{ steps.current.outputs.version }}"
          git tag "$TAG"
          git push origin "$TAG"
          gh release create "$TAG" --generate-notes
```

- [ ] **Step 2: Validate the YAML is well-formed**

Run: `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"`
Expected: no output, exit code 0. (`pyyaml` is already a project dependency — see `pyproject.toml`'s `[project] dependencies`.)

- [ ] **Step 3: Verify the version-read step against the real `pyproject.toml`**

Run: `grep -m1 '^version = ' pyproject.toml | sed -E 's/version = "(.*)"/\1/'`
Expected output: `0.1.0` (the current value of `version` in `pyproject.toml`). This is the exact command used in the workflow's "Read current version" step — confirming it extracts the right value before relying on it in CI.

- [ ] **Step 4: Verify the latest-tag fallback for a repo with no tags**

Run: `git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0"`
Expected output: `v0.0.0` (no tags exist yet in this repo, so the command after `||` runs). This confirms the workflow's "no tags yet" baseline behaves as the spec requires: "if no tags exist yet, treat the baseline as absent so any version present counts as new."

- [ ] **Step 5: Add a "Releasing" section to the README**

In `README.md`, add a new section after the existing `## AI commit advisor` section (which is currently the last section in the file), with this exact content:

```markdown

## Releasing

A workflow (`.github/workflows/release.yml`) watches every push to `main`.
When the `version` field in `pyproject.toml` changes, it re-runs the full
lint/type-check/test gate, then tags the commit `v<version>` and publishes
a GitHub Release with auto-generated notes. Pushes that don't change the
version are a no-op for this workflow.

To cut a release: bump `version` in `pyproject.toml` in a normal PR.
Merging that PR to `main` is what ships the release — there's no separate
manual step.
```

- [ ] **Step 6: Confirm the full project gate still passes**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src tests && uv run pytest`
Expected: all four commands succeed (no `src/` code changed, so this should pass exactly as it did before this task).

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/release.yml README.md
git commit -m "Add automated release workflow triggered by version bumps"
```

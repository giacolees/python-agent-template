# Automated release workflow

## Problem

`pyproject.toml` declares `version = "0.1.0"` but the project has no tags,
no GitHub Releases, and no automation tying a version number to a shippable
snapshot. Anyone cloning this template as a starting point (see the
"Using this as a template" README section) has no way to tell which commit
corresponds to which version, and there's no repeatable process for cutting
a release.

## Design

A new workflow, `.github/workflows/release.yml`, triggered on `push` to
`main` (mirroring `ci.yml`'s trigger), does the following on every push:

1. **Detect a version change.** Read `version` from `pyproject.toml`.
   Compare it against the latest existing tag (stripping the `v` prefix);
   if no tags exist yet, treat the baseline as absent so any version
   present counts as new. If the version is unchanged from the latest tag,
   the job exits successfully with no further action — this is the normal
   case for most pushes to `main` (e.g. doc-only PRs like the README
   update), not a failure.

2. **Gate on the full check suite.** If the version changed, run the same
   sequence `ci.yml` runs: `uv sync --all-groups && uv run ruff check . &&
   uv run ruff format --check . && uv run mypy src tests && uv run
   pytest`. This workflow re-runs the gate itself rather than depending on
   `ci.yml`'s separate run for the same commit, so it never depends on
   `ci.yml`'s naming, timing, or job structure.

3. **Tag and release.** On success, create tag `v<version>` at the current
   commit, push it, and create a GitHub Release for that tag using `gh
   release create v<version> --generate-notes` — GitHub's built-in
   auto-generated notes (categorized merged PRs/commits since the previous
   tag, with contributor credits). No `CHANGELOG.md` to maintain.

**Trigger scope:** main-only. `ci.yml` already lints and tests every PR;
this workflow only needs to act once a version bump lands on `main`, where
the actual release happens. No PR-time dry-run.

**Permissions:** the job needs `contents: write` (to push the tag and
create the release) on the default `GITHUB_TOKEN` — no new secrets.

**Cutting a release:** bump `version` in `pyproject.toml` in a normal PR;
merging it to `main` is what ships the release. Nothing else triggers it.

## Out of scope

- No `CHANGELOG.md` (superseded by GitHub's auto-generated notes).
- No PyPI publishing — this is a template repo meant to be cloned, not an
  installable package.
- No automatic version bumping (conventional commits, semantic-release,
  etc.) — the human chooses and writes the new version number.
- No PR-time dry-run of the release gate.

## Testing

- Unit-testable logic is minimal (a version-compare and a tag-exists
  check); verify by exercising the workflow itself:
  - A push to `main` with no version change: workflow runs, detects no
    change, exits with no tag/release created.
  - A push to `main` with a version bump (e.g. to `0.1.1`): workflow runs
    the gate, creates tag `v0.1.1`, and a GitHub Release appears with
    auto-generated notes.
  - A version bump that fails lint/type-check/tests: workflow fails before
    tagging; no tag or release is created.

# Pull Request Template — {{ project_name }}

When opening a Pull Request (whether as a human or an AI agent), format the PR description using the following structure. This ensures all changes are easy to review and verification steps are clear.

## Summary
- High-level overview of the changes.
- State *why* the change is needed (the diff already shows what changed).
- Use bullet points for multiple logical changes.

## Verification
- Explain how the changes were tested and verified.
- Mention any specific commands run (e.g., `uv run pytest`, `uv run ruff check .`).
- Call out if any specific edge cases were manually verified.

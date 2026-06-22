# CLAUDE.md

Instructions for AI agents (Claude Code or otherwise) working in this repo.

## Before starting any task

Read `.agent-memory/INDEX.md` first. It's a shared, git-tracked log of
durable project knowledge — decisions, conventions, gotchas — contributed
automatically by every collaborator's agent as commits land. Treat it as
context any teammate would already have.

For deeper, query-specific search beyond what's in the index, run:

```bash
uv run python -m python_agent_template.memory recall "<query>"
```

## Binding rules

Follow every rule in `.agentrules/` exactly, for human and AI
contributions alike:

- [.agentrules/CODING_STANDARDS.md](.agentrules/CODING_STANDARDS.md)
- [.agentrules/NAMING_CONVENTIONS.md](.agentrules/NAMING_CONVENTIONS.md)
- [.agentrules/COLLABORATION.md](.agentrules/COLLABORATION.md)

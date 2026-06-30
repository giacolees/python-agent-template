# Agent Coding Standards — {{ project_name }}

These rules are binding for all code generated or modified in this repository,
by humans or AI agents. They exist to keep the pipeline auditable, testable,
and safe to run against real sensor/hardware targets.

## 1. Strict Type Hinting

- Every function and method signature MUST have type hints for all
  parameters and the return value (including `-> None`).
- Do not use bare `Any` to bypass typing unless interfacing with an
  untyped third-party library, and note why in a comment. `mem0`, `faiss`,
  and `fastembed` are the canonical example in this repo (see the
  `ignore_missing_imports` override for them in `pyproject.toml`'s
  `[tool.mypy]` config) — wrapping their calls with `Any` and a short
  comment is acceptable; don't add per-call `# type: ignore` instead.

## 2. Docstrings

- Every public function, method, and class MUST have a NumPy-style
  docstring.
- Docstrings MUST explicitly include `Parameters`, `Returns`, and
  `Raises` sections (omit a section only if it is truly empty, e.g. a
  function with no parameters).

## 3. No Magic Numbers

- Hyperparameters, sensor thresholds, hardware targets (e.g. A100 vs.
  DGX), file paths, and other tunable values MUST be injected via
  configuration files (see `configs/`), not hardcoded in source.
- Constants that are genuinely fixed (e.g. mathematical constants)
  may remain as named module-level constants, not inline literals.

## 4. Error Handling

- Generic `except Exception:` (or bare `except:`) blocks are strictly
  forbidden. Catch the narrowest specific exception type(s) that the
  call can actually raise.
- Use semantic logging (`logging.info`, `logging.warning`,
  `logging.error`, etc.) instead of `print()` for all runtime
  diagnostics.

## 5. Modularity

- Functions and methods must be scoped to a single responsibility.
- Separate I/O operations (file/network/hardware access) from pure
  processing and mathematical logic, so that the latter can be
  unit-tested in `tests/` without mocking I/O.

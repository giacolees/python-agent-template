"""Smoke tests for the compaction-memory shell scripts."""

import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _is_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def test_extractor_drivers_exist_and_parse() -> None:
    for name in ("claude", "codex", "gemini"):
        script = REPO / "scripts" / "extractors" / f"{name}.sh"
        assert _is_executable(script), f"{script} missing or not executable"
        # bash -n is a syntax check with no execution.
        subprocess.run(["bash", "-n", str(script)], check=True)

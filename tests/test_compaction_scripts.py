"""Smoke tests for the compaction-memory shell scripts."""

import json
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


def test_core_script_noops_when_skip_set() -> None:
    script = REPO / "scripts" / "compaction_memory.sh"
    assert _is_executable(script), f"{script} missing or not executable"
    result = subprocess.run(
        [str(script)],
        input="some transcript text",
        text=True,
        capture_output=True,
        env={**os.environ, "SKIP_COMPACTION_MEMORY": "1"},
    )
    assert result.returncode == 0


def test_core_script_noops_on_empty_stdin() -> None:
    script = REPO / "scripts" / "compaction_memory.sh"
    env = {key: value for key, value in os.environ.items() if key != "CI"}
    result = subprocess.run(
        [str(script)],
        input="",
        text=True,
        capture_output=True,
        env=env,
    )
    assert result.returncode == 0


def test_precompact_adapter_noops_on_invalid_payload() -> None:
    script = REPO / "scripts" / "hooks" / "precompact_claude.sh"
    assert _is_executable(script), f"{script} missing or not executable"
    result = subprocess.run(
        [str(script)],
        input="not json",
        text=True,
        capture_output=True,
        env={**os.environ, "SKIP_COMPACTION_MEMORY": "1"},
    )
    assert result.returncode == 0


def test_registration_files_are_valid_json() -> None:
    mcp_config = json.loads((REPO / ".mcp.json").read_text(encoding="utf-8"))
    assert "agent-memory" in mcp_config["mcpServers"]

    settings = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    precompact = settings["hooks"]["PreCompact"]
    commands = [
        hook["command"]
        for entry in precompact
        for hook in entry["hooks"]
    ]
    assert "scripts/hooks/precompact_claude.sh" in commands

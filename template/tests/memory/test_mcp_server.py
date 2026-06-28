"""Tests for memory.mcp_server tool delegation."""

import memory.mcp_server as mcp_server
import pytest


def test_remember_insights_tool_delegates_to_store(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_store(findings: list[str], **kwargs: object) -> list[str]:
        captured["findings"] = list(findings)
        return list(findings)

    monkeypatch.setattr(mcp_server, "store_insights", fake_store)

    result = mcp_server.remember_insights(["alpha", "beta"])

    assert captured["findings"] == ["alpha", "beta"]
    assert result == "stored 2 insight(s)"


def test_recall_tool_returns_memory_texts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mcp_server,
        "cli_recall",
        lambda query, top_k=5: [{"memory": "found thing", "score": 0.9}],
    )

    assert mcp_server.recall("anything") == ["found thing"]

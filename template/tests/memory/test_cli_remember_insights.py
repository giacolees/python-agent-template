"""Tests for the `remember-insights` CLI subcommand."""

import io
import sys

import memory.cli as cli
import pytest


def test_remember_insights_reads_stdin_and_calls_store(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_store(findings: list[str], *, local: bool = True, **kwargs: object) -> list[str]:
        captured["findings"] = list(findings)
        captured["local"] = local
        return list(findings)

    monkeypatch.setattr("memory.insights.store_insights", fake_store)
    monkeypatch.setattr(sys, "argv", ["memory", "remember-insights"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("first finding\n\nsecond finding\n"))

    cli.main()

    assert captured["findings"] == ["first finding", "second finding"]
    assert captured["local"] is True

"""Tests for CLI update command."""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Any

import pytest

from acuity_cli.commands import update


class RunRecorder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, cmd: list[str], **_: Any) -> None:
        self.calls.append(cmd)


class OutputRecorder:
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    def __call__(self, data: dict[str, Any], *_: Any, **__: Any) -> None:
        self.payload = data


def _base_args() -> argparse.Namespace:
    return argparse.Namespace(pipx=False, venv=None)


def test_update_runs_pip_install(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = RunRecorder()
    output = OutputRecorder()

    monkeypatch.setattr(update.subprocess, "run", runner)
    monkeypatch.setattr(update, "print_output", output)

    result = update.run(_base_args(), output_format="json", quiet=True)

    assert result == 0
    assert runner.calls
    assert runner.calls[0][:4] == [sys.executable, "-m", "pip", "install"]
    assert "dc-acuity-cli" in runner.calls[0]
    assert output.payload is not None
    assert output.payload["updated"] is True


def test_update_pep668_guidance(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_: Any, **__: Any) -> None:
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=[sys.executable, "-m", "pip", "install", "-U", "dc-acuity-cli"],
            stderr="externally-managed-environment",
        )

    output = OutputRecorder()
    monkeypatch.setattr(update.subprocess, "run", _raise)
    monkeypatch.setattr(update, "print_output", output)

    result = update.run(_base_args(), output_format="json", quiet=True)

    assert result == 2
    assert output.payload is not None
    assert output.payload["error"] == "externally-managed-environment"

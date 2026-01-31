"""Tests for loading credentials via ops CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from acuity_cli import config as config_module
from acuity_cli.config import load_config


class _FakeCompletedProcess:
    def __init__(self, stdout: str, returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = ""


def test_load_config_fetches_ops_and_saves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fetch missing credentials from ops and persist them."""
    config_path = tmp_path / "config.json"
    calls: list[list[str]] = []

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        **kwargs: Any,
    ) -> _FakeCompletedProcess:
        calls.append(cmd)
        field_index = cmd.index("--field") + 1
        field = cmd[field_index]
        if field == "user_id":
            return _FakeCompletedProcess("user-123\n")
        if field == "api_key":
            return _FakeCompletedProcess("api-key-456\n")
        return _FakeCompletedProcess("", returncode=1)

    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/ops")
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(config_module, "load_dotenv", lambda: None)
    monkeypatch.setenv("ACUITY_CONFIG", str(config_path))
    monkeypatch.delenv("ACUITY_USER_ID", raising=False)
    monkeypatch.delenv("ACUITY_API_KEY", raising=False)

    config = load_config(no_input=True)

    assert config.user_id == "user-123"
    assert config.api_key == "api-key-456"
    assert config_path.exists()

    saved = json.loads(config_path.read_text())
    assert saved["user_id"] == "user-123"
    assert saved["api_key"] == "api-key-456"
    assert len(calls) == 2
    assert "--no-input" in calls[0]
    assert "--no-input" in calls[1]


def test_load_config_only_fetches_missing_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only fetch values that are not provided by env."""
    config_path = tmp_path / "config.json"
    calls: list[list[str]] = []

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        **kwargs: Any,
    ) -> _FakeCompletedProcess:
        calls.append(cmd)
        field_index = cmd.index("--field") + 1
        field = cmd[field_index]
        if field == "api_key":
            return _FakeCompletedProcess("api-key-789\n")
        return _FakeCompletedProcess("", returncode=1)

    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/ops")
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(config_module, "load_dotenv", lambda: None)
    monkeypatch.setenv("ACUITY_CONFIG", str(config_path))
    monkeypatch.setenv("ACUITY_USER_ID", "env-user")
    monkeypatch.delenv("ACUITY_API_KEY", raising=False)

    config = load_config(no_input=True)

    assert config.user_id == "env-user"
    assert config.api_key == "api-key-789"
    assert len(calls) == 1
    assert "--field" in calls[0]

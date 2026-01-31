"""Tests for config command key validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from acuity_cli.commands import config_cmd
from acuity_cli.config import Config
from acuity_cli.errors import EXIT_USAGE_ERROR


def _test_config() -> Config:
    return Config(
        user_id="user-123",
        api_key="x" * 12,
        output="json",
        quiet=True,
    )


def test_config_set_rejects_unknown_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(config_cmd, "CONFIG_FILE", config_path)

    result = config_cmd._handle_set("unknown_key", "value", _test_config())

    assert result == EXIT_USAGE_ERROR
    assert not config_path.exists()

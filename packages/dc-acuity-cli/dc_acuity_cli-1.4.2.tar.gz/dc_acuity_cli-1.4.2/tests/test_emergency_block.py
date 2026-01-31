"""Tests for emergency block command."""

from __future__ import annotations

import argparse
from typing import Any

import pytest

from acuity_cli.commands import availability
from acuity_cli.config import Config


class FakeClient:
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    def create_block(self, **kwargs: Any) -> dict[str, int]:
        self.payload = kwargs
        return {"id": 123}


def test_block_command_sends_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    args = argparse.Namespace(
        availability_command="block",
        start="2025-01-15T09:00:00",
        end="2025-01-15T17:00:00",
        calendar_id=456,
        output_file=None,
    )

    fake = FakeClient()
    monkeypatch.setattr(availability, "AcuityClient", lambda _config: fake)

    availability.run(args, config=_test_config())

    assert fake.payload is not None
    assert fake.payload["start"] == "2025-01-15T09:00:00"
    assert fake.payload["end"] == "2025-01-15T17:00:00"
    assert fake.payload["calendar_id"] == 456


def _test_config() -> Config:
    return Config(
        user_id="user-123",
        api_key="x" * 12,
        output="json",
        quiet=True,
        no_input=True,
        no_color=True,
    )

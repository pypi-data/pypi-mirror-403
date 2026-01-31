"""Tests for client history command."""

from __future__ import annotations

import argparse
from typing import Any

import pytest

from acuity_cli.commands import clients
from acuity_cli.config import Config


class FakeClient:
    def __init__(self) -> None:
        self.email = None

    def list_appointments(self, **kwargs: Any) -> list[dict[str, object]]:
        self.email = kwargs.get("email")
        return [{"id": 1, "type": "Consult", "datetime": "2025-01-01T10:00:00"}]


def test_client_history_uses_email(monkeypatch: pytest.MonkeyPatch) -> None:
    args = argparse.Namespace(
        clients_command="history",
        email="jane@example.com",
        output_file=None,
    )

    fake = FakeClient()
    monkeypatch.setattr(clients, "AcuityClient", lambda _config: fake)

    clients.run(args, config=_test_config())

    assert fake.email == "jane@example.com"


def _test_config() -> Config:
    return Config(
        user_id="user-123",
        api_key="x" * 12,
        output="json",
        quiet=True,
        no_input=True,
        no_color=True,
    )

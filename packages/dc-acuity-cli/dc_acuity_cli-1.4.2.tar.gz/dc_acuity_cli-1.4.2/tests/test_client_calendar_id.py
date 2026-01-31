"""Tests for calendar_id handling in AcuityClient."""

from __future__ import annotations

from typing import Any

import pytest

from acuity_cli.client import AcuityClient
from acuity_cli.config import Config


def _test_config() -> Config:
    return Config(
        user_id="user-123",
        api_key="x" * 12,
        output="json",
    )


def test_calendar_id_zero_is_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AcuityClient(_test_config())
    captured: dict[str, Any] = {}

    def fake_request(
        _method: str,
        _endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> list[dict]:
        captured["params"] = params
        captured["json_data"] = json_data
        return []

    monkeypatch.setattr(client, "_request", fake_request)

    client.get_available_dates(appointment_type_id=1, month="2026-01", calendar_id=0)

    assert captured["params"]["calendarID"] == 0

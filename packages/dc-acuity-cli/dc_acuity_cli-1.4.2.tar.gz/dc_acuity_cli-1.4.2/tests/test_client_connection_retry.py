"""Tests for connection retry behavior in AcuityClient."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from acuity_cli.client import AcuityClient
from acuity_cli.config import Config


class _FakeResponse:
    def __init__(
        self,
        status_code: int,
        text: str = "",
        json_data: Any = None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self._json_data = json_data
        self.headers: dict[str, str] = {}

    def json(self) -> Any:
        return self._json_data


def _test_config() -> Config:
    return Config(
        user_id="user-123",
        api_key="x" * 12,
        output="json",
    )


def test_request_retries_connection_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AcuityClient(_test_config())
    calls = 0

    def fake_request(*_args: Any, **_kwargs: Any) -> _FakeResponse:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise requests.exceptions.ConnectionError("boom")
        return _FakeResponse(200, text="{}", json_data={})

    monkeypatch.setattr(client.session, "request", fake_request)
    monkeypatch.setattr("acuity_cli.client.time.sleep", lambda _t: None)

    assert client._request("GET", "/appointment-types") == {}
    assert calls == 3

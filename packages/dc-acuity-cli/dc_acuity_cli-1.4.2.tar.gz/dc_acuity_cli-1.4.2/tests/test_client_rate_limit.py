"""Tests for rate limit handling in AcuityClient."""

from __future__ import annotations

from typing import Any

import pytest

from acuity_cli.client import AcuityAPIError, AcuityClient
from acuity_cli.config import Config


class _FakeResponse:
    def __init__(
        self,
        status_code: int,
        text: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def json(self) -> Any:
        return {}


def _test_config() -> Config:
    return Config(
        user_id="user-123",
        api_key="x" * 12,
        output="json",
    )


def test_request_rate_limit_exhaustion_raises_rate_limited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AcuityClient(_test_config())

    def fake_request(*_args: Any, **_kwargs: Any) -> _FakeResponse:
        return _FakeResponse(429, text="", headers={"Retry-After": "1"})

    monkeypatch.setattr(client.session, "request", fake_request)
    monkeypatch.setattr("acuity_cli.client.time.sleep", lambda _t: None)

    with pytest.raises(AcuityAPIError) as exc:
        client._request("GET", "/appointment-types")

    assert exc.value.code == "RATE_LIMITED"
    assert "Rate limit exceeded" in exc.value.message

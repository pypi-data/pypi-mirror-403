"""Tests for JSON parsing safeguards in AcuityClient."""

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
        json_data: Any = None,
        json_error: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self._json_data = json_data
        self._json_error = json_error
        self.headers: dict[str, str] = {}

    def json(self) -> Any:
        if self._json_error:
            raise self._json_error
        return self._json_data


def _test_config() -> Config:
    return Config(
        user_id="user-123",
        api_key="x" * 12,
        output="json",
    )


def test_request_handles_invalid_json_error_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AcuityClient(_test_config())

    def fake_request(*_args: Any, **_kwargs: Any) -> _FakeResponse:
        return _FakeResponse(
            400,
            text="<html>bad</html>",
            json_error=ValueError("bad json"),
        )

    monkeypatch.setattr(client.session, "request", fake_request)

    with pytest.raises(AcuityAPIError) as exc:
        client._request("GET", "/appointment-types")

    assert exc.value.code == "API_ERROR"
    assert exc.value.message == "Error 400"
    assert exc.value.details.get("raw") == "<html>bad</html>"


def test_request_handles_invalid_json_success_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AcuityClient(_test_config())

    def fake_request(*_args: Any, **_kwargs: Any) -> _FakeResponse:
        return _FakeResponse(
            200,
            text="<html>ok</html>",
            json_error=ValueError("bad json"),
        )

    monkeypatch.setattr(client.session, "request", fake_request)

    with pytest.raises(AcuityAPIError) as exc:
        client._request("GET", "/appointment-types")

    assert exc.value.code == "API_ERROR"
    assert exc.value.message == "Invalid JSON response from API"
    assert exc.value.details.get("raw") == "<html>ok</html>"

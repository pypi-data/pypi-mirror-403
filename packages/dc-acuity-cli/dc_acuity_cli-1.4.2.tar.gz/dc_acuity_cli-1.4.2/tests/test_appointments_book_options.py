"""Tests for appointments book options."""

from __future__ import annotations

import argparse
from typing import Any

import pytest

from acuity_cli.commands import appointments
from acuity_cli.config import Config
from acuity_cli.errors import EXIT_USAGE_ERROR


class FakeClient:
    def __init__(self) -> None:
        self.kwargs: dict[str, Any] | None = None

    def create_appointment(self, **kwargs: Any) -> dict[str, int]:
        self.kwargs = kwargs
        return {"id": 1}


def _test_config() -> Config:
    return Config(
        user_id="user-123",
        api_key="x" * 12,
        output="json",
        quiet=True,
        no_input=True,
        no_color=True,
    )


def _base_args() -> argparse.Namespace:
    return argparse.Namespace(
        appointments_command="book",
        appointment_type_id=123,
        datetime_str="2026-01-21T10:00:00",
        first_name="Jeff",
        last_name="Show",
        email="jeff@example.com",
        calendar_id=None,
        phone=None,
        notes=None,
        output_file=None,
    )


def test_book_passes_labels_and_no_email(monkeypatch: pytest.MonkeyPatch) -> None:
    args = _base_args()
    args.label_ids = [1]
    args.no_email = True

    fake = FakeClient()
    monkeypatch.setattr(appointments, "AcuityClient", lambda _config: fake)
    monkeypatch.setattr(appointments, "print_output", lambda *_, **__: None)

    result = appointments.run(args, config=_test_config())

    assert result == 0
    assert fake.kwargs is not None
    assert fake.kwargs["label_ids"] == [1]
    assert fake.kwargs["no_email"] is True


def test_book_rejects_multiple_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    args = _base_args()
    args.label_ids = [1, 2]
    args.no_email = False

    fake = FakeClient()
    monkeypatch.setattr(appointments, "AcuityClient", lambda _config: fake)
    monkeypatch.setattr(appointments, "print_output", lambda *_, **__: None)

    result = appointments.run(args, config=_test_config())

    assert result == EXIT_USAGE_ERROR
    assert fake.kwargs is None

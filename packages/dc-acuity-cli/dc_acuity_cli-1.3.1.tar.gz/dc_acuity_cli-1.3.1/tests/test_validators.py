"""Tests for input validators."""

from __future__ import annotations

import pytest

from acuity_cli import validators


def test_validate_datetime_accepts_iso() -> None:
    """Accept ISO-8601 datetimes."""
    validators.validate_datetime("2025-01-15T14:00:00")


def test_validate_datetime_rejects_invalid() -> None:
    """Reject non-ISO datetimes."""
    with pytest.raises(ValueError):
        validators.validate_datetime("2025-01-15 14:00")


def test_validate_date_accepts_ymd() -> None:
    """Accept YYYY-MM-DD dates."""
    validators.validate_date("2025-02-01")


def test_validate_date_rejects_invalid() -> None:
    """Reject invalid dates."""
    with pytest.raises(ValueError):
        validators.validate_date("2025/02/01")


def test_validate_month_accepts_ym() -> None:
    """Accept YYYY-MM months."""
    validators.validate_month("2025-02")


def test_validate_month_rejects_invalid() -> None:
    """Reject invalid months."""
    with pytest.raises(ValueError):
        validators.validate_month("2025-2")

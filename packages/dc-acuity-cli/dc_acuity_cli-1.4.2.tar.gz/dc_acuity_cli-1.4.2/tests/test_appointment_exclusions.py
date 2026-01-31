"""Tests for appointment exclusion filtering."""

from __future__ import annotations

from acuity_cli.filters import filter_appointments


def test_filter_appointments_excludes_by_title_and_name() -> None:
    """Exclude appointments when keyword matches title or client name."""
    appointments = [
        {"id": 1, "type": "EDITING TIME", "firstName": "Jordan", "lastName": "K"},
        {"id": 2, "type": "Talk Show Studio", "firstName": "Editing", "lastName": ""},
        {"id": 3, "type": "Talk Show Studio", "firstName": "Alice", "lastName": "Ng"},
    ]

    filtered = filter_appointments(appointments, ["editing"])

    assert [appt["id"] for appt in filtered] == [3]


def test_filter_appointments_allows_empty_exclusions() -> None:
    """Return all appointments when exclusions are empty."""
    appointments = [
        {"id": 1, "type": "EDITING TIME"},
        {"id": 2, "type": "Talk Show Studio"},
    ]

    filtered = filter_appointments(appointments, [])

    assert filtered == appointments

"""Filtering helpers for CLI output."""

from __future__ import annotations

from collections.abc import Iterable


def filter_appointments(
    appointments: list[dict],
    exclude_keywords: Iterable[str],
) -> list[dict]:
    """Filter appointments by exclusion keywords.

    Args:
        appointments: Appointment records from the API.
        exclude_keywords: Case-insensitive keyword list to exclude.

    Returns:
        Filtered list of appointments.

    """
    normalized_keywords = _normalize_keywords(exclude_keywords)
    if not normalized_keywords:
        return appointments

    filtered: list[dict] = []
    for appointment in appointments:
        if not _matches_exclusion(appointment, normalized_keywords):
            filtered.append(appointment)
    return filtered


def _normalize_keywords(keywords: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for keyword in keywords:
        if not isinstance(keyword, str):
            continue
        cleaned = keyword.strip().lower()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _matches_exclusion(appointment: dict, keywords: list[str]) -> bool:
    searchable = _appointment_search_text(appointment)
    for keyword in keywords:
        if keyword in searchable:
            return True
    return False


def _appointment_search_text(appointment: dict) -> str:
    parts: list[str] = []
    for key in ("type", "title", "name", "firstName", "lastName"):
        value = appointment.get(key, "")
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    return " ".join(parts).lower()

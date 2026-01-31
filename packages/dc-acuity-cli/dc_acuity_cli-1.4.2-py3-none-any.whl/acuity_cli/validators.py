"""Input validation utilities for the Acuity CLI.

Provides local validation of datetime formats before making API calls.
"""

from __future__ import annotations

import re
from datetime import datetime

# ISO-8601 datetime pattern: YYYY-MM-DDTHH:MM:SS (with optional timezone)
DATETIME_PATTERN = re.compile(
    r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"
    r"T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:Z|[+-]\d{2}:\d{2})?$"
)

# Date pattern: YYYY-MM-DD
DATE_PATTERN = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")

# Month pattern: YYYY-MM
MONTH_PATTERN = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")


def validate_datetime(value: str) -> str:
    """Validate ISO-8601 datetime format (YYYY-MM-DDTHH:MM:SS[Z|±HH:MM]).

    Args:
        value: The datetime string to validate

    Returns:
        The validated datetime string

    Raises:
        ValueError: If the format is invalid

    """
    if not value:
        raise ValueError("Datetime value is required")

    if not DATETIME_PATTERN.match(value):
        raise ValueError(
            f"Invalid datetime format: '{value}'. "
            "Expected ISO-8601 format: YYYY-MM-DDTHH:MM:SS[Z|±HH:MM] "
            "(e.g., 2026-01-15T14:00:00)"
        )

    # Verify it's a valid date (e.g., not 2026-02-30)
    try:
        # Strip timezone for strptime validation
        if value.endswith("Z"):
            base_value = value[:-1]
        elif "+" in value:
            base_value = value.split("+")[0]
        elif value.count("-") > 2:
            # Handle negative timezone offset like -05:00
            parts = value.rsplit("-", 1)
            if ":" in parts[-1]:
                base_value = parts[0]
            else:
                base_value = value
        else:
            base_value = value
        datetime.strptime(base_value, "%Y-%m-%dT%H:%M:%S")
    except ValueError as e:
        raise ValueError(f"Invalid datetime: '{value}'. {e}") from e

    return value


def validate_date(value: str) -> str:
    """Validate date format (YYYY-MM-DD).

    Args:
        value: The date string to validate

    Returns:
        The validated date string

    Raises:
        ValueError: If the format is invalid

    """
    if not value:
        raise ValueError("Date value is required")

    if not DATE_PATTERN.match(value):
        raise ValueError(
            f"Invalid date format: '{value}'. "
            "Expected format: YYYY-MM-DD (e.g., 2026-01-15)"
        )

    # Verify it's a valid date (e.g., not 2026-02-30)
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date: '{value}'. {e}") from e

    return value


def validate_month(value: str) -> str:
    """Validate month format (YYYY-MM).

    Args:
        value: The month string to validate

    Returns:
        The validated month string

    Raises:
        ValueError: If the format is invalid

    """
    if not value:
        raise ValueError("Month value is required")

    if not MONTH_PATTERN.match(value):
        raise ValueError(
            f"Invalid month format: '{value}'. Expected format: YYYY-MM (e.g., 2026-01)"
        )

    # Verify it's a valid month
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError as e:
        raise ValueError(f"Invalid month: '{value}'. {e}") from e

    return value

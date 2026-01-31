"""Error codes and exit code mappings for the Acuity CLI."""

from __future__ import annotations

EXIT_SUCCESS = 0
EXIT_GENERIC = 1
EXIT_USAGE_ERROR = 2
EXIT_AUTH_ERROR = 3
EXIT_NOT_FOUND = 4
EXIT_CONFLICT = 5


def exit_code_for_error(code: str) -> int:
    """Map API error codes to standardized exit codes.

    Args:
        code: Error code string

    Returns:
        Exit code integer

    """
    mapping = {
        "AUTH_FAILED": EXIT_AUTH_ERROR,
        "NOT_FOUND": EXIT_NOT_FOUND,
        "CLIENT_EXISTS": EXIT_CONFLICT,
        "SLOT_UNAVAILABLE": EXIT_CONFLICT,
        "CONFLICT": EXIT_CONFLICT,
        "CONFIG_ERROR": EXIT_USAGE_ERROR,
        "VALIDATION_ERROR": EXIT_USAGE_ERROR,
    }
    return mapping.get(code, EXIT_GENERIC)

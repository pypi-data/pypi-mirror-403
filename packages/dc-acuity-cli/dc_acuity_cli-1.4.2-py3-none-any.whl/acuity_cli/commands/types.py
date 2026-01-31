"""Appointment types commands.

Usage:
    acuity types list
"""

from __future__ import annotations

import argparse

from ..client import AcuityAPIError, AcuityClient
from ..config import Config
from ..errors import EXIT_USAGE_ERROR, exit_code_for_error
from ..formatters import print_output


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add types subcommand parser.

    Args:
        subparsers: Parent subparsers action

    """
    parser = subparsers.add_parser(
        "types",
        help="Manage appointment types (CALL FIRST for booking workflow)",
        description=(
            "List and view appointment types. "
            "Must be called first to get appointmentTypeID."
        ),
    )

    types_sub = parser.add_subparsers(dest="types_command", required=True)

    # types list
    list_parser = types_sub.add_parser(
        "list",
        help="List all appointment types",
        description=(
            "List all available appointment types with their IDs, names, and durations."
        ),
    )
    list_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of results to return",
    )
    list_parser.add_argument(
        "--offset",
        type=int,
        help="Number of results to skip (for pagination)",
    )


def run(args: argparse.Namespace, config: Config) -> int:
    """Run types command.

    Args:
        args: Parsed arguments
        config: CLI configuration

    Returns:
        Exit code (0 success, non-zero error)

    """
    try:
        client = AcuityClient(config)

        if args.types_command == "list":
            data = client.list_appointment_types(
                limit=args.limit,
                offset=args.offset,
            )
            print_output(
                data,
                config.output,
                success=True,
                export_path=args.output_file,
                quiet=config.quiet,
            )
            return 0

        return 2  # Invalid command

    except AcuityAPIError as e:
        print_output(
            e.details,
            config.output,
            success=False,
            error_code=e.code,
            error_message=e.message,
            quiet=config.quiet,
        )
        return exit_code_for_error(e.code)

    except ValueError as e:
        print_output(
            None,
            config.output,
            success=False,
            error_code="CONFIG_ERROR",
            error_message=str(e),
            quiet=config.quiet,
        )
        return EXIT_USAGE_ERROR

"""Calendars commands.

Usage:
    acuity calendars list
"""

from __future__ import annotations

import argparse

from ..client import AcuityAPIError, AcuityClient
from ..config import Config
from ..errors import EXIT_USAGE_ERROR, exit_code_for_error
from ..formatters import print_output


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add calendars subcommand parser.

    Args:
        subparsers: Parent subparsers action

    """
    parser = subparsers.add_parser(
        "calendars",
        help="Manage calendars (team members/producers)",
        description="List calendars to get calendarID for specific producers.",
    )

    calendars_sub = parser.add_subparsers(dest="calendars_command", required=True)

    # calendars list
    list_parser = calendars_sub.add_parser(
        "list",
        help="List all calendars",
        description="List all available calendars with their IDs and names.",
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
    """Run calendars command.

    Args:
        args: Parsed arguments
        config: CLI configuration

    Returns:
        Exit code (0 success, non-zero error)

    """
    try:
        client = AcuityClient(config)

        if args.calendars_command == "list":
            data = client.list_calendars(
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

        return EXIT_USAGE_ERROR

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
        return 2

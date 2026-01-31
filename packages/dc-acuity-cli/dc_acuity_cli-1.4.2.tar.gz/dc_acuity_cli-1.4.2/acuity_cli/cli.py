"""Main CLI entry point for Acuity Scheduling.

Usage:
    acuity [global flags] <command> [subcommand] [flags]

Commands:
    types         List appointment types (CALL FIRST)
    calendars     List calendars (team members)
    availability  Check scheduling availability
    clients       Manage clients
    appointments  Manage appointments

Examples:
    # Step 1: Get appointment types (ALWAYS FIRST)
    acuity types list

    # Step 2: Check availability
    acuity availability dates --type 12345 --month 2025-01
    acuity availability times --type 12345 --date 2025-01-15

    # Step 3: Validate slot
    acuity availability check --type 12345 --datetime "2025-01-15T14:00:00"

    # Step 4: Book appointment
    acuity appointments book --type 12345 --datetime "2025-01-15T14:00:00"
        --first-name Jane --last-name Doe --email jane@example.com

"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from . import __version__
from .commands import (
    appointments,
    availability,
    calendars,
    clients,
    config_cmd,
    types,
    update,
)
from .config import load_config

WORKFLOW_HELP = """
BOOKING WORKFLOW (4 required steps):

  1. acuity types list                    # Get appointmentTypeID (MUST BE FIRST)
  2. acuity availability dates --type ID  # Find open dates
     acuity availability times --type ID  # Find open times on date
  3. acuity availability check --type ID  # Validate slot still open
  4. acuity appointments book --type ID   # Create appointment

Always start with 'types list' - other commands need the appointmentTypeID.
"""


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser.

    Returns:
        Configured ArgumentParser

    """
    parser = argparse.ArgumentParser(
        prog="acuity",
        description=(
            "Acuity Scheduling CLI - Manage appointments, clients, and availability."
        ),
        epilog=WORKFLOW_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global flags
    parser.add_argument(
        "--version",
        action="version",
        version=f"acuity-cli {__version__}",
    )

    parser.add_argument(
        "-o",
        "--output",
        "--format",
        dest="output",
        type=str,
        choices=["json", "text", "markdown", "csv"],
        default=None,
        help="Output format (default: json)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Shortcut for --format json",
    )

    parser.add_argument(
        "--plain",
        action="store_true",
        help="Shortcut for --format text",
    )

    parser.add_argument(
        "--output-file",
        dest="output_file",
        metavar="FILE",
        help="Write output to file instead of stdout ('-' for stdout)",
    )

    parser.add_argument(
        "--user-id",
        type=str,
        dest="user_id",
        help="Acuity user ID (or set ACUITY_USER_ID)",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        dest="api_key",
        help="Acuity API key (or set ACUITY_API_KEY)",
    )

    parser.add_argument(
        "--config",
        type=str,
        dest="config_path",
        help="Path to config file (or set ACUITY_CONFIG)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress non-essential output",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    parser.add_argument(
        "--no-input",
        action="store_true",
        dest="no_input",
        help="Disable prompts; fail unless --force is provided",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        dest="no_color",
        help="Disable colored output",
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="Update the CLI to the latest available version",
    )
    parser.add_argument(
        "--pipx",
        action="store_true",
        help="Use pipx when running --update or the update command",
    )
    parser.add_argument(
        "--venv",
        type=str,
        metavar="PATH",
        help="Use a virtualenv when running --update or the update command",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", required=False)

    # Add command parsers
    types.add_parser(subparsers)
    calendars.add_parser(subparsers)
    availability.add_parser(subparsers)
    clients.add_parser(subparsers)
    appointments.add_parser(subparsers)
    config_cmd.add_parser(subparsers)
    update.add_parser(subparsers)

    return parser


def _resolve_output_format(args: argparse.Namespace) -> str | None:
    """Resolve output format from flags."""
    selected = []
    if args.output:
        selected.append(args.output)
    if args.json:
        selected.append("json")
    if args.plain:
        selected.append("text")

    unique = {value for value in selected if value}
    if len(unique) > 1:
        raise ValueError("Multiple output formats specified; choose one format flag.")

    return next(iter(unique), None)


def _setup_logging(args: argparse.Namespace) -> None:
    """Configure logging based on verbosity flags."""
    level = logging.WARNING
    if args.quiet:
        level = logging.ERROR
    if args.verbose:
        level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main(argv: list[str] | None = None) -> int:
    """Run the CLI with the given arguments.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 success, non-zero error)

    """
    parser = create_parser()
    args = parser.parse_args(argv)

    _setup_logging(args)

    # Honor NO_COLOR environment variable (https://no-color.org)
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        args.no_color = True

    try:
        resolved_output = _resolve_output_format(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if args.update or args.command == "update":
        return update.run(
            args,
            output_format=resolved_output or "json",
            quiet=args.quiet,
        )

    if not args.command:
        parser.print_help()
        return 0

    # Load configuration
    try:
        config = load_config(
            user_id=args.user_id,
            api_key=args.api_key,
            output=resolved_output,
            config_path=args.config_path,
            quiet=args.quiet,
            no_color=args.no_color,
            no_input=args.no_input,
        )
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        return 2

    # Route to appropriate command handler
    command_handlers = {
        "types": types.run,
        "calendars": calendars.run,
        "availability": availability.run,
        "clients": clients.run,
        "appointments": appointments.run,
        "config": config_cmd.run,
    }

    handler = command_handlers.get(args.command)
    if handler:
        return handler(args, config)

    # Should not reach here due to required=True
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

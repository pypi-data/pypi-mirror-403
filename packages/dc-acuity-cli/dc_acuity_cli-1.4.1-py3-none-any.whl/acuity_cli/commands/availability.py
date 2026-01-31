"""Availability commands.

Usage:
    acuity availability dates --type ID --month 2025-01
    acuity availability times --type ID --date 2025-01-15
    acuity availability check --type ID --datetime "2025-01-15T14:00:00"

"""

from __future__ import annotations

import argparse
from datetime import datetime

from ..client import AcuityAPIError, AcuityClient
from ..config import Config
from ..errors import EXIT_CONFLICT, EXIT_USAGE_ERROR, exit_code_for_error
from ..formatters import print_output
from ..validators import validate_date, validate_datetime, validate_month


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add availability subcommand parser.

    Args:
        subparsers: Parent subparsers action

    """
    parser = subparsers.add_parser(
        "availability",
        help="Check scheduling availability",
        description="Check available dates, times, and validate slots before booking.",
    )

    avail_sub = parser.add_subparsers(dest="availability_command", required=True)

    # availability dates
    dates_parser = avail_sub.add_parser(
        "dates",
        help="Get available dates in a month",
        description="Get dates with availability for a specific month.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Find available dates in February 2025 for appointment type 12345\n"
            "  acuity availability dates --type 12345 --month 2025-02\n"
            "\n"
            "  # Current month (if no --month specified)\n"
            "  acuity availability dates --type 12345\n"
            "\n"
            "  # For specific calendar/provider\n"
            "  acuity availability dates --type 12345 --month 2025-02 --calendar 5678"
        ),
    )
    dates_parser.add_argument(
        "--type",
        type=int,
        required=True,
        dest="appointment_type_id",
        help="Appointment type ID (required)",
    )
    dates_parser.add_argument(
        "--month",
        type=str,
        default=None,
        help="Month in YYYY-MM format (default: current month)",
    )
    dates_parser.add_argument(
        "--calendar",
        type=int,
        dest="calendar_id",
        help="Filter by calendar ID",
    )

    # availability times
    times_parser = avail_sub.add_parser(
        "times",
        help="Get available time slots for a date",
        description="Get available time slots for a specific date.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Get all available times on Jan 15, 2025\n"
            "  acuity availability times --type 12345 --date 2025-01-15\n"
            "\n"
            "  # For specific calendar/provider\n"
            "  acuity availability times --type 12345 --date 2025-01-15 \\\n"
            "    --calendar 5678\n"
            "\n"
            "  # Use with -o for machine-readable JSON\n"
            "  acuity availability times --type 12345 --date 2025-01-15 -o json"
        ),
    )
    times_parser.add_argument(
        "--type",
        type=int,
        required=True,
        dest="appointment_type_id",
        help="Appointment type ID (required)",
    )
    times_parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Date in YYYY-MM-DD format (required)",
    )
    times_parser.add_argument(
        "--calendar",
        type=int,
        dest="calendar_id",
        help="Filter by calendar ID",
    )

    # availability check
    check_parser = avail_sub.add_parser(
        "check",
        help="Validate slot before booking (required step)",
        description="Final validation that a time slot is still available.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    check_parser.add_argument(
        "--type",
        type=int,
        required=True,
        dest="appointment_type_id",
        help="Appointment type ID (required)",
    )
    check_parser.add_argument(
        "--datetime",
        type=str,
        required=True,
        dest="datetime_str",
        help="ISO-8601 datetime (e.g., 2025-01-15T14:00:00)",
    )
    check_parser.add_argument(
        "--calendar",
        type=int,
        dest="calendar_id",
        help="Filter by calendar ID",
    )

    # availability block
    block_parser = avail_sub.add_parser(
        "block",
        help="Block off a time range",
        description="Emergency block off a time range on a calendar.",
    )
    block_parser.add_argument(
        "--start",
        type=str,
        required=True,
        help="Start datetime (ISO-8601)",
    )
    block_parser.add_argument(
        "--end",
        type=str,
        required=True,
        help="End datetime (ISO-8601)",
    )
    block_parser.add_argument(
        "--calendar",
        type=int,
        dest="calendar_id",
        help="Target calendar ID",
    )


def run(args: argparse.Namespace, config: Config) -> int:
    """Run availability command.

    Args:
        args: Parsed arguments
        config: CLI configuration

    Returns:
        Exit code (0 success, non-zero error)

    """
    try:
        client = AcuityClient(config)

        if args.availability_command == "dates":
            month = args.month or datetime.now().strftime("%Y-%m")
            validate_month(month)
            data = client.get_available_dates(
                args.appointment_type_id,
                month,
                args.calendar_id,
            )
            print_output(
                data,
                config.output,
                success=True,
                export_path=args.output_file,
                quiet=config.quiet,
            )
            return 0

        elif args.availability_command == "times":
            validate_date(args.date)
            data = client.get_available_times(
                args.appointment_type_id,
                args.date,
                args.calendar_id,
            )
            print_output(
                data,
                config.output,
                success=True,
                export_path=args.output_file,
                quiet=config.quiet,
            )
            return 0

        elif args.availability_command == "check":
            # Validate datetime format before API call
            validate_datetime(args.datetime_str)

            check_result = client.check_time_slot(
                args.appointment_type_id,
                args.datetime_str,
                args.calendar_id,
            )
            print_output(
                check_result,
                config.output,
                success=True,
                export_path=args.output_file,
                quiet=config.quiet,
            )
            # Return conflict exit code if slot is not valid
            return 0 if check_result.get("valid") else EXIT_CONFLICT

        elif args.availability_command == "block":
            validate_datetime(args.start)
            validate_datetime(args.end)
            result = client.create_block(
                start=args.start,
                end=args.end,
                calendar_id=args.calendar_id,
            )
            print_output(
                result,
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
        return EXIT_USAGE_ERROR

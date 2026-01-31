"""Appointments commands.

Usage:
    acuity appointments list --min-date 2025-01-01 --max-date 2025-01-31
    acuity appointments get 12345
    acuity appointments book --type ID --datetime "2025-01-15T14:00:00" ...
    acuity appointments reschedule 12345 --datetime "2025-01-20T10:00:00"
    acuity appointments cancel 12345 --force

"""

from __future__ import annotations

import argparse
import sys

from ..client import AcuityAPIError, AcuityClient
from ..config import Config
from ..errors import EXIT_USAGE_ERROR, exit_code_for_error
from ..filters import filter_appointments
from ..formatters import is_tty, print_output
from ..validators import validate_date, validate_datetime


def _confirm_action(prompt: str) -> bool:
    """Prompt user for confirmation on destructive actions.

    Args:
        prompt: The confirmation message to display

    Returns:
        True if user confirms, False otherwise

    """
    try:
        response = input(f"{prompt} [y/N]: ")
        return response.lower() in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print(file=sys.stderr)
        return False


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add appointments subcommand parser.

    Args:
        subparsers: Parent subparsers action

    """
    parser = subparsers.add_parser(
        "appointments",
        help="Manage appointments",
        description="List, create, reschedule, and cancel appointments.",
    )

    appt_sub = parser.add_subparsers(dest="appointments_command", required=True)

    # appointments list
    list_parser = appt_sub.add_parser(
        "list",
        help="List appointments",
        description="List appointments with optional filters.",
    )
    list_parser.add_argument(
        "--min-date",
        type=str,
        dest="min_date",
        help="Start date filter (YYYY-MM-DD)",
    )
    list_parser.add_argument(
        "--max-date",
        type=str,
        dest="max_date",
        help="End date filter (YYYY-MM-DD)",
    )
    list_parser.add_argument(
        "--first-name",
        type=str,
        dest="first_name",
        help="Filter by client first name",
    )
    list_parser.add_argument(
        "--last-name",
        type=str,
        dest="last_name",
        help="Filter by client last name",
    )
    list_parser.add_argument(
        "--email",
        type=str,
        help="Filter by client email",
    )
    list_parser.add_argument(
        "--export",
        type=str,
        dest="output_file",
        metavar="FILE",
        help="Save output to file instead of printing (e.g., --export report.csv)",
    )
    list_parser.add_argument(
        "--include-excluded",
        action="store_true",
        help="Include appointments matching exclusion keywords",
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

    # appointments get
    get_parser = appt_sub.add_parser(
        "get",
        help="Get appointment details",
        description="Get full details of a specific appointment.",
    )
    get_parser.add_argument(
        "appointment_id",
        type=int,
        help="Appointment ID",
    )

    # appointments book
    book_parser = appt_sub.add_parser(
        "book",
        help="Create new appointment",
        description="Book a new appointment. Run 'availability check' first!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Book a 30-minute appointment on Jan 15, 2025 at 2 PM\n"
            "  acuity appointments book \\\n"
            "    --type 12345 \\\n"
            "    --datetime 2025-01-15T14:00:00 \\\n"
            "    --first-name John \\\n"
            "    --last-name Doe \\\n"
            "    --email john.doe@example.com\n"
            "\n"
            "  # Book with phone and notes\n"
            "  acuity appointments book \\\n"
            "    --type 12345 --datetime 2025-01-15T14:00:00 \\\n"
            "    --first-name Jane --last-name Smith \\\n"
            "    --email jane@example.com --phone 555-1234 \\\n"
            "    --notes 'First time client, bring ID'"
        ),
    )
    book_parser.add_argument(
        "--type",
        type=int,
        required=True,
        dest="appointment_type_id",
        help="Appointment type ID (required)",
    )
    book_parser.add_argument(
        "--datetime",
        type=str,
        required=True,
        dest="datetime_str",
        help="ISO-8601 datetime (e.g., 2025-01-15T14:00:00)",
    )
    book_parser.add_argument(
        "--first-name",
        type=str,
        required=True,
        dest="first_name",
        help="Client first name (required)",
    )
    book_parser.add_argument(
        "--last-name",
        type=str,
        required=True,
        dest="last_name",
        help="Client last name (required)",
    )
    book_parser.add_argument(
        "--email",
        type=str,
        required=True,
        help="Client email (required)",
    )
    book_parser.add_argument(
        "--calendar",
        type=int,
        dest="calendar_id",
        help="Target calendar ID",
    )
    book_parser.add_argument(
        "--phone",
        type=str,
        help="Client phone number",
    )
    book_parser.add_argument(
        "--notes",
        type=str,
        help="Appointment notes",
    )
    book_parser.add_argument(
        "--label",
        type=int,
        action="append",
        dest="label_ids",
        help="Apply a label ID (Acuity accepts a single label per appointment)",
    )
    book_parser.add_argument(
        "--no-email",
        action="store_true",
        dest="no_email",
        help="Suppress confirmation email/SMS (sends noEmail=true)",
    )

    # appointments reschedule
    reschedule_parser = appt_sub.add_parser(
        "reschedule",
        help="Reschedule appointment",
        description="Move an appointment to a new date/time.",
    )
    reschedule_parser.add_argument(
        "appointment_id",
        type=int,
        help="Appointment ID to reschedule",
    )
    reschedule_parser.add_argument(
        "--datetime",
        type=str,
        required=True,
        dest="datetime_str",
        help="New ISO-8601 datetime",
    )
    reschedule_parser.add_argument(
        "--calendar",
        type=int,
        dest="calendar_id",
        help="New calendar ID (auto-finds if omitted)",
    )
    reschedule_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )
    reschedule_parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Show what would happen without making changes",
    )

    # appointments cancel
    cancel_parser = appt_sub.add_parser(
        "cancel",
        help="Cancel appointment",
        description="Cancel an existing appointment.",
    )
    cancel_parser.add_argument(
        "appointment_id",
        type=int,
        help="Appointment ID to cancel",
    )
    cancel_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )
    cancel_parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Show what would happen without making changes",
    )


def run(args: argparse.Namespace, config: Config) -> int:
    """Run appointments command.

    Args:
        args: Parsed arguments
        config: CLI configuration

    Returns:
        Exit code (0 success, non-zero error)

    """
    try:
        client = AcuityClient(config)

        if args.appointments_command == "list":
            # Validate date formats if provided
            if args.min_date:
                validate_date(args.min_date)
            if args.max_date:
                validate_date(args.max_date)
            data = client.list_appointments(
                min_date=args.min_date,
                max_date=args.max_date,
                first_name=args.first_name,
                last_name=args.last_name,
                email=args.email,
                limit=args.limit,
                offset=args.offset,
            )
            if not args.include_excluded:
                data = filter_appointments(
                    data,
                    config.appointment_exclude_keywords,
                )
            print_output(
                data,
                config.output,
                success=True,
                export_path=args.output_file,
                quiet=config.quiet,
            )
            return 0

        elif args.appointments_command == "get":
            appt = client.get_appointment(args.appointment_id)
            print_output(
                appt,
                config.output,
                success=True,
                export_path=args.output_file,
                quiet=config.quiet,
            )
            return 0

        elif args.appointments_command == "book":
            # Validate datetime format before API call
            validate_datetime(args.datetime_str)
            label_ids = args.label_ids or []
            if len(label_ids) > 1:
                print_output(
                    None,
                    config.output,
                    success=False,
                    error_code="VALIDATION_ERROR",
                    error_message="Only one label is allowed per appointment.",
                    quiet=config.quiet,
                )
                return EXIT_USAGE_ERROR
            booked = client.create_appointment(
                appointment_type_id=args.appointment_type_id,
                datetime_str=args.datetime_str,
                first_name=args.first_name,
                last_name=args.last_name,
                email=args.email,
                calendar_id=args.calendar_id,
                phone=args.phone,
                notes=args.notes,
                label_ids=label_ids or None,
                no_email=args.no_email,
            )
            print_output(
                booked,
                config.output,
                success=True,
                export_path=args.output_file,
                quiet=config.quiet,
            )
            return 0

        elif args.appointments_command == "reschedule":
            return _handle_reschedule(args, config, client)

        elif args.appointments_command == "cancel":
            return _handle_cancel(args, config, client)

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


def _handle_reschedule(
    args: argparse.Namespace,
    config: Config,
    client: AcuityClient,
) -> int:
    """Handle the reschedule subcommand with confirmation.

    Args:
        args: Parsed arguments
        config: CLI configuration
        client: API client

    Returns:
        Exit code

    """
    # Validate datetime format before API call
    validate_datetime(args.datetime_str)

    # Dry run mode
    if args.dry_run:
        print_output(
            {
                "dry_run": True,
                "action": "reschedule",
                "appointment_id": args.appointment_id,
                "new_datetime": args.datetime_str,
                "new_calendar_id": args.calendar_id,
            },
            config.output,
            success=True,
            export_path=args.output_file,
            quiet=config.quiet,
        )
        return 0

    # Confirmation required unless --force
    if not args.force:
        if config.no_input or not is_tty():
            print(
                "Confirmation required; re-run with --force to proceed.",
                file=sys.stderr,
            )
            return EXIT_USAGE_ERROR

        if not _confirm_action(
            f"Reschedule appointment {args.appointment_id} to {args.datetime_str}?"
        ):
            print("Cancelled.", file=sys.stderr)
            return 0

    data = client.reschedule_appointment(
        appointment_id=args.appointment_id,
        datetime_str=args.datetime_str,
        calendar_id=args.calendar_id,
    )
    print_output(
        data,
        config.output,
        success=True,
        export_path=args.output_file,
        quiet=config.quiet,
    )
    return 0


def _handle_cancel(
    args: argparse.Namespace,
    config: Config,
    client: AcuityClient,
) -> int:
    """Handle the cancel subcommand with confirmation.

    Args:
        args: Parsed arguments
        config: CLI configuration
        client: API client

    Returns:
        Exit code

    """
    # Dry run mode
    if args.dry_run:
        print_output(
            {
                "dry_run": True,
                "action": "cancel",
                "appointment_id": args.appointment_id,
            },
            config.output,
            success=True,
            export_path=args.output_file,
            quiet=config.quiet,
        )
        return 0

    # Confirmation required unless --force
    if not args.force:
        if config.no_input or not is_tty():
            print(
                "Confirmation required; re-run with --force to proceed.",
                file=sys.stderr,
            )
            return EXIT_USAGE_ERROR

        if not _confirm_action(f"Cancel appointment {args.appointment_id}?"):
            print("Cancelled.", file=sys.stderr)
            return 0

    data = client.cancel_appointment(args.appointment_id)
    print_output(
        data,
        config.output,
        success=True,
        export_path=args.output_file,
        quiet=config.quiet,
    )
    return 0

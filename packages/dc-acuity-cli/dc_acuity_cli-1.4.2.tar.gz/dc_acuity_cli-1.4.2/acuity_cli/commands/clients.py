"""Clients commands.

Usage:
    acuity clients list --search "john"
    acuity clients create --first-name John --last-name Doe --email john@example.com

"""

from __future__ import annotations

import argparse

from ..client import AcuityAPIError, AcuityClient
from ..config import Config
from ..errors import EXIT_USAGE_ERROR, exit_code_for_error
from ..formatters import print_output


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add clients subcommand parser.

    Args:
        subparsers: Parent subparsers action

    """
    parser = subparsers.add_parser(
        "clients",
        help="Manage clients",
        description="Search and create client profiles.",
    )

    clients_sub = parser.add_subparsers(dest="clients_command", required=True)

    # clients list
    list_parser = clients_sub.add_parser(
        "list",
        help="Search clients",
        description="Search clients by name, email, or phone (partial match).",
    )
    list_parser.add_argument(
        "--search",
        type=str,
        required=True,
        help="Search query (matches name, email, or phone)",
    )
    list_parser.add_argument(
        "--export",
        type=str,
        dest="output_file",
        metavar="FILE",
        help="Save output to file instead of printing (e.g., --export clients.csv)",
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

    # clients create
    create_parser = clients_sub.add_parser(
        "create",
        help="Create new client",
        description="Create a new client profile.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Create a basic client profile\n"
            "  acuity clients create \\\n"
            "    --first-name Jane \\\n"
            "    --last-name Smith \\\n"
            "    --email jane.smith@example.com\n"
            "\n"
            "  # Create with full contact info\n"
            "  acuity clients create \\\n"
            "    --first-name John --last-name Doe \\\n"
            "    --email john.doe@example.com --phone 555-0123 \\\n"
            "    --notes 'Referred by Sarah, allergic to latex'\n"
            "\n"
            "  # Output as JSON for scripting\n"
            "  acuity clients create --first-name Bob --last-name Jones \\\n"
            "    --email bob@example.com -o json"
        ),
    )
    create_parser.add_argument(
        "--first-name",
        type=str,
        required=True,
        dest="first_name",
        help="Client first name (required)",
    )
    create_parser.add_argument(
        "--last-name",
        type=str,
        required=True,
        dest="last_name",
        help="Client last name (required)",
    )
    create_parser.add_argument(
        "--email",
        type=str,
        required=True,
        help="Client email address (required)",
    )
    create_parser.add_argument(
        "--phone",
        type=str,
        help="Client phone number",
    )
    create_parser.add_argument(
        "--notes",
        type=str,
        help="Internal notes",
    )

    # clients history
    history_parser = clients_sub.add_parser(
        "history",
        help="Show client appointment history",
        description="List appointments for a client by email.",
    )
    history_parser.add_argument(
        "--email",
        type=str,
        required=True,
        help="Client email address (required)",
    )


def run(args: argparse.Namespace, config: Config) -> int:
    """Run clients command.

    Args:
        args: Parsed arguments
        config: CLI configuration

    Returns:
        Exit code (0 success, non-zero error)

    """
    try:
        client = AcuityClient(config)

        if args.clients_command == "list":
            data = client.search_clients(
                args.search,
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

        elif args.clients_command == "create":
            created = client.create_client(
                first_name=args.first_name,
                last_name=args.last_name,
                email=args.email,
                phone=args.phone,
                notes=args.notes,
            )
            print_output(
                created,
                config.output,
                success=True,
                export_path=args.output_file,
                quiet=config.quiet,
            )
            return 0

        elif args.clients_command == "history":
            data = client.list_appointments(email=args.email)
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
        return EXIT_USAGE_ERROR

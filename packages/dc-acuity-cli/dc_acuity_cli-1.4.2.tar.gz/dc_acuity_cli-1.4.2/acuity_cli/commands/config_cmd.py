"""Configuration management commands.

Usage:
    acuity config show           # Display current config (API key masked)
    acuity config set KEY VALUE  # Set a config value
    acuity config path           # Print config file path
    acuity config validate       # Check if config is valid

"""

from __future__ import annotations

import argparse
import json
import sys

from ..config import CONFIG_FILE, Config, load_config, load_config_file
from ..errors import EXIT_SUCCESS, EXIT_USAGE_ERROR
from ..formatters import print_output


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add config subcommand parser.

    Args:
        subparsers: Parent subparsers action

    """
    parser = subparsers.add_parser(
        "config",
        help="Manage CLI configuration",
        description="View, set, and validate CLI configuration.",
    )

    config_sub = parser.add_subparsers(dest="config_command", required=True)

    # config show
    config_sub.add_parser(
        "show",
        help="Display current configuration",
        description="Display current configuration with API key masked.",
    )

    # config set
    set_parser = config_sub.add_parser(
        "set",
        help="Set a configuration value",
        description="Set a configuration value in the config file.",
    )
    set_parser.add_argument(
        "key",
        type=str,
        help="Configuration key to set",
    )
    set_parser.add_argument(
        "value",
        type=str,
        help="Value to set",
    )

    # config path
    config_sub.add_parser(
        "path",
        help="Print config file path",
        description="Print the path to the configuration file.",
    )

    # config validate
    config_sub.add_parser(
        "validate",
        help="Validate configuration",
        description="Check if the current configuration is valid.",
    )


def _mask_api_key(api_key: str) -> str:
    """Mask API key for display.

    Args:
        api_key: The API key to mask

    Returns:
        Masked API key showing only first 4 and last 4 characters

    """
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


def run(args: argparse.Namespace, config: Config) -> int:
    """Run config command.

    Args:
        args: Parsed arguments
        config: CLI configuration

    Returns:
        Exit code (0 success, non-zero error)

    """
    if args.config_command == "show":
        return _handle_show(config)

    elif args.config_command == "set":
        return _handle_set(args.key, args.value, config)

    elif args.config_command == "path":
        return _handle_path(config)

    elif args.config_command == "validate":
        return _handle_validate(config)

    return EXIT_USAGE_ERROR


def _handle_show(config: Config) -> int:
    """Display current configuration with masked API key.

    Args:
        config: CLI configuration

    Returns:
        Exit code

    """
    config_data = {
        "user_id": config.user_id,
        "api_key": _mask_api_key(config.api_key),
        "default_timezone": config.default_timezone,
        "default_calendar": config.default_calendar,
        "output": config.output,
        "appointment_exclude_keywords": config.appointment_exclude_keywords,
    }

    print_output(
        config_data,
        config.output,
        success=True,
        quiet=config.quiet,
    )
    return EXIT_SUCCESS


def _handle_set(key: str, value: str, config: Config) -> int:
    """Set a configuration value.

    Args:
        key: Configuration key to set
        value: Value to set
        config: CLI configuration

    Returns:
        Exit code

    """
    valid_keys = {
        "user_id",
        "api_key",
        "default_timezone",
        "default_calendar",
        "output",
        "appointment_exclude_keywords",
    }
    if key not in valid_keys:
        print_output(
            None,
            config.output,
            success=False,
            error_code="CONFIG_ERROR",
            error_message=(
                f"Unknown config key: {key}. "
                f"Valid keys: {', '.join(sorted(valid_keys))}"
            ),
            quiet=config.quiet,
        )
        return EXIT_USAGE_ERROR

    # Load existing config
    existing_config = load_config_file()

    # Parse value as JSON if it looks like JSON, otherwise keep as string
    parsed_value: str | int | list[str] | None = value
    if value.lower() == "null":
        parsed_value = None
    elif value.isdigit():
        parsed_value = int(value)
    elif value.startswith("[") or value.startswith("{"):
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            pass

    # Update config
    existing_config[key] = parsed_value

    # Ensure config directory exists
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write config
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, indent=2)
            f.write("\n")
        CONFIG_FILE.chmod(0o600)
    except OSError as e:
        print(f"Error writing config file: {e}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    print_output(
        {"key": key, "value": parsed_value, "path": str(CONFIG_FILE)},
        config.output,
        success=True,
        quiet=config.quiet,
    )
    return EXIT_SUCCESS


def _handle_path(config: Config) -> int:
    """Print config file path.

    Args:
        config: CLI configuration

    Returns:
        Exit code

    """
    print_output(
        {"path": str(CONFIG_FILE), "exists": CONFIG_FILE.exists()},
        config.output,
        success=True,
        quiet=config.quiet,
    )
    return EXIT_SUCCESS


def _handle_validate(config: Config) -> int:
    """Validate current configuration.

    Args:
        config: CLI configuration

    Returns:
        Exit code

    """
    errors: list[str] = []

    # Check required fields
    if not config.user_id:
        errors.append("ACUITY_USER_ID is required")
    if not config.api_key:
        errors.append("ACUITY_API_KEY is required")
    elif len(config.api_key) < 10:
        errors.append("ACUITY_API_KEY appears invalid (too short)")

    if errors:
        print_output(
            {"valid": False, "errors": errors},
            config.output,
            success=False,
            error_code="CONFIG_INVALID",
            error_message="; ".join(errors),
            quiet=config.quiet,
        )
        return EXIT_USAGE_ERROR

    # Attempt to load config to verify it works
    try:
        loaded_config = load_config()
        loaded_config.validate()
    except ValueError as e:
        print_output(
            {"valid": False, "errors": [str(e)]},
            config.output,
            success=False,
            error_code="CONFIG_INVALID",
            error_message=str(e),
            quiet=config.quiet,
        )
        return EXIT_USAGE_ERROR

    print_output(
        {"valid": True, "config_file": str(CONFIG_FILE)},
        config.output,
        success=True,
        quiet=config.quiet,
    )
    return EXIT_SUCCESS

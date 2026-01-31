"""Configuration management for Acuity CLI.

Handles credential loading with precedence:
  flags > env vars > config file (~/.config/acuity/config.json)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

API_BASE_URL = "https://acuityscheduling.com/api/v1"
DEFAULT_TIMEZONE = "America/Chicago"
DEFAULT_OUTPUT = "json"
DEFAULT_APPOINTMENT_EXCLUDE_KEYWORDS = ["editing"]
CONFIG_DIR = Path.home() / ".config" / "acuity"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_OPS_ITEM = "acuity"
DEFAULT_OPS_USER_FIELD = "user_id"
DEFAULT_OPS_KEY_FIELD = "api_key"
DEFAULT_OPS_TIMEOUT_SECONDS = 5


@dataclass
class Config:
    """CLI configuration."""

    user_id: str
    api_key: str
    default_timezone: str = DEFAULT_TIMEZONE
    default_calendar: int | None = None
    output: str = DEFAULT_OUTPUT
    appointment_exclude_keywords: list[str] = field(default_factory=list)
    quiet: bool = False
    no_color: bool = False
    no_input: bool = False

    def validate(self) -> None:
        """Validate required fields."""
        if not self.user_id:
            raise ValueError("ACUITY_USER_ID is required")
        if not self.api_key:
            raise ValueError("ACUITY_API_KEY is required")
        if len(self.api_key) < 10:
            raise ValueError("ACUITY_API_KEY appears invalid (too short)")


def load_config_file(config_path: Path | None = None) -> dict:
    """Load config from ~/.config/acuity/config.json if it exists."""
    resolved_path = config_path or CONFIG_FILE
    if resolved_path.exists():
        try:
            with open(resolved_path) as f:
                return cast(dict[str, Any], json.load(f))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load config file: {e}")
    return {}


def load_config(
    user_id: str | None = None,
    api_key: str | None = None,
    output: str | None = None,
    config_path: str | None = None,
    quiet: bool = False,
    no_color: bool = False,
    no_input: bool = False,
) -> Config:
    """Load configuration with precedence: args > env > config file.

    Args:
        user_id: Override from CLI flag
        api_key: Override from CLI flag
        output: Output format override
        config_path: Config file path override
        quiet: Suppress non-essential output
        no_color: Disable colored output
        no_input: Disable interactive prompts

    Returns:
        Config object with resolved values

    """
    # Load .env file if present
    load_dotenv()

    resolved_config_path = config_path or os.getenv("ACUITY_CONFIG")
    config_file_path = Path(resolved_config_path) if resolved_config_path else None

    # Load config file defaults
    file_config = load_config_file(config_file_path)

    # Resolve with precedence: args > env > file
    resolved_user_id = (
        user_id or os.getenv("ACUITY_USER_ID") or file_config.get("user_id", "")
    )

    resolved_api_key = (
        api_key or os.getenv("ACUITY_API_KEY") or file_config.get("api_key", "")
    )

    resolved_output = (
        output
        or os.getenv("ACUITY_OUTPUT")
        or file_config.get("output", DEFAULT_OUTPUT)
    )

    resolved_timezone = os.getenv("ACUITY_TIMEZONE") or file_config.get(
        "default_timezone", DEFAULT_TIMEZONE
    )

    resolved_calendar = file_config.get("default_calendar")
    resolved_exclusions = _resolve_exclusion_keywords(
        os.getenv("ACUITY_APPOINTMENT_EXCLUDE"),
        file_config.get("appointment_exclude_keywords"),
    )

    ops_user_id = ""
    ops_api_key = ""
    if not resolved_user_id or not resolved_api_key:
        ops_item = os.getenv("ACUITY_OPS_ITEM", DEFAULT_OPS_ITEM)
        ops_vault = os.getenv("ACUITY_OPS_VAULT")
        ops_user_field = os.getenv("ACUITY_OPS_USER_FIELD", DEFAULT_OPS_USER_FIELD)
        ops_key_field = os.getenv("ACUITY_OPS_KEY_FIELD", DEFAULT_OPS_KEY_FIELD)

        if not resolved_user_id:
            ops_user_id = _ops_get_secret(
                ops_item,
                ops_user_field,
                ops_vault,
                no_input,
                quiet,
            )
            if ops_user_id:
                resolved_user_id = ops_user_id

        if not resolved_api_key:
            ops_api_key = _ops_get_secret(
                ops_item,
                ops_key_field,
                ops_vault,
                no_input,
                quiet,
            )
            if ops_api_key:
                resolved_api_key = ops_api_key

        if ops_user_id or ops_api_key:
            _save_ops_credentials(
                config_file_path,
                file_config,
                ops_user_id,
                ops_api_key,
            )

    return Config(
        user_id=resolved_user_id,
        api_key=resolved_api_key,
        default_timezone=resolved_timezone,
        default_calendar=resolved_calendar,
        output=resolved_output,
        appointment_exclude_keywords=resolved_exclusions,
        quiet=quiet,
        no_color=no_color,
        no_input=no_input,
    )


def _ops_get_secret(
    item: str,
    field: str,
    vault: str | None,
    no_input: bool,
    quiet: bool,
) -> str:
    if not item or not field:
        return ""
    if shutil.which("ops") is None:
        return ""

    cmd = ["ops", "get", item, "--field", field, "--plain"]
    if vault:
        cmd.extend(["--vault", vault])
    if quiet:
        cmd.append("--quiet")
    if no_input or not sys.stdin.isatty():
        cmd.append("--no-input")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_OPS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        logger.warning("Timed out retrieving ops secret.")
        return ""

    if result.returncode != 0:
        if result.stderr.strip():
            logger.debug(f"ops command failed: {result.stderr.strip()}")
        return ""
    return result.stdout.strip()


def _save_ops_credentials(
    config_path: Path | None,
    existing_config: dict,
    user_id: str,
    api_key: str,
) -> None:
    target_path = config_path or CONFIG_FILE
    updates: dict[str, Any] = {}

    if user_id and not existing_config.get("user_id"):
        updates["user_id"] = user_id
    if api_key and not existing_config.get("api_key"):
        updates["api_key"] = api_key

    if not updates:
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Set restrictive permissions on config directory
    try:
        target_path.parent.chmod(0o700)
    except OSError as exc:
        logger.warning(f"Failed to set directory permissions: {exc}")

    merged = {**existing_config, **updates}
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
            f.write("\n")

        # Set restrictive permissions on config file (owner read/write only)
        target_path.chmod(0o600)
    except OSError as exc:
        logger.warning(f"Failed to write config file or set permissions: {exc}")


def _resolve_exclusion_keywords(
    env_value: str | None,
    config_value: object | None,
) -> list[str]:
    if env_value is not None:
        return _parse_keyword_list(env_value)
    if config_value is not None:
        return _parse_keyword_list(config_value)
    return DEFAULT_APPOINTMENT_EXCLUDE_KEYWORDS.copy()


def _parse_keyword_list(raw_value: object) -> list[str]:
    if isinstance(raw_value, list):
        values = raw_value
    elif isinstance(raw_value, str):
        values = [value.strip() for value in raw_value.split(",")]
    else:
        return []

    keywords: list[str] = []
    for value in values:
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                keywords.append(cleaned)
    return keywords

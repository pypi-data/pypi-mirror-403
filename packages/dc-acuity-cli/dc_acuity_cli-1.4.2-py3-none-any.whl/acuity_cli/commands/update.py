"""Update the Acuity CLI installation."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from ..errors import EXIT_GENERIC, EXIT_SUCCESS, EXIT_USAGE_ERROR
from ..formatters import print_output


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add update subcommand parser."""
    subparsers.add_parser(
        "update",
        help="Update the CLI using pip",
        description="Update the Acuity CLI to the latest available version.",
    )


def run(
    args: argparse.Namespace,
    *,
    output_format: str,
    quiet: bool,
) -> int:
    """Run update command."""
    if args.pipx and args.venv:
        print_output(
            None,
            output_format,
            success=False,
            error_code="UPDATE_INVALID",
            error_message="Use either --pipx or --venv, not both.",
            quiet=quiet,
        )
        return EXIT_USAGE_ERROR

    if args.pipx:
        command = ["pipx", "install", "--force", "dc-acuity-cli"]
        runner = _run_command
    elif args.venv:
        command = _ensure_venv_command(Path(args.venv))
        runner = _run_command
    else:
        command = [sys.executable, "-m", "pip", "install", "-U", "dc-acuity-cli"]
        runner = _run_pip_command

    try:
        runner(command)
    except (OSError, subprocess.CalledProcessError) as exc:
        if _is_pep668_error(exc):
            _print_pep668_help(output_format, quiet)
            return EXIT_USAGE_ERROR
        print_output(
            {"command": command},
            output_format,
            success=False,
            error_code="UPDATE_FAILED",
            error_message=str(exc),
            quiet=quiet,
        )
        return EXIT_GENERIC

    print_output(
        {"updated": True, "command": command},
        output_format,
        success=True,
        quiet=quiet,
    )
    return EXIT_SUCCESS


def _run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _run_pip_command(command: list[str]) -> None:
    subprocess.run(command, check=True, capture_output=True, text=True)


def _ensure_venv_command(venv_path: Path) -> list[str]:
    if not venv_path.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    python_path = venv_path / "bin" / "python"
    return [str(python_path), "-m", "pip", "install", "-U", "dc-acuity-cli"]


def _is_pep668_error(exc: Exception) -> bool:
    if not isinstance(exc, subprocess.CalledProcessError):
        return False
    stderr = (exc.stderr or "").lower()
    return "externally-managed-environment" in stderr or "pep 668" in stderr


def _print_pep668_help(output_format: str, quiet: bool) -> None:
    print_output(
        {
            "updated": False,
            "error": "externally-managed-environment",
            "help": [
                "Use pipx: brew install pipx && pipx install dc-acuity-cli",
                "Or use a venv: python3 -m venv ~/venvs/acuity && "
                "source ~/venvs/acuity/bin/activate",
                "Then: pip install -U dc-acuity-cli",
            ],
        },
        output_format,
        success=False,
        error_code="EXTERNALLY_MANAGED_ENV",
        error_message="Python environment is externally managed (PEP 668).",
        quiet=quiet,
    )

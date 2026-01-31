"""Tests for help text with examples.

Verifies that key subcommands include practical examples in help output.
"""

import subprocess
import sys


def run_help_command(args: list[str]) -> str:
    """Run acuity CLI with --help and return output.

    Args:
        args: Command arguments (e.g., ['appointments', 'book', '--help'])

    Returns:
        The help text output

    Raises:
        subprocess.CalledProcessError: If command fails

    """
    cmd = [sys.executable, "-m", "acuity_cli"] + args + ["--help"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout + result.stderr


class TestHelpExamples:
    """Test help text includes practical examples."""

    def test_appointments_book_help_includes_examples(self) -> None:
        """appointments book --help should include usage examples."""
        help_text = run_help_command(["appointments", "book"])

        # Should include example invocation
        assert "examples:" in help_text.lower() or "example:" in help_text.lower(), (
            "appointments book help missing 'examples' or 'example' section"
        )

        # Should show real parameter values
        assert "2025" in help_text, (
            "appointments book help should show date example (e.g., 2025-01-15)"
        )
        assert "@" in help_text, "appointments book help should show email example"

    def test_availability_dates_help_includes_examples(self) -> None:
        """availability dates --help should include usage examples."""
        help_text = run_help_command(["availability", "dates"])

        assert "examples:" in help_text.lower() or "example:" in help_text.lower(), (
            "availability dates help missing 'examples' or 'example' section"
        )
        assert "2025" in help_text, (
            "availability dates help should show month example (e.g., 2025-02)"
        )

    def test_availability_times_help_includes_examples(self) -> None:
        """availability times --help should include usage examples."""
        help_text = run_help_command(["availability", "times"])

        assert "examples:" in help_text.lower() or "example:" in help_text.lower(), (
            "availability times help missing 'examples' or 'example' section"
        )
        assert "2025" in help_text, (
            "availability times help should show date example (e.g., 2025-02-15)"
        )

    def test_clients_create_help_includes_examples(self) -> None:
        """clients create --help should include usage examples."""
        help_text = run_help_command(["clients", "create"])

        assert "examples:" in help_text.lower() or "example:" in help_text.lower(), (
            "clients create help missing 'examples' or 'example' section"
        )
        assert "@" in help_text, "clients create help should show email example"

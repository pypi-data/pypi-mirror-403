"""Output formatters for Acuity CLI.

Supports JSON, text, markdown, and CSV output formats.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from datetime import datetime, timezone
from typing import Any


def format_output(
    data: Any,
    output_format: str = "json",
    success: bool = True,
    error_code: str | None = None,
    error_message: str | None = None,
) -> str:
    """Format data for output.

    Args:
        data: Data to format (list, dict, etc.)
        output_format: Output format (json, text, markdown)
        success: Whether the operation succeeded
        error_code: Error code if failed
        error_message: Error message if failed

    Returns:
        Formatted string output

    """
    if output_format == "json":
        return format_json(data, success, error_code, error_message)
    elif output_format == "markdown":
        return format_markdown(data, success, error_code, error_message)
    elif output_format == "csv":
        return format_csv(data, success, error_code, error_message)
    else:
        return format_text(data, success, error_code, error_message)


def format_json(
    data: Any,
    success: bool = True,
    error_code: str | None = None,
    error_message: str | None = None,
) -> str:
    """Format data as JSON.

    Args:
        data: Data to format
        success: Whether the operation succeeded
        error_code: Error code if failed
        error_message: Error message if failed

    Returns:
        JSON string

    """
    if success:
        output = {
            "success": True,
            "data": data,
            "meta": {
                "count": len(data) if isinstance(data, list) else 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
    else:
        output = {
            "success": False,
            "error": {
                "code": error_code or "ERROR",
                "message": error_message or "An error occurred",
            },
        }
        if data:
            output["error"]["details"] = data

    return json.dumps(output, indent=2, default=str)


def format_text(
    data: Any,
    success: bool = True,
    error_code: str | None = None,
    error_message: str | None = None,
) -> str:
    """Format data as plain text.

    Args:
        data: Data to format
        success: Whether the operation succeeded
        error_code: Error code if failed
        error_message: Error message if failed

    Returns:
        Plain text string

    """
    if not success:
        return f"Error [{error_code}]: {error_message}"

    if isinstance(data, list):
        return format_list_as_text(data)
    elif isinstance(data, dict):
        return format_dict_as_text(data)
    else:
        return str(data)


def format_list_as_text(items: list) -> str:
    """Format a list of items as text table.

    Args:
        items: List of dictionaries to format

    Returns:
        Text table string

    """
    if not items:
        return "No results found."

    # Get column headers from first item
    if not isinstance(items[0], dict):
        return "\n".join(str(item) for item in items)

    # Determine columns and widths
    columns = list(items[0].keys())[:6]  # Limit to 6 columns
    widths = {}

    for col in columns:
        max_width = len(col)
        for item in items[:20]:  # Sample first 20 for width
            val = str(item.get(col, ""))[:40]  # Truncate long values
            max_width = max(max_width, len(val))
        widths[col] = min(max_width, 40)

    # Build header
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    separator = "-+-".join("-" * widths[col] for col in columns)

    # Build rows
    rows = []
    for item in items:
        row_vals = []
        for col in columns:
            val = str(item.get(col, ""))[: widths[col]]
            row_vals.append(val.ljust(widths[col]))
        rows.append(" | ".join(row_vals))

    return f"{header}\n{separator}\n" + "\n".join(rows)


def format_dict_as_text(item: dict) -> str:
    """Format a single dict as key-value text.

    Args:
        item: Dictionary to format

    Returns:
        Key-value text string

    """
    lines = []
    max_key_len = max(len(str(k)) for k in item.keys()) if item else 0

    for key, value in item.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str)
        lines.append(f"{str(key).ljust(max_key_len)}: {value}")

    return "\n".join(lines)


def format_markdown(
    data: Any,
    success: bool = True,
    error_code: str | None = None,
    error_message: str | None = None,
) -> str:
    """Format data as markdown.

    Args:
        data: Data to format
        success: Whether the operation succeeded
        error_code: Error code if failed
        error_message: Error message if failed

    Returns:
        Markdown string

    """
    if not success:
        return f"## Error\n\n**Code:** `{error_code}`\n\n**Message:** {error_message}"

    if isinstance(data, list):
        return format_list_as_markdown(data)
    elif isinstance(data, dict):
        return format_dict_as_markdown(data)
    else:
        return str(data)


def format_list_as_markdown(items: list) -> str:
    """Format a list as markdown table.

    Args:
        items: List of dictionaries to format

    Returns:
        Markdown table string

    """
    if not items:
        return "*No results found.*"

    if not isinstance(items[0], dict):
        return "\n".join(f"- {item}" for item in items)

    # Get columns
    columns = list(items[0].keys())[:6]

    # Build header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"

    # Build rows
    rows = []
    for item in items:
        row_vals = []
        for col in columns:
            val = str(item.get(col, ""))
            # Escape pipe characters
            val = val.replace("|", "\\|")
            # Truncate long values
            if len(val) > 50:
                val = val[:47] + "..."
            row_vals.append(val)
        rows.append("| " + " | ".join(row_vals) + " |")

    return f"{header}\n{separator}\n" + "\n".join(rows)


def format_dict_as_markdown(item: dict) -> str:
    """Format a single dict as markdown.

    Args:
        item: Dictionary to format

    Returns:
        Markdown string

    """
    lines = []

    for key, value in item.items():
        if isinstance(value, dict):
            lines.append(f"**{key}:**")
            for k, v in value.items():
                lines.append(f"  - {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"**{key}:** {len(value)} items")
        else:
            lines.append(f"**{key}:** {value}")

    return "\n".join(lines)


def format_csv(
    data: Any,
    success: bool = True,
    error_code: str | None = None,
    error_message: str | None = None,
    headers: list[str] | None = None,
) -> str:
    """Format data as CSV.

    Args:
        data: Data to format (should be a list of dicts for CSV)
        success: Whether the operation succeeded
        error_code: Error code if failed
        error_message: Error message if failed
        headers: Optional list of column headers (auto-detected if not provided)

    Returns:
        CSV string

    """
    if not success:
        output = io.StringIO()
        error_writer = csv.writer(output)
        error_writer.writerow(["error_code", "error_message"])
        error_writer.writerow([error_code, error_message])
        return output.getvalue()

    # Handle non-list data
    if not isinstance(data, list):
        data = [data] if data else []

    if not data:
        return ""

    # Auto-detect headers from first item
    if not headers and isinstance(data[0], dict):
        headers = list(data[0].keys())

    if not headers:
        return ""

    output = io.StringIO()
    data_writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
    data_writer.writeheader()

    for row in data:
        if isinstance(row, dict):
            clean_row = {k: _flatten_value(v) for k, v in row.items() if k in headers}
            data_writer.writerow(clean_row)

    return output.getvalue()


def is_tty() -> bool:
    """Check if stdout is a TTY (interactive terminal).

    Returns:
        True if running in interactive terminal, False otherwise.

    """
    return sys.stdout.isatty()


def _flatten_value(value: Any) -> str:
    """Flatten a value for CSV output.

    Handles nested dicts and lists by converting to strings.

    Args:
        value: Value to flatten

    Returns:
        String representation suitable for CSV

    """
    if value is None:
        return ""
    elif isinstance(value, dict):
        # Flatten dict to key=value pairs
        return "; ".join(f"{k}={v}" for k, v in value.items())
    elif isinstance(value, list):
        # Join list items with semicolons
        return "; ".join(str(item) for item in value)
    else:
        return str(value)


def print_output(
    data: Any,
    output_format: str = "json",
    success: bool = True,
    error_code: str | None = None,
    error_message: str | None = None,
    file: Any = None,
    export_path: str | None = None,
    quiet: bool = False,
) -> None:
    """Print formatted output to stdout, stderr, or file.

    Args:
        data: Data to format and print
        output_format: Output format (json, text, markdown, csv)
        success: Whether the operation succeeded
        error_code: Error code if failed
        error_message: Error message if failed
        file: Output file object (defaults to stdout for success, stderr for errors)
        export_path: Path to save output to file instead of printing
        quiet: Suppress non-essential output

    """
    output = format_output(data, output_format, success, error_code, error_message)

    # Handle output file path
    if export_path == "-":
        export_path = None

    if export_path:
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(output)
                if not output.endswith("\n"):
                    f.write("\n")
        except OSError as exc:
            print(f"Error writing to {export_path}: {exc}", file=sys.stderr)
            return
        if not quiet:
            # Print confirmation to stderr so it doesn't interfere with piping
            print(f"Output written to {export_path}", file=sys.stderr)
        return

    # Default: success goes to stdout, errors to stderr
    if file is None:
        file = sys.stdout if success else sys.stderr

    # Ensure output ends with newline
    if output and not output.endswith("\n"):
        output += "\n"

    # Use print instead of direct write to handle encoding properly
    print(output, file=file, end="")

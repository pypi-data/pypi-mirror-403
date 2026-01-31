"""Acuity Scheduling CLI.

A command-line interface for managing Acuity Scheduling appointments,
clients, and availability. Designed for AI agent integration.

Usage:
    acuity types list
    acuity availability dates --type ID --month 2025-01
    acuity appointments book --type ID --datetime "2025-01-15T14:00:00" ...
"""

from importlib import metadata

try:
    __version__ = metadata.version("dc-acuity-cli")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"

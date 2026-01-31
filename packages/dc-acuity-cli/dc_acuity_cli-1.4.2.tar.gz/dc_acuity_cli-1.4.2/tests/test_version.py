"""Tests for CLI version reporting."""

from __future__ import annotations

from importlib import metadata

import pytest

from acuity_cli import __version__


def test_version_matches_package_metadata() -> None:
    try:
        package_version = metadata.version("dc-acuity-cli")
    except metadata.PackageNotFoundError:
        pytest.skip("Package metadata not available in this environment")

    assert __version__ == package_version

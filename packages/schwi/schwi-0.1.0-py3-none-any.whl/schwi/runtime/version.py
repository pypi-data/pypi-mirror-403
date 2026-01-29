"""Application version lookup."""

from __future__ import annotations

from importlib import metadata


def get_app_version(package_name: str = 'schwi') -> str:
    """Return the installed package version."""
    return metadata.version(package_name)

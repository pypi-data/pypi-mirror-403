"""Version command."""

from __future__ import annotations

from ..cli import _get_package_name  # noqa: TID252
from .base import Command


def _version_command(_args: list[str]) -> bool:
    """Show version information."""
    package_name = _get_package_name()

    try:
        package_module = __import__(package_name, fromlist=["__version__"])
        version = getattr(package_module, "__version__", "unknown")
        print(f"{package_name} version {version}")
        return True
    except ImportError:
        print(f"{package_name} version unknown")
        return False


version_command = Command(_version_command, "Show version information")


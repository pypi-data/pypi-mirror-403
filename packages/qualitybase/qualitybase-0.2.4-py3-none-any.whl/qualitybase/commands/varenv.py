"""Environment variables command."""

from __future__ import annotations

import os

from .base import Command


def _varenv_command(args: list[str]) -> bool:
    """Show or manage environment variables.

    Usage:
      varenv --show              Show all environment variables
      varenv --show KEY          Show specific environment variable
      varenv --show KEY1 KEY2    Show multiple environment variables
    """
    show_mode = False
    show_keys: list[str] = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--show":
            show_mode = True
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                show_keys.append(args[i])
                i += 1
        else:
            i += 1

    if not show_mode and not show_keys:
        print("Usage: varenv --show [KEY1 KEY2 ...]")
        print("  --show              Show all environment variables")
        print("  --show KEY          Show specific environment variable")
        print("  --show KEY1 KEY2    Show multiple environment variables")
        return False

    if show_mode:
        if not show_keys:
            for key, env_value in sorted(os.environ.items()):
                print(f"{key}={env_value}")
        else:
            for key in show_keys:
                value: str | None = os.environ.get(key)
                if value is not None:
                    print(f"{key}={value}")
                else:
                    print(f"{key}=<not set>")

    return True


varenv_command = Command(_varenv_command, "Show environment variables")

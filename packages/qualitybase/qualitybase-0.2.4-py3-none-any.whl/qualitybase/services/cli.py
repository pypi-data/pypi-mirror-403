#!/usr/bin/env python3
"""CLI service for running library CLI commands."""

from __future__ import annotations

import sys
from pathlib import Path

from qualitybase.services import utils

print_error = utils.print_error
print_info = utils.print_info


def _find_package_name(project_root: Path) -> str | None:
    """Find the package name in src/ directory.

    Args:
        project_root: Root directory of the project

    Returns:
        Package name if found, None otherwise
    """
    src_path = project_root / "src"
    if not src_path.exists():
        return None

    # Find first directory in src/ that contains __init__.py
    for item in src_path.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            init_file = item / "__init__.py"
            if init_file.exists():
                return item.name

    return None


def main() -> int:
    """Main entry point."""
    project_root = Path(__file__).resolve().parent.parent
    src_path = project_root / "src"

    if src_path.exists():
        sys.path.insert(0, str(src_path))

    # Find package name dynamically
    package_name = _find_package_name(project_root)
    if not package_name:
        print_error("No package found in src/ directory")
        print_info("Make sure your library package is in src/<package_name>/")
        return 1

    try:
        # Dynamic import based on detected package name
        import importlib
        cli_module = importlib.import_module(f"{package_name}.cli")  # nosec B307
        cli_main = cli_module.main

        args = sys.argv[1:] if len(sys.argv) > 1 else []
        exit_code = cli_main(args)
        return int(exit_code)
    except ImportError as exc:
        print_error(f"Failed to import library CLI from {package_name}.cli: {exc}")
        print_info("Make sure the library has a cli.py module with a main() function.")
        return 1
    except AttributeError as exc:
        print_error(f"CLI module {package_name}.cli does not have a main() function: {exc}")
        return 1
    except Exception as exc:
        print_error(f"Error running CLI: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


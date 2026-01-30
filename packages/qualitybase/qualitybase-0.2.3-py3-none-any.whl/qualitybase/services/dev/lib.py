# pylint: disable=R0801  # Duplicate code acceptable for common imports
"""Library update tasks."""

from __future__ import annotations

import sys
from pathlib import Path

from qualitybase.services import utils

# Import from utils
# pylint: disable=R0801  # Duplicate code acceptable for common imports
PROJECT_ROOT = utils.PROJECT_ROOT
PIP = utils.PIP
print_info = utils.print_info
print_success = utils.print_success
print_error = utils.print_error
print_warning = utils.print_warning
venv_exists = utils.venv_exists
run_command = utils.run_command


def task_update_lib() -> bool:
    """Install or update a library from local directory in editable mode.

    Usage:
      ./service.py dev update-lib <path_to_library>
      ./service.py dev update-lib path/to/lib

    The library will be installed in editable mode (-e) so changes are
    immediately available without reinstalling.

    Args:
        Path to the library directory (must contain setup.py or pyproject.toml)
    """
    if not venv_exists():
        print_error("Virtual environment not found. Run 'python dev.py venv' first.")
        return False

    # Get path from command line arguments
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    if not args:
        print_error("No library path provided.")
        print_info("Usage: python dev.py update-lib <path_to_library>")
        print_info("       ./service.py dev update-lib path/to/lib")
        return False

    target_dir = Path(args[0]).resolve()

    # Handle relative paths
    if not target_dir.is_absolute():
        target_dir = (PROJECT_ROOT / args[0]).resolve()

    if not target_dir.exists():
        print_error(f"Library directory not found at {target_dir}")
        print_info("Provide a valid path: python dev.py update-lib /path/to/library")
        return False

    if not target_dir.is_dir():
        print_error(f"Path is not a directory: {target_dir}")
        return False

    # Check if it looks like a Python package
    has_setup = (target_dir / "setup.py").exists()
    has_pyproject = (target_dir / "pyproject.toml").exists()

    if not (has_setup or has_pyproject):
        print_warning(
            f"Warning: No setup.py or pyproject.toml found in {target_dir}. "
            "This might not be a Python package."
        )

    lib_name = target_dir.name
    print_info(f"Installing {lib_name} into the virtual environment...")
    print_info(f"Library path: {target_dir}")

    success, _ = run_command([str(PIP), "install", "-e", str(target_dir)], check=False)
    if success:
        print_success(f"{lib_name} installed/updated successfully.")
        return True

    print_error(f"Failed to install/update {lib_name}.")
    return False


# pylint: disable=R0801  # Duplicate code acceptable for common imports
"""Environment management tasks."""

from __future__ import annotations

import platform
import shutil
from pathlib import Path  # noqa: TC003

from qualitybase.services import utils

# Import from utils
# pylint: disable=R0801  # Duplicate code acceptable for common imports
PROJECT_ROOT = utils.PROJECT_ROOT
VENV_DIR = utils.VENV_DIR
PIP = utils.PIP
print_info = utils.print_info
print_success = utils.print_success
print_error = utils.print_error
print_warning = utils.print_warning
venv_exists = utils.venv_exists
run_command = utils.run_command


def install_build_dependencies() -> bool:
    """Install build dependencies."""
    success, _ = run_command([str(PIP), "install", "--upgrade", "pip", "setuptools", "wheel", "build"])
    return success


def task_venv() -> bool:
    """Create a virtual environment."""
    if venv_exists():
        print_warning("Virtual environment already exists.")
        return True

    python_cmd = "python3" if platform.system() != "Windows" else "python"
    print_info("Creating virtual environment...")
    success, _ = run_command([python_cmd, "-m", "venv", str(VENV_DIR)], check=False)
    if not success:
        return False

    print_success(f"Virtual environment created at {VENV_DIR}")
    activation = (
        f"{VENV_DIR}\\Scripts\\activate"
        if platform.system() == "Windows"
        else f"source {VENV_DIR}/bin/activate"
    )
    print_info(f"Activate it with: {activation}")
    return True


def task_venv_clean() -> bool:
    """Recreate the virtual environment."""
    if venv_exists():
        print_info("Removing existing virtual environment...")
        shutil.rmtree(VENV_DIR, ignore_errors=True)
        print_success("Virtual environment removed.")
    return task_venv()


def task_install() -> bool:
    """Install the package in production mode."""
    if not venv_exists() and not task_venv():
        return False

    print_info("Installing package (production)...")
    if not install_build_dependencies():
        return False

    success, _ = run_command([str(PIP), "install", "."], check=False)
    if not success:
        return False

    # Install requirements.txt if it exists
    requirements = PROJECT_ROOT / "requirements.txt"
    if requirements.exists():
        print_info("Installing dependencies from requirements.txt...")
        run_command([str(PIP), "install", "-r", str(requirements)], check=False)

    print_success("Installation complete.")
    return True


def _install_requirements_file(req_path: Path) -> None:
    """Install dependencies from a requirements file if it exists."""
    if req_path.exists():
        print_info(f"Installing dependencies from {req_path.name}...")
        run_command([str(PIP), "install", "-r", str(req_path)], check=False)


def _install_dev_dependencies_from_file() -> bool:
    """Install development dependencies from requirements-dev.txt or requirements-quality.txt if they exist."""
    requirements_files = [
        "requirements-dev.txt",
        "requirements-quality.txt",
    ]

    installed_any = False

    for req_file in requirements_files:
        req_path = PROJECT_ROOT / req_file
        if req_path.exists():
            print_info(f"Installing development dependencies from {req_file}...")
            success, _ = run_command([str(PIP), "install", "-r", str(req_path)], check=False)
            if success:
                installed_any = True

    return installed_any


def _install_dev_dependencies_fallback() -> None:
    """Install development dependencies using fallback methods."""
    print_info("Installing development dependencies from pyproject.toml...")
    deps = ["lint", "security", "test", "quality"]
    for dep_group in deps:
        success, _ = run_command([str(PIP), "install", "-e", f".[{dep_group}]"], check=False)
        if not success:
            print_warning(f"Failed to install {dep_group} dependencies")

    requirements_files = [
        "requirements-quality.txt",
        "requirements-django.txt",
    ]
    for req_file in requirements_files:
        _install_requirements_file(PROJECT_ROOT / req_file)


def task_install_dev() -> bool:
    """Install the package in editable mode with dev dependencies."""
    if not venv_exists() and not task_venv():
        return False

    print_info("Installing package (development)...")
    if not install_build_dependencies():
        return False

    success, _ = run_command([str(PIP), "install", "-e", "."], check=False)
    if not success:
        return False

    _install_requirements_file(PROJECT_ROOT / "requirements.txt")

    if _install_dev_dependencies_from_file():
        print_success("Development installation complete.")
        return True

    print_warning("Failed to install from requirements-dev.txt/requirements-quality.txt, trying fallback methods...")
    _install_dev_dependencies_fallback()

    print_success("Development installation complete.")
    return True


def load_envfile_from_path(env_file_path: Path, project_root: Path | None = None) -> bool:
    """Load environment variables from a .env file into the current process.

    Args:
        env_file_path: Path to the .env file (can be relative or absolute).
        project_root: Project root directory for resolving relative paths.
                      If None, uses PROJECT_ROOT from utils.

    Returns:
        True if loading was successful, False otherwise.
    """
    import os

    if project_root is None:
        project_root = PROJECT_ROOT

    if not env_file_path.is_absolute():
        env_file_path = (project_root / env_file_path).resolve()

    if not env_file_path.exists():
        return False

    if not env_file_path.is_file():
        return False

    try:
        from dotenv import dotenv_values

        env_vars = dotenv_values(env_file_path)
        loaded_count = 0
        for key, value in env_vars.items():
            if value is not None:
                os.environ[key] = value
                loaded_count += 1
        return loaded_count > 0

    except ImportError:
        return False
    except Exception:
        return False


def _load_envfile_from_path(env_file_path: Path) -> None:
    """Load environment variables from a .env file (internal function).

    Args:
        env_file_path: Path to the .env file (can be relative or absolute).
    """
    load_envfile_from_path(env_file_path)


def task_load_envfile() -> bool:
    """Load environment variables from a .env file.

    Usage:
      ./service.py dev load-envfile <path_to_env_file>
      ./service.py dev load-envfile path/to/.env

    Args:
        Path to the .env file (can be relative or absolute).
    """
    import sys

    # Get path from command line arguments
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    if not args:
        print_error("No .env file path provided.")
        print_info("Usage: ./service.py dev load-envfile <path_to_env_file>")
        print_info("       ./service.py dev load-envfile path/to/.env")
        return False

    env_file_path = Path(args[0])

    if load_envfile_from_path(env_file_path):
        print_success(f"Environment variables loaded from {env_file_path}")
        return True

    print_error(f"Failed to load environment variables from {env_file_path}")
    print_info("Make sure the file exists and is readable.")
    return False


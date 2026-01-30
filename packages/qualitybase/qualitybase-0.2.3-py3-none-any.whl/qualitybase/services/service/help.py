"""Help display functions for service routing."""

from __future__ import annotations

import importlib.util
import platform
from pathlib import Path

from qualitybase.services import utils


def show_help(project_root: Path, usage_prefix: str = "./service.py") -> None:  # noqa: C901
    """Display help for all available services.

    Args:
        project_root: The root directory of the project
        usage_prefix: The prefix to use for usage examples (default: "./service.py")
    """
    print(f"Usage: {usage_prefix} <service> [command] [args...]")
    print("\nServices:")

    # Configure utils before importing services
    try:
        utils.PROJECT_ROOT = project_root

        def _resolve_venv_dir():
            preferred_names = [".venv", "venv"]
            for name in preferred_names:
                candidate = project_root / name
                if candidate.exists():
                    return candidate
            return project_root / preferred_names[0]

        utils.VENV_DIR = _resolve_venv_dir()
        utils.VENV_BIN = utils.VENV_DIR / ("Scripts" if platform.system() == "Windows" else "bin")
        utils.PYTHON = utils.VENV_BIN / ("python.exe" if platform.system() == "Windows" else "python")
        utils.PIP = utils.VENV_BIN / ("pip.exe" if platform.system() == "Windows" else "pip")
        utils_available = True
    except ImportError:
        utils_available = False

    # Import and display help for each service
    # Note: qualitybase is an installed package, so we use direct imports only
    # No path manipulation - everything works via standard Python imports

    # django.py, publish.py, quality.py, and dev.py are modules, but django/, publish/, quality/, and dev/ are packages
    # We need to load the .py module files directly using importlib.util
    if utils_available:
        utils_file = Path(utils.__file__)
        services_config = [
            ("dev", "DEV", "task_help"),
            ("django", "DJANGO", "task_help"),
            ("publish", "PUBLISH", "task_help"),
            ("quality", "QUALITY", "task_help"),
        ]

        for service_name, display_name, method_name in services_config:
            try:
                service_file = utils_file.parent / f"{service_name}.py"
                if service_file.exists():
                    spec = importlib.util.spec_from_file_location(
                        f"qualitybase.services.{service_name}", service_file
                    )
                    if spec is None or spec.loader is None:
                        continue
                    service_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(service_module)

                    if hasattr(service_module, method_name):
                        print(f"\n{display_name}:")
                        method = getattr(service_module, method_name)
                        # All services now use task_help(), call directly
                        method()
            except Exception:
                # Silently ignore errors for individual services
                pass

    print("\n  cli      Library CLI commands")
    print("\nExamples:")
    print(f"  {usage_prefix} quality lint")
    print(f"  {usage_prefix} dev install-dev")
    print(f"  {usage_prefix} django runserver")
    print(f"  {usage_prefix} publish release-full")
    print(f"  {usage_prefix} cli help")


"""Main entry point for service routing."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from qualitybase.services.service.help import show_help
from qualitybase.services.service.run import run_qualitybase_service
from qualitybase.services.utils import ensure_virtualenv

if TYPE_CHECKING:
    from pathlib import Path


def main(project_root: Path, usage_prefix: str = "./service.py") -> int:  # noqa: C901
    """Main entry point for service routing.

    Args:
        project_root: Root directory of the project
        usage_prefix: Prefix to use for usage examples (default: "./service.py")

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Configure utils before ensuring venv
    import qualitybase.services.utils as utils
    utils.PROJECT_ROOT = project_root
    ensure_virtualenv()

    if len(sys.argv) < 2:
        show_help(project_root, usage_prefix=usage_prefix)
        return 1

    service = sys.argv[1].lower()
    command_args = sys.argv[2:]

    qualitybase_services = {"quality", "dev", "django", "publish"}

    if service in qualitybase_services:
        return run_qualitybase_service(service, command_args, project_root)

    if service == "cli":
        src_path = project_root / "src"
        if not src_path.exists():
            print(f"Error: src directory not found at {src_path}")
            return 1

        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        def _find_package_name(project_root: Path) -> str | None:
            src = project_root / "src"
            if not src.exists():
                return None
            for item in src.iterdir():
                if item.is_dir() and not item.name.startswith("_") and (item / "__init__.py").exists():
                    return item.name
            return None

        package_name = _find_package_name(project_root)
        if not package_name:
            print(f"Error: No package found in {src_path}")
            return 1

        try:
            from qualitybase.cli import cli_main as qualitybase_cli_main

            cli_file_path = src_path / package_name / "cli.py"
            if not cli_file_path.exists():
                print(f"Error: cli.py not found at {cli_file_path}")
                return 1

            result = qualitybase_cli_main(cli_file_path, command_args)
            return int(result) if isinstance(result, (int, bool)) else (0 if result else 1)
        except ImportError as exc:
            print(f"Error: Failed to import {package_name}.cli: {exc}")
            return 1
        except AttributeError as exc:
            print(f"Error: {package_name}.cli does not have a main() function: {exc}")
            return 1
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return 130
        except Exception as exc:
            print(f"Error executing CLI: {exc}")
            return 1

    print(f"Error: Unknown service '{service}'")
    print("Available services: quality, dev, django, publish, cli")
    return 1


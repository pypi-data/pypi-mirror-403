"""Service execution functions for qualitybase."""

from __future__ import annotations

import importlib.util
import inspect
import runpy
import sys
from pathlib import Path

from qualitybase.services import utils


def run_qualitybase_service(service_name: str, command_args: list[str], project_root: Path) -> int:  # noqa: C901
    """Run a service from qualitybase.services module.

    Args:
        service_name: Name of the service to run (e.g., "quality", "dev", "django", "publish")
        command_args: List of command arguments to pass to the service
        project_root: Root directory of the project calling the service

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Configure utils with project root before importing services
    utils.PROJECT_ROOT = project_root

    def _resolve_venv_dir():
        preferred_names = [".venv", "venv"]
        for name in preferred_names:
            candidate = project_root / name
            if candidate.exists():
                return candidate
        return project_root / preferred_names[0]

    import platform
    utils.VENV_DIR = _resolve_venv_dir()
    utils.VENV_BIN = utils.VENV_DIR / ("Scripts" if platform.system() == "Windows" else "bin")
    utils.PYTHON = utils.VENV_BIN / ("python.exe" if platform.system() == "Windows" else "python")
    utils.PIP = utils.VENV_BIN / ("pip.exe" if platform.system() == "Windows" else "pip")

    # Update all loaded qualitybase.services.* modules to use the new PROJECT_ROOT
    # This is important because modules may have already been imported and cached
    for module_name in list(sys.modules.keys()):
        if module_name.startswith("qualitybase.services"):
            module = sys.modules[module_name]
            if hasattr(module, "PROJECT_ROOT"):
                module.PROJECT_ROOT = project_root  # type: ignore[attr-defined]
            if hasattr(module, "VENV_BIN"):
                module.VENV_BIN = utils.VENV_BIN  # type: ignore[attr-defined]
            if hasattr(module, "VENV_DIR"):
                module.VENV_DIR = utils.VENV_DIR  # type: ignore[attr-defined]
            if hasattr(module, "PYTHON"):
                module.PYTHON = utils.PYTHON  # type: ignore[attr-defined]
            if hasattr(module, "PIP"):
                module.PIP = utils.PIP  # type: ignore[attr-defined]

    try:
        # Load the service module using importlib
        utils_file = Path(utils.__file__)
        service_file = utils_file.parent / f"{service_name}.py"

        if not service_file.exists():
            print(f"Error: Service '{service_name}' not found in qualitybase")
            return 1

        # Use runpy to execute the service module
        # This ensures the module is executed as __main__ and handles imports correctly
        old_argv = sys.argv[:]
        sys.argv = [f"{service_name}.py"] + command_args

        try:
            # Check if the service has a main() function and its signature
            spec = importlib.util.spec_from_file_location(
                f"qualitybase.services.{service_name}", service_file
            )
            if spec is None or spec.loader is None:
                print(f"Error: Could not load service module '{service_name}'")
                return 1
            service_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(service_module)

            if hasattr(service_module, "main"):
                main_func = service_module.main
                sig = inspect.signature(main_func)

                # Check if main() accepts arguments
                # main() expects arguments (e.g., dev.main(argv)) or takes no arguments (e.g., quality.main())
                result = main_func(command_args) if len(sig.parameters) > 0 else main_func()

                # Convert boolean result to exit code if needed
                if isinstance(result, bool):
                    return 0 if result else 1
                elif isinstance(result, int):
                    return result
                else:
                    return 0
            else:
                # Fallback: use runpy if no main() function
                runpy.run_path(str(service_file), run_name="__main__")
                return 0
        except SystemExit as e:
            # SystemExit is raised by sys.exit(), extract the code
            return e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        finally:
            sys.argv = old_argv

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130
    except Exception as exc:
        print(f"Error executing service '{service_name}': {exc}")
        import traceback
        traceback.print_exc()
        return 1


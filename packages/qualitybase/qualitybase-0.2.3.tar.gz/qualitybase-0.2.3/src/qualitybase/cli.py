#!/usr/bin/env python3
"""CLI service for running library CLI commands."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import TypedDict

    class CommandInfo(TypedDict):
        """Command information structure."""
        func: Callable[[list[str]], bool]
        description: str
else:
    from typing import TypedDict

    class CommandInfo(TypedDict):
        """Command information structure."""
        func: Callable[[list[str]], bool]
        description: str

# Global context for CLI execution
_CLI_CONTEXT: dict[str, Path | None] = {"cli_file_path": None}


def _get_package_name_from_path(cli_file_path: Path, package_name: str | None = None) -> str:
    """Get package name from file path.

    Args:
        cli_file_path: Path to cli.py file
        package_name: Optional explicit package name

    Returns:
        Package name
    """
    if package_name:
        return package_name.split(".")[0]

    try:
        parent_dir = cli_file_path.parent.name
        if parent_dir and parent_dir != "cli.py":
            return parent_dir
        parent_parent = cli_file_path.parent.parent.name
        if parent_parent:
            return parent_parent
    except Exception:
        pass

    return cli_file_path.parent.name if cli_file_path.parent.name else "unknown"


def _discover_from_path(commands_path: Path, package_name: str) -> dict[str, CommandInfo]:  # noqa: C901
    """Discover commands from a specific path.

    Args:
        commands_path: Path to commands directory
        package_name: Package name for importing modules

    Returns:
        Dictionary mapping command names to their functions and descriptions
    """
    result: dict[str, CommandInfo] = {}
    import importlib
    import inspect

    if not commands_path.exists():
        return result

    try:
        base_package = package_name.rsplit(".", 1)[0] if "." in package_name else package_name
        base_module = importlib.import_module(f"{base_package}.commands.base")  # nosec B307
        Command = base_module.Command
    except (ImportError, AttributeError):
        try:
            from qualitybase.commands.base import Command
        except ImportError:
            Command = None

    for py_file in commands_path.glob("*.py"):
        if py_file.stem == "__init__":
            continue

        base_package = package_name.rsplit(".", 1)[0] if "." in package_name else package_name
        module = importlib.import_module(f"{base_package}.commands.{py_file.stem}")  # nosec B307

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if name.endswith("_command") and not name.startswith("_"):
                command_name = name[:-8]

                description = inspect.getdoc(obj) or ""
                if description:
                    description = description.split("\n")[0].strip()

                result[command_name] = {
                    "func": obj,
                    "description": description,
                }

        if Command:
            for name, obj in inspect.getmembers(module):
                if isinstance(obj, Command):
                    if name.startswith("_"):
                        continue
                    if name.endswith("_command"):
                        command_name = name[:-8]
                    elif name.endswith("Command"):
                        command_name = name[:-7].lower()
                    else:
                        command_name = name.lower()

                    description = obj.description or ""
                    if not description:
                        description = inspect.getdoc(obj) or ""
                        if description:
                            description = description.split("\n")[0].strip()

                    result[command_name] = {
                        "func": obj,
                        "description": description,
                    }

    return result


def _discover_from_package(package: str) -> dict[str, CommandInfo]:
    """Discover commands from a package.

    Args:
        package: Package name to discover commands from

    Returns:
        Dictionary mapping command names to their functions and descriptions
    """
    import importlib
    from pathlib import Path

    try:
        commands_module = importlib.import_module(f"{package}.commands")  # nosec B307
        commands_path = Path(commands_module.__file__).parent if commands_module.__file__ else Path()
        package_name = commands_module.__package__ if hasattr(commands_module, "__package__") else package
        return _discover_from_path(commands_path, package_name or package)
    except ImportError:
        return {}


def _discover_from_command(command: str | dict) -> dict[str, CommandInfo]:
    """Discover a single command from configuration.

    Args:
        command: Command name or command configuration dict

    Returns:
        Dictionary mapping command names to their functions and descriptions
    """
    if isinstance(command, str):
        return _discover_from_package(command)
    return {}


def _load_agentia_rules() -> dict[str, str]:
    """Load rules from .agentia/rules/* directory.

    Returns:
        Dictionary containing parsed rules
    """
    from pathlib import Path
    rules: dict[str, str] = {}
    rules_dir = Path(".agentia/rules")

    if not rules_dir.exists():
        return rules

    for rule_file in rules_dir.glob("*.md"):
        try:
            with open(rule_file, encoding="utf-8") as f:
                content = f.read()
                rules[rule_file.stem] = content
        except Exception:
            pass

    return rules


def discover_commands(  # noqa: C901
    cli_file_path: Path,
    package_name: str | None = None,
    _commands_dir: str | Path | None = None,
) -> dict[str, CommandInfo]:
    """Discover commands by scanning commands directory or package.

    Args:
        cli_file_path: Path to cli.py file
        package_name: Package name to discover commands from
        commands_dir: Path to commands directory (if None, uses package's commands)

    Returns:
        Dictionary mapping command names to their functions and descriptions
    """
    result: dict[str, CommandInfo] = {}
    import json
    from pathlib import Path

    _load_agentia_rules()

    package = package_name or _get_package_name_from_path(cli_file_path)

    config_file = Path(".commands.json")
    if not config_file.exists():
        config_file = cli_file_path.parent / ".commands.json"

    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        config_dir = config_file.parent.resolve()

        if "packages" in config:
            for pkg in config["packages"]:
                result.update(_discover_from_package(pkg))
        if "directories" in config:
            for directory in config["directories"]:
                dir_path = config_dir / directory if not Path(directory).is_absolute() else Path(directory)
                result.update(_discover_from_path(dir_path, package))
        if "commands" in config:
            for command in config["commands"]:
                result.update(_discover_from_command(command))

    if not result:
        commands_path = cli_file_path.parent / "commands"
        if commands_path.exists():
            result.update(_discover_from_path(commands_path, package))

    return result


def _discover_commands(cli_file_path: Path | None = None) -> dict[str, CommandInfo]:
    """Discover commands using cli file path.

    Args:
        cli_file_path: Path to cli.py file (if None, tries to detect from caller)

    Returns:
        Dictionary mapping command names to their functions and descriptions
    """
    if cli_file_path is None:
        import inspect
        frame = inspect.currentframe()
        qualitybase_cli_path = Path(__file__).resolve()
        for _ in range(20):
            if not frame:
                break
            frame = frame.f_back
            if frame:
                frame_file = frame.f_globals.get("__file__")
                if frame_file:
                    frame_path = Path(frame_file).resolve()
                    if "cli.py" in frame_file and frame_path != qualitybase_cli_path:
                        cli_file_path = frame_path
                        break
        if cli_file_path is None:
            raise ValueError("Could not detect cli_file_path automatically")

    return discover_commands(cli_file_path)


def _get_package_name(cli_file_path: Path | None = None) -> str:
    """Get package name from cli file path.

    Args:
        cli_file_path: Path to cli.py file (if None, tries to detect from caller)

    Returns:
        Package name
    """
    if cli_file_path is None:
        import inspect
        frame = inspect.currentframe()
        qualitybase_cli_path = Path(__file__).resolve()
        for _ in range(20):
            if not frame:
                break
            frame = frame.f_back
            if frame:
                frame_file = frame.f_globals.get("__file__")
                if frame_file:
                    frame_path = Path(frame_file).resolve()
                    if "cli.py" in frame_file and frame_path != qualitybase_cli_path:
                        cli_file_path = frame_path
                        break
        if cli_file_path is None:
            return "unknown"

    return _get_package_name_from_path(cli_file_path)


def cli_main(cli_file_path: Path, argv: Sequence[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        cli_file_path: Path to cli.py file
        argv: Command arguments (if None, uses sys.argv[1:])

    Returns:
        Exit code
    """
    import os
    from typing import cast

    # Store CLI context for commands to access
    _CLI_CONTEXT["cli_file_path"] = cli_file_path

    envfile_path = os.environ.get("ENVFILE_PATH")
    if envfile_path:
        try:
            from pathlib import Path

            from qualitybase.services.dev.env import load_envfile_from_path

            project_root = Path.cwd()
            load_envfile_from_path(Path(envfile_path), project_root)
        except ImportError:
            pass
        except Exception:
            pass

    args = list(argv if argv is not None else sys.argv[1:])
    commands = discover_commands(cli_file_path)

    if not args:
        package_name = _get_package_name_from_path(cli_file_path)
        print(f"Usage: {package_name} <command> [args...]")
        print("\nCommands:")
        for cmd_name, cmd_info in sorted(commands.items()):
            description = cmd_info["description"]
            print(f"  {cmd_name:<12} {description}")
        print("\nExamples:")
        for cmd_name in list(commands.keys())[:3]:
            print(f"  {package_name} {cmd_name}")
        return 1

    command = args[0].lower()

    if command in commands:
        cmd_info = commands[command]
        cmd_func = cmd_info["func"]
        if isinstance(cmd_func, str):
            print(f"Invalid command function for '{command}'", file=sys.stderr)
            return 1
        func = cast("Callable[[list[str]], bool]", cmd_func)
        try:
            result = func(args[1:] if len(args) > 1 else [])
            return 0 if result else 1
        except Exception as exc:
            print(f"Error executing command '{command}': {exc}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(f"Available commands: {', '.join(sorted(commands.keys()))}")
        return 1


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


def _load_modules():
    """Load required modules after adding parent to sys.path."""
    try:
        from qualitybase.services import utils
        return utils
    except ImportError:
        _services_dir = Path(__file__).resolve().parent
        _project_root = _services_dir.parent
        if str(_project_root) not in sys.path:
            sys.path.insert(0, str(_project_root))

        try:
            from services import utils
            return utils
        except ImportError:
            from qualitybase.services import utils
            return utils


def _get_package_name_from_caller() -> Path | str:
    """Detect cli.py path from caller stack.

    Returns:
        Path to cli.py file if found, otherwise "unknown" string
    """
    import inspect
    frame = inspect.currentframe()
    qualitybase_cli_path = Path(__file__).resolve()
    for _ in range(20):
        if not frame:
            break
        frame = frame.f_back
        if frame:
            frame_file = frame.f_globals.get("__file__")
            if frame_file:
                frame_path = Path(frame_file).resolve()
                if "cli.py" in frame_file and frame_path != qualitybase_cli_path:
                    return frame_path
    return Path(__file__)


def main() -> int:
    """Main entry point for qualitybase CLI."""
    cli_file_path = Path(__file__)
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    return cli_main(cli_file_path, args)


if __name__ == "__main__":
    sys.exit(main())


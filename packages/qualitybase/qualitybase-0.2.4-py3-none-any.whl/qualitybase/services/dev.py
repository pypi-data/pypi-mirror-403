#!/usr/bin/env python3
"""Development helper script for Python projects.

This is a template script that provides common development tasks.
"""

from __future__ import annotations

import os
import sys

from qualitybase.services import utils
from qualitybase.services.dev import build, clean, env, help, lib

# Import utility functions for error handling
print_info = utils.print_info
print_error = utils.print_error
print_warning = utils.print_warning

# Import task functions from modules
task_help = help.task_help
task_venv = env.task_venv
task_install = env.task_install
task_install_dev = env.task_install_dev
task_venv_clean = env.task_venv_clean
task_load_envfile = env.task_load_envfile
task_clean = clean.task_clean
task_clean_build = clean.task_clean_build
task_clean_pyc = clean.task_clean_pyc
task_clean_test = clean.task_clean_test
task_build = build.task_build
task_update_lib = lib.task_update_lib


COMMANDS = {
    "help": task_help,
    "venv": task_venv,
    "install": task_install,
    "install-dev": task_install_dev,
    "venv-clean": task_venv_clean,
    "load-envfile": task_load_envfile,
    "clean": task_clean,
    "clean-build": task_clean_build,
    "clean-pyc": task_clean_pyc,
    "clean-test": task_clean_test,
    "build": task_build,
    "update-lib": task_update_lib,
}


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    args = list(argv if argv is not None else sys.argv[1:])

    envfile_path = os.environ.get("ENVFILE_PATH")
    if envfile_path:
        from pathlib import Path

        env_file = Path(envfile_path)
        if not env_file.is_absolute():
            env_file = (utils.PROJECT_ROOT / envfile_path).resolve()
        env._load_envfile_from_path(env_file)  # noqa: SLF001

    if not args:
        task_help()
        return 0

    command = args[0]
    if command not in COMMANDS:
        print_error(f"Unknown command: {command}")
        print_info("Run `./service.py dev help` to list available commands.")
        return 1

    return utils.run_service_command(COMMANDS[command])


if __name__ == "__main__":
    sys.exit(main())


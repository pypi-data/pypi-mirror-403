"""Base command class."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class Command:
    """Command class containing description and execution function."""

    description: str
    func: Callable[[list[str]], bool]

    def __init__(
        self,
        func: Callable[[list[str]], bool],
        description: str = "",
    ) -> None:
        """Initialize a command.

        Args:
            func: Function to execute. Takes args list and returns bool.
            description: Command description for help.
        """
        self.func = func
        self.description = description or (func.__doc__ or "").split("\n")[0].strip()

    def __call__(self, args: list[str]) -> bool:
        """Execute the command.

        Args:
            args: Command arguments.

        Returns:
            True if command executed successfully, False otherwise.
        """
        return self.func(args)


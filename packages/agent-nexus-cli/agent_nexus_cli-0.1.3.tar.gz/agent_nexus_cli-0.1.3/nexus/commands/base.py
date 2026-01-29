"""Base Command Module.

Defines the interface for slash commands.
"""

from typing import Protocol


class Command(Protocol):
    """Command Protocol.

    Interface that all slash commands must implement.

    Inherits:
        typing.Protocol

    Attrs:
        name: str - Command name.
        description: str - Command description.

    Methods:
        execute(args): Execute the command.
    """

    name: str
    description: str

    async def execute(self, args: list[str], context: dict | None = None) -> None:
        """Execute the command.

        Args:
            args: list[str] - Command arguments.
            context: dict | None - Optional execution context.

        Returns:
            None

        Raises:
            None
        """

        ...

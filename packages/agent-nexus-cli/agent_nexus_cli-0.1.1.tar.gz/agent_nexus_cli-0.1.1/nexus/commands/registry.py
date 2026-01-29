"""Command Registry Module.

Manages the registration and execution of slash commands.
"""

from typing import ClassVar

from rich.table import Table

from nexus.commands.base import Command
from nexus.ui.console import console


class CommandRegistry:
    """Command Registry Class.

    Central registry for all available slash commands.

    Inherits:
        None

    Attrs:
        _commands: ClassVar[dict[str, Command]] - Dictionary of registered commands.

    Methods:
        register(command): Register a new command.
        get_command(name): Get a command by name.
        execute(input_str): Execute a command string.
        list_commands(): Get all registered commands.
        show_help(): Display help for all commands.
    """

    _commands: ClassVar[dict[str, Command]] = {}

    @classmethod
    def register(cls, command: Command) -> None:
        """Register a new command.

        Args:
            command: Command - Command instance to register.

        Returns:
            None

        Raises:
            None
        """

        cls._commands[command.name] = command

    @classmethod
    def get_command(cls, name: str) -> Command | None:
        """Get a command by name.

        Args:
            name: str - Command name.

        Returns:
            Command | None - The command instance or None if not found.

        Raises:
            None
        """

        return cls._commands.get(name)

    @classmethod
    async def execute(cls, input_str: str, context: dict | None = None) -> bool:
        """Execute a command string.

        Args:
            input_str: str - Raw input string.
            context: dict | None - Optional execution context.

        Returns:
            bool - True if a command was found and executed.

        Raises:
            None
        """

        if not input_str.startswith("/"):
            return False

        parts = input_str[1:].split()
        if not parts:
            return False

        cmd_name = parts[0].lower()
        args = parts[1:]

        command = cls.get_command(cmd_name)
        if command:
            await command.execute(args, context=context)
            return True

        console.print(f"[red]Unknown command: /{cmd_name}[/red]")
        console.print("[dim]Type /help for a list of available commands.[/dim]")
        return True

    @classmethod
    def list_commands(cls) -> list[Command]:
        """Get all registered commands.

        Args:
            None

        Returns:
            list[Command] - List of registered commands sorted by name.

        Raises:
            None
        """

        return sorted(cls._commands.values(), key=lambda x: x.name)

    @classmethod
    def show_help(cls) -> None:
        """Display help for all commands.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """

        table = Table(
            title="[bold cyan]Available Commands[/bold cyan]",
            show_header=True,
            header_style="bold white",
            border_style="cyan",
            expand=False,
        )
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")

        for cmd in cls.list_commands():
            table.add_row(f"/{cmd.name}", cmd.description)

        console.print(table)
        console.print()

"""Core Commands Module.

Implementation of core slash commands.
"""

from rich.align import Align
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table, box
from rich.text import Text

from nexus.agent.metrics import MetricsManager
from nexus.commands.registry import CommandRegistry
from nexus.config.settings import settings
from nexus.tools.mcp import _active_mcp_tools_info, get_mcp_status
from nexus.ui.console import console


class HelpCommand:
    """Help Command Class.

    Lists available slash commands.

    Inherits:
        None

    Attrs:
        name: str - Command name.
        description: str - Command description.

    Methods:
        execute(args): Execute help command.
    """

    name = "help"
    description = "Show available slash commands"

    async def execute(self, args: list[str], context: dict | None = None) -> None:
        """Execute help command.

        Args:
            args: list[str] - Command arguments.
            context: dict | None - Optional execution context.

        Returns:
            None

        Raises:
            None
        """

        CommandRegistry.show_help()


class AboutCommand:
    """About Command Class.

    Shows application information.

    Inherits:
        None

    Attrs:
        name: str - Command name.
        description: str - Command description.

    Methods:
        execute(args): Execute about command.
    """

    name = "about"
    description = "Show application information"

    async def execute(self, args: list[str], context: dict | None = None) -> None:
        """Execute about command.

        Args:
            args: list[str] - Command arguments.
            context: dict | None - Optional execution context.

        Returns:
            None

        Raises:
            None
        """

        banner_text = Text.assemble(
            ("NEXUS", "bold white"),
            (" - AI Coding Agent\n", "bold cyan"),
            ("Powered by LangChain, LangGraph & MCP", "dim cyan"),
        )

        panel = Panel(
            Align.left(banner_text),
            border_style="cyan",
            width=60,
            padding=(1, 2),
        )
        console.print(panel)
        console.print()


class ConfigCommand:
    """Config Command Class.

    Shows current configuration settings.

    Inherits:
        None

    Attrs:
        name: str - Command name.
        description: str - Command description.

    Methods:
        execute(args): Execute config command.
    """

    name = "config"
    description = "Show current configuration"

    async def execute(self, args: list[str], context: dict | None = None) -> None:
        """Execute config command.

        Args:
            args: list[str] - Command arguments.
            context: dict | None - Optional execution context.

        Returns:
            None

        Raises:
            None
        """

        table = Table(
            title="[bold cyan]Configuration[/bold cyan]",
            show_header=True,
            header_style="bold white",
            border_style="cyan",
            padding=(0, 1),
        )
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        if context and "get_state" in context:
            state = context["get_state"]()
            current_mode = state.get("current_mode", "CODE")
            table.add_row("Current Mode", f"[bold cyan]{current_mode}[/bold cyan]")

        table.add_row("Model", f"[green]{settings.model_name}[/green]")
        table.add_row("Temperature", f"[yellow]{settings.temperature}[/yellow]")
        table.add_row("Max Tokens", f"[yellow]{settings.max_tokens}[/yellow]")
        table.add_row("Max Iterations", f"[yellow]{settings.max_iterations}[/yellow]")
        table.add_row(
            "Approval Required",
            "[green]Yes[/green]" if settings.approval_required else "[red]No[/red]",
        )
        table.add_row("Working Directory", f"[dim]{settings.working_directory}[/dim]")
        table.add_row(
            "LangSmith Tracing",
            "[green]Enabled[/green]" if settings.langsmith_tracing else "[red]Disabled[/red]",
        )
        table.add_row("Checkpoint DB", f"[dim]{settings.checkpoint_db}[/dim]")
        table.add_row("Plans Directory", f"[dim]{settings.plans_directory}[/dim]")
        table.add_row("Log Level", f"[yellow]{settings.log_level}[/yellow]")

        console.print(table)
        console.print()


class MCPsCommand:
    """MCPs Command Class.

    Shows detailed info about active MCP servers and tools.

    Inherits:
        None

    Attrs:
        name: str - Command name.
        description: str - Command description.

    Methods:
        execute(args): Execute mcps command.
    """

    name = "mcps"
    description = "Show active MCP servers and tool details"

    async def execute(self, args: list[str], context: dict | None = None) -> None:
        """Execute mcps command.

        Args:
            args: list[str] - Command arguments.
            context: dict | None - Optional execution context.

        Returns:
            None

        Raises:
            None
        """

        status = get_mcp_status()
        mcp_loaded = status["loaded"]

        mcp_panel_title = f"[bold cyan]Active MCP Servers ({mcp_loaded})[/bold cyan]"

        if mcp_loaded == 0:
            console.print(
                Panel(
                    "[dim]No active MCP servers found.[/dim]",
                    title=mcp_panel_title,
                    border_style="cyan",
                    width=60,
                ),
            )
            return

        for server in status["servers"]:
            name = server["name"]
            command = server["command"]
            tool_count = server["tools"]

            server_table = Table(box=box.SIMPLE, show_edge=False, padding=(0, 1), expand=True)
            server_table.add_column("Property", style="dim", width=15)
            server_table.add_column("Value", style="white")

            server_table.add_row("Command", command)
            server_table.add_row("Tool Count", str(tool_count))

            tools_info = _active_mcp_tools_info.get(name, [])
            if tools_info:
                server_table.add_row("", "")
                server_table.add_row("[cyan]Tools[/cyan]", "")
                for t in tools_info:
                    server_table.add_row("", f"[bold]{t['name']}[/bold]: {t['description']}")

            console.print(
                Panel(
                    server_table,
                    title=f"[bold green]{name}[/bold green]",
                    border_style="dim",
                    expand=False,
                ),
            )
            console.print()


class ModeCommand:
    """Mode Command Class.

    Switches agent operational mode.

    Inherits:
        None

    Attrs:
        name: str - Command name.
        description: str - Command description.

    Methods:
        execute(args, context): Execute mode command.
    """

    name = "mode"
    description = "Switch agent operational mode (code, architect, ask)"

    async def execute(self, args: list[str], context: dict | None = None) -> None:
        """Execute mode command.

        Args:
            args: list[str] - Command arguments.
            context: dict | None - Optional execution context.

        Returns:
            None

        Raises:
            None
        """

        if not args:
            current_mode = "unknown"
            if context and "get_state" in context:
                state = context["get_state"]()
                current_mode = state.get("current_mode", "CODE")

            console.print(f"[yellow]Current mode:[/yellow] [bold cyan]{current_mode}[/bold cyan]")
            console.print("[yellow]Usage:[/yellow] /mode <code|architect|ask>")
            return

        mode_name = args[0].upper()
        if mode_name not in ["CODE", "ARCHITECT", "ASK"]:
            console.print(f"[red]Invalid mode: {args[0]}[/red]")
            console.print("[yellow]Available modes:[/yellow] code, architect, ask")
            return

        if context and "update_state" in context:
            await context["update_state"]({"current_mode": mode_name})
            console.print(f"[green]✓[/green] Switched to [bold cyan]{mode_name}[/bold cyan] mode")
        else:
            console.print("[red]Error: Could not update agent mode in this context.[/red]")


class MetricsCommand:
    """Metrics Command Class.

    Shows aggregate metrics for current session.

    Inherits:
        None

    Attrs:
        name: str - Command name.
        description: str - Command description.

    Methods:
        execute(args, context): Execute metrics command.
    """

    name = "metrics"
    description = "Show aggregate session metrics"

    async def execute(self, args: list[str], context: dict | None = None) -> None:
        """Execute metrics command.

        Args:
            args: list[str] - Command arguments.
            context: dict | None - Optional execution context.

        Returns:
            None

        Raises:
            None
        """

        if not context or "metrics_manager" not in context or "thread_id" not in context:
            console.print("[red]Error: Metrics context not available.[/red]")
            return

        metrics_manager: MetricsManager = context["metrics_manager"]
        thread_id: str = context["thread_id"]

        summary = metrics_manager.get_session_summary(thread_id)
        if not summary or not summary.get("total_requests"):
            console.print("[yellow]No metrics available for this session yet.[/yellow]")
            return

        table = Table(
            title=f"[bold cyan]Aggregate Metrics: {thread_id}[/bold cyan]",
            show_header=True,
            header_style="bold white",
            border_style="cyan",
            box=box.ROUNDED,
        )

        table.add_column("Metric", style="dim")
        table.add_column("Value", style="white")

        table.add_row("Total Requests", str(summary["total_requests"]))
        table.add_row("Total Latency", f"{summary['total_latency']:.2f}s")
        table.add_row("Avg Latency", f"{summary['avg_latency']:.2f}s")

        ttft = summary.get("avg_ttft")
        if ttft is not None:
            table.add_row("Avg TTFT", f"{ttft:.2f}s")

        table.add_row(Rule(style="dim"), Rule(style="dim"))
        table.add_row("Total Input Tokens", str(summary["total_input_tokens"]))
        table.add_row("Total Output Tokens", str(summary["total_output_tokens"]))
        table.add_row("Total Tokens", str(summary["total_tokens"]))

        cached = summary.get("total_cached_tokens", 0)
        if cached > 0:
            table.add_row("Total Cached Tokens", str(cached))

        console.print(table)
        console.print()


def register_core_commands() -> None:
    """Register core commands.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """

    CommandRegistry.register(HelpCommand())
    CommandRegistry.register(AboutCommand())
    CommandRegistry.register(ConfigCommand())
    CommandRegistry.register(MCPsCommand())
    CommandRegistry.register(ModeCommand())
    CommandRegistry.register(MetricsCommand())

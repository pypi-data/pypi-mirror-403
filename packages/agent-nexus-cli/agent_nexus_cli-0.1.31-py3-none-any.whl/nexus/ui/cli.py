"""CLI Module.

Rich-Click CLI for Nexus.
"""

import asyncio
import time
from typing import Any

import rich_click as click
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from rich.align import Align
from rich.columns import Columns
from rich.console import Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.table import Table, box
from rich.text import Text

from nexus.agent.graph import create_agent_graph
from nexus.agent.metrics import ChatMetrics, MetricsManager
from nexus.commands.core import register_core_commands
from nexus.commands.registry import CommandRegistry
from nexus.config.prompts import get_config_status
from nexus.config.settings import settings
from nexus.tools.mcp import get_mcp_status
from nexus.ui.console import console

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.STYLE_OPTION = "bold cyan"
click.rich_click.STYLE_ARGUMENT = "bold yellow"
click.rich_click.STYLE_COMMAND = "bold green"

PANEL_WIDTH_SMALL: int = 60
PANEL_WIDTH_MED: int = 70
PADDING_NORMAL: tuple[int, int] = (1, 2)
PADDING_WIDE: tuple[int, int] = (1, 4)


def print_banner() -> None:
    """Print Nexus Banner.

    Display modern responsive banner.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """

    banner_text = Text.assemble(
        ("NEXUS", "bold white"),
        (" - AI Coding Agent\n", "bold cyan"),
        ("Powered by LangChain & LangGraph", "dim cyan"),
    )

    banner_panel = Panel(
        Align.center(banner_text),
        border_style="cyan",
        width=PANEL_WIDTH_SMALL,
        padding=PADDING_NORMAL,
    )

    console.print(Align.center(banner_panel))


def _get_session_table(thread_id: str, mode: str, *, stream: bool) -> Table:
    """Get Session Table.

    Generate table for session information.

    Args:
        thread_id: str - Thread identifier.
        mode: str - Agent mode.
        stream: bool - Streaming status.

    Returns:
        Table - Session information table.

    Raises:
        None
    """

    mode_colors = {"CODE": "green", "ASK": "blue", "ARCHITECT": "magenta"}
    mode_style = mode_colors.get(mode, "cyan")

    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim", justify="right")
    table.add_column(style="cyan")
    table.add_row("Model", settings.model_name)
    table.add_row("Mode", f"[{mode_style}]{mode}[/{mode_style}]")
    table.add_row("Thread", thread_id)
    table.add_row("Working Dir", str(settings.working_directory))
    table.add_row("Streaming", "Enabled" if stream else "Disabled")
    return table


def _get_prompts_table(status: dict) -> Table:
    """Get Prompts Table.

    Generate table for custom prompts.

    Args:
        status: dict - Configuration status information.

    Returns:
        Table - Prompts information table.

    Raises:
        None
    """

    table = Table(box=box.SIMPLE_HEAD, show_edge=False, padding=(0, 1), expand=True)
    table.add_column("File", style="cyan")
    table.add_column("Lines", justify="right", style="dim")

    if status["prompts"]["loaded"] > 0:
        for p in status["prompts"]["files"]:
            table.add_row(p["name"], f"{p['lines']}")
    else:
        table.add_row("[dim]No valid prompts found[/dim]", "")
    return table


def _get_rules_table(status: dict) -> Table:
    """Get Rules Table.

    Generate table for loaded rules.

    Args:
        status: dict - Configuration status information.

    Returns:
        Table - Rules information table.

    Raises:
        None
    """

    table = Table(box=box.SIMPLE_HEAD, show_edge=False, padding=(0, 1), expand=True)
    table.add_column("File", style="cyan")
    table.add_column("Lines", justify="right", style="dim")

    if status["rules"]["loaded"] > 0:
        for r in status["rules"]["files"]:
            table.add_row(r["name"], f"{r['lines']}")
    else:
        table.add_row("[dim]No valid rules found[/dim]", "")
    return table


def _get_mcp_table() -> tuple[Table, int]:
    """Get MCP Table.

    Generate table for MCP server information.

    Args:
        None

    Returns:
        tuple[Table, int] - Table and count of loaded servers.

    Raises:
        None
    """

    status = get_mcp_status()
    table = Table(box=box.SIMPLE_HEAD, show_edge=False, padding=(0, 1), expand=True)
    table.add_column("Server", style="cyan")
    table.add_column("Command", justify="right", style="dim")

    if status["loaded"] > 0:
        for s in status["servers"]:
            table.add_row(s["name"], s["command"])
    else:
        table.add_row("[dim]No active MCP servers[/dim]", "")
    return table, status["loaded"]


def _print_session_info(thread_id: str, mode: str = "CODE", *, stream: bool) -> None:
    """Print Session Information.

    Display session configuration details.

    Args:
        thread_id: str - Thread identifier.
        mode: str - Agent mode.
        stream: bool - Streaming status.

    Returns:
        None

    Raises:
        None
    """

    session_table = _get_session_table(thread_id, mode, stream=stream)
    session_panel = Panel(
        session_table,
        title="[bold cyan]Session[/bold cyan]",
        border_style="cyan",
        width=PANEL_WIDTH_SMALL,
    )

    status = get_config_status()
    prompts_table = _get_prompts_table(status)
    prompts_panel = Panel(
        prompts_table,
        title=f"[bold cyan]Custom Prompts ({status['prompts']['loaded']})[/bold cyan]",
        border_style="cyan",
        width=PANEL_WIDTH_SMALL,
    )

    rules_table = _get_rules_table(status)
    rules_panel = Panel(
        rules_table,
        title=f"[bold cyan]Loaded Rules ({status['rules']['loaded']})[/bold cyan]",
        border_style="cyan",
        width=PANEL_WIDTH_SMALL,
    )

    mcp_table, mcp_loaded = _get_mcp_table()
    mcp_panel = Panel(
        mcp_table,
        title=f"[bold cyan]MCP Servers ({mcp_loaded})[/bold cyan]",
        border_style="cyan",
        width=PANEL_WIDTH_SMALL,
    )

    console.print(Align.center(session_panel))
    if status["prompts"]["loaded"] > 0:
        console.print(Align.center(prompts_panel))
    if status["rules"]["loaded"] > 0:
        console.print(Align.center(rules_panel))
    if mcp_loaded > 0:
        console.print(Align.center(mcp_panel))
    console.print()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="1.0.0", prog_name="nexus")
def cli(ctx: click.Context) -> None:
    """Nexus CLI.

    Primary command group for AI Coding Agent.

    Args:
        ctx: click.Context - Call context instance.

    Returns:
        None

    Raises:
        None
    """

    register_core_commands()

    if ctx.invoked_subcommand is None:
        print_banner()
        welcome_panel = Panel(
            "[bold white]Welcome to Nexus![/bold white]\n\n"
            "[dim]Available commands:[/dim]\n"
            "  [cyan]nexus chat[/cyan]     - Start interactive chat\n"
            "  [cyan]nexus history[/cyan]  - View conversation history\n"
            "  [cyan]nexus config[/cyan]   - Show configuration\n\n"
            "[dim]For help:[/dim] [yellow]nexus --help[/yellow]",
            border_style="cyan",
            padding=PADDING_WIDE,
            width=PANEL_WIDTH_SMALL,
        )
        console.print(Align.center(welcome_panel))


@cli.command()
@click.argument("message", required=False)
@click.option(
    "--thread-id",
    "-t",
    help="Thread ID for conversation continuity",
    default="default",
)
@click.option(
    "--stream/--no-stream",
    default=True,
    help="Stream responses in real-time",
)
def chat(message: str | None, thread_id: str, *, stream: bool) -> None:
    """Chat Command.

    Start interactive chat session.

    Args:
        message: str | None - Initial message content.
        thread_id: str - Thread identity string.
        stream: bool - Response streaming flag.

    Returns:
        None

    Raises:
        None
    """

    asyncio.run(_chat(message, thread_id, stream=stream))


async def _chat(message: str | None, thread_id: str, *, stream: bool) -> None:
    """Internal Chat Execution.

    Execute internal chat logic within async loop.

    Args:
        message: str | None - Initial message.
        thread_id: str - Thread identifier.
        stream: bool - Streaming status.

    Returns:
        None

    Raises:
        None
    """

    print_banner()

    async with AsyncSqliteSaver.from_conn_string(settings.checkpoint_db) as checkpointer:
        status = console.status("[bold cyan]Initializing agent...[/bold cyan]", spinner="dots")
        status.start()
        try:
            async with create_agent_graph(checkpointer=checkpointer) as agent:
                status.stop()
                config: dict = {"configurable": {"thread_id": thread_id}}

                state = await agent.aget_state(config)
                current_mode = state.values.get("current_mode", "CODE") if state.values else "CODE"

                _print_session_info(thread_id, mode=current_mode, stream=stream)

                metrics_manager = MetricsManager()

                if message is None:
                    await _interactive_chat_loop(agent, config, metrics_manager, thread_id, stream=stream)
                else:
                    await _process_message(
                        agent,
                        message,
                        config,
                        stream=stream,
                        metrics_manager=metrics_manager,
                        thread_id=thread_id,
                        mode=current_mode,
                    )
                    _print_metrics_summary(metrics_manager, thread_id)
        finally:
            status.stop()


async def _interactive_chat_loop(
    agent: Any,
    config: dict,
    metrics_manager: MetricsManager,
    thread_id: str,
    *,
    stream: bool,
) -> None:
    """Interactive Chat Loop.

    Manage terminal chat session.

    Args:
        agent: Any - Agent graph instance.
        config: dict - Execution configuration dictionary.
        metrics_manager: MetricsManager - Session metrics manager.
        thread_id: str - Thread identifier.
        stream: bool - Token streaming flag.

    Returns:
        None

    Raises:
        None
    """

    console.print(
        Align.center(
            Panel(
                "[dim]Type your message and press Enter\n"
                "Commands: [yellow]exit[/yellow], [yellow]quit[/yellow], "
                "[yellow]q[/yellow] to exit[/dim]",
                border_style="dim",
                width=PANEL_WIDTH_SMALL,
            ),
        ),
    )
    console.print()

    session_start = time.time()
    while True:
        try:
            state = await agent.aget_state(config)
            current_mode = state.values.get("current_mode", "CODE") if state.values else "CODE"

            _print_header("User", mode=current_mode)

            prompt_text = "[bold green]> [/bold green]"
            message = console.input(f"{prompt_text}")

            if message.lower() in ["exit", "quit", "q"]:
                duration = time.time() - session_start
                _print_exit_screen(metrics_manager, thread_id, duration)
                break

            if not message.strip():
                continue

            async def get_current_state() -> dict:
                """Fetch current agent state.

                Args:
                    None

                Returns:
                    dict - Current agent state values.

                Raises:
                    None
                """

                st = await agent.aget_state(config)
                return st.values if st.values else {}

            async def update_state(new_values: dict) -> None:
                """Update agent state values.

                Args:
                    new_values: dict - New state values to merge.

                Returns:
                    None

                Raises:
                    None
                """

                await agent.aupdate_state(config, new_values, as_node="agent")

            context = {
                "get_state": get_current_state,
                "update_state": update_state,
                "metrics_manager": metrics_manager,
                "thread_id": thread_id,
            }

            if message.startswith("/") and await CommandRegistry.execute(message, context=context):
                continue

            await _process_message(
                agent,
                message,
                config,
                stream=stream,
                metrics_manager=metrics_manager,
                thread_id=thread_id,
                mode=current_mode,
            )

        except KeyboardInterrupt:
            console.print("\n\n[dim]Use 'exit' to quit[/dim]")
        except EOFError:
            duration = time.time() - session_start
            _print_exit_screen(metrics_manager, thread_id, duration)
            break


def _print_exit_screen(metrics_manager: MetricsManager, thread_id: str, duration: float) -> None:
    """Print Premium Exit Screen.

    Display session summary and goodbye message in a premium layout.

    Args:
        metrics_manager: MetricsManager - Session metrics manager.
        thread_id: str - Thread identifier.
        duration: float - Session duration in seconds.

    Returns:
        None

    Raises:
        None
    """

    summary = metrics_manager.get_session_summary(thread_id)

    goodbye_text = Text.assemble(
        ("NEXUS ARCHIVE COMPLETE", "bold cyan"),
        ("\nSession terminated successfully. Standing by for next deployment.", "italic dim"),
    )

    minutes = int(duration // 60)
    seconds = int(duration % 60)
    duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    stats = []
    if summary and summary.get("total_requests"):
        stats.append(
            Panel(
                Align.center(f"[bold cyan]{summary['total_requests']}[/bold cyan]\n[dim]Requests[/dim]"),
                border_style="dim",
                width=20,
            ),
        )
        stats.append(
            Panel(
                Align.center(f"[bold green]{summary.get('total_tokens', 0):,}[/bold green]\n[dim]Tokens[/dim]"),
                border_style="dim",
                width=20,
            ),
        )
        stats.append(
            Panel(
                Align.center(f"[bold yellow]{duration_str}[/bold yellow]\n[dim]Session[/dim]"),
                border_style="dim",
                width=20,
            ),
        )

    console.print()
    console.print(Rule(style="dim"))
    console.print()

    console.print(
        Align.center(
            Panel(
                Align.center(goodbye_text),
                border_style="cyan",
                padding=(1, 2),
                width=PANEL_WIDTH_SMALL,
            ),
        ),
    )

    console.print()

    if stats:
        console.print(Align.center(Columns(stats, equal=True, expand=False)))
        console.print()

    if summary and summary.get("total_requests"):
        _print_metrics_summary(metrics_manager, thread_id, hide_title=True)

    console.print(Align.center("[dim]Nexus AI Agent • Developed by Rohit[/dim]"))
    console.print()


def _print_metrics_summary(
    metrics_manager: MetricsManager,
    thread_id: str,
    *,
    hide_title: bool = False,
) -> None:
    """Print Metrics Summary.

    Display aggregated session metrics in table.

    Args:
        metrics_manager: MetricsManager - Metrics manager instance.
        thread_id: str - Thread identifier.
        hide_title: bool - Flag to suppress table title.

    Returns:
        None

    Raises:
        None
    """

    summary: dict = metrics_manager.get_session_summary(thread_id)
    if not summary or not summary.get("total_requests"):
        return

    table = Table(
        title="[bold cyan]Session Metrics Summary[/bold cyan]" if not hide_title else None,
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

    console.print(Align.center(table, width=PANEL_WIDTH_MED))
    console.print()


def _print_request_metrics(metrics: ChatMetrics) -> None:
    """Print Request Metrics.

    Display performance metrics for single request.

    Args:
        metrics: ChatMetrics - Performance metrics data.

    Returns:
        None

    Raises:
        None
    """

    latency = f"{metrics.request_latency:.2f}s"
    ttft = f"{metrics.first_token_latency:.2f}s" if metrics.first_token_latency else "N/A"

    usage_parts = []
    if metrics.input_tokens > 0:
        usage_parts.append(f"{metrics.input_tokens} in")
    if metrics.output_tokens > 0:
        usage_parts.append(f"{metrics.output_tokens} out")
    if metrics.cached_tokens > 0:
        usage_parts.append(f"{metrics.cached_tokens} cached")

    usage_str = f"Usage: {metrics.total_tokens} tokens ({', '.join(usage_parts)})" if usage_parts else "Usage: N/A"

    metrics_text = Text.assemble(
        (" Latency: ", "dim"),
        (f"{latency}", "cyan dim"),
        (" | TTFT: ", "dim"),
        (f"{ttft}", "cyan dim"),
        (" | ", "dim"),
        (f"{usage_str} ", "dim"),
    )

    console.print(Rule(metrics_text, style="dim", align="right"))


def _print_header(role: str, mode: str | None = None) -> None:
    """Print Header.

    Display styled header for role or mode.

    Args:
        role: str - Role name.
        mode: str | None - Optional agent mode.

    Returns:
        None

    Raises:
        None
    """

    if role.lower() == "user":
        mode_colors = {
            "CODE": "green",
            "ASK": "blue",
            "ARCHITECT": "magenta",
        }
        style = mode_colors.get(mode or "CODE", "green")
        label = f" {mode or 'USER'} "
    else:
        style = "cyan"
        label = " Assistant "

    console.print()
    console.print(Rule(f"[bold white on {style}] {label} [/bold white on {style}]", style=style))
    console.print()


class StreamingResponseHandler:
    """StreamingResponseHandler.

    Manage state and rendering of streaming AI responses.

    Inherits:
        None

    Attrs:
        full_content: str - Accumulated response content.

    Methods:
        __init__(): Initialize handler.
        update(chunk): Update content with chunk.
        render(): Render current state as Rich group.
    """

    def __init__(self) -> None:
        """Initialize StreamingResponseHandler.

        Set default empty content.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """

        self.full_content: str = ""

    def update(self, chunk: str) -> None:
        """Update content with new chunk.

        Append chunk to full content string.

        Args:
            chunk: str - Text chunk from stream.

        Returns:
            None

        Raises:
            None
        """

        self.full_content += chunk

    def render(self) -> Group:
        """Render current state.

        Generate Rich Group containing Markdown.

        Args:
            None

        Returns:
            Group - Renderable content group.

        Raises:
            None
        """

        if not self.full_content:
            return Group(Text("...", style="dim"))

        return Group(Markdown(self.full_content))


async def _handle_streaming_response(
    agent: Any,
    input_state: dict,
    config: dict,
    mode: str,
    start_time: float,
) -> tuple[float | None, dict]:
    """Handle Streaming Response.

    Render AI output chunks.

    Args:
        agent: Any - Agent graph instance.
        input_state: dict - State dictionary.
        config: dict - Runtime configuration context.
        mode: str - Current operation mode.
        start_time: float - Execution start timestamp.

    Returns:
        tuple[float | None, dict] - TTFT and usage metadata.

    Raises:
        None
    """

    _print_header("Assistant", mode=mode)
    ttft: float | None = None
    usage: dict = {}

    handler = StreamingResponseHandler()
    with Live(handler.render(), console=console, refresh_per_second=10) as live:
        async for event in agent.astream_events(input_state, config, version="v2"):
            kind: str = event["event"]

            if kind == "on_chat_model_stream":
                if ttft is None:
                    ttft = time.time() - start_time
                content: str = event["data"]["chunk"].content
                if content:
                    handler.update(content)
                    live.update(handler.render())
            elif kind == "on_chat_model_end":
                output = event["data"].get("output", {})
                if hasattr(output, "usage_metadata") and output.usage_metadata:
                    usage = output.usage_metadata
            elif kind == "on_tool_start":
                tool_name: str = event["name"]
                live.stop()
                console.print(f"\n[dim]┌─ Tool: [cyan]{tool_name}[/cyan][/dim]")
            elif kind == "on_tool_end":
                console.print("[dim]└─ ✓ Completed[/dim]\n")
                live.start()
            elif kind == "on_chain_start" and event["name"] == "approval":
                live.stop()
            elif kind == "on_chain_end" and event["name"] == "approval":
                live.start()

    console.print()
    return ttft, usage


async def _handle_static_response(agent: Any, input_state: dict, config: dict, mode: str) -> dict:
    """Handle Static Response.

    Invoke AI and show final output.

    Args:
        agent: Any - Agent graph instance.
        input_state: dict - State dictionary.
        config: dict - Runtime configuration context.
        mode: str - Current operation mode.

    Returns:
        dict - Token usage metadata.

    Raises:
        None
    """

    with console.status("[bold cyan]Processing...[/bold cyan]", spinner="dots"):
        result: dict = await agent.ainvoke(input_state, config)

    last_message: Any = result["messages"][-1]
    usage: dict = {}
    if hasattr(last_message, "usage_metadata") and last_message.usage_metadata:
        usage = last_message.usage_metadata

    mode_colors = {"CODE": "green", "ASK": "blue", "ARCHITECT": "magenta"}
    style = mode_colors.get(mode, "cyan")

    console.print(
        Align.center(
            Panel(
                Markdown(last_message.content),
                title=f"[bold white on {style}] Assistant [/bold white on {style}]",
                border_style=style,
                padding=(1, 2),
                width=PANEL_WIDTH_MED,
            ),
        ),
    )
    console.print()
    return usage


async def _process_message(  # noqa: PLR0913
    agent: Any,
    message: str,
    config: dict,
    *,
    stream: bool,
    metrics_manager: MetricsManager,
    thread_id: str,
    mode: str = "CODE",
) -> None:
    """Process Message.

    Process user input and record metrics.

    Args:
        agent: Any - Agent graph instance.
        message: str - User input content.
        config: dict - Runtime configuration context.
        stream: bool - Response streaming flag.
        metrics_manager: MetricsManager - Statistics tracking manager.
        thread_id: str - Thread identifier.
        mode: str - Operational mode identifier.

    Returns:
        None

    Raises:
        None
    """

    input_state: dict = {
        "messages": [HumanMessage(content=message)],
        "iteration_count": 0,
        "working_directory": str(settings.working_directory),
        "tool_calls_made": [],
        "files_modified": [],
    }

    console.print()
    start_time = time.time()

    if stream:
        ttft, usage = await _handle_streaming_response(agent, input_state, config, mode, start_time)
    else:
        ttft = None
        usage = await _handle_static_response(agent, input_state, config, mode)

    total_latency = time.time() - start_time
    metrics = ChatMetrics(
        thread_id=thread_id,
        timestamp=start_time,
        request_latency=total_latency,
        first_token_latency=ttft,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        cached_tokens=usage.get("cached_tokens", 0),
    )
    metrics_manager.save_metrics(metrics)
    _print_request_metrics(metrics)


@cli.command()
@click.option(
    "--thread-id",
    "-t",
    help="Thread ID to show history for",
    default="default",
)
@click.option(
    "--limit",
    "-n",
    help="Number of checkpoints to show",
    default=10,
    type=int,
)
def history(thread_id: str, limit: int) -> None:
    """History Command.

    Show conversation history for thread.

    Args:
        thread_id: str - Thread identifier.
        limit: int - Maximum checkpoints to display.

    Returns:
        None

    Raises:
        None
    """

    asyncio.run(_show_history(thread_id, limit))


async def _show_history(thread_id: str, limit: int) -> None:
    """Show History.

    Display historical conversation states.

    Args:
        thread_id: str - Thread identifier.
        limit: int - Checkpoint limit.

    Returns:
        None

    Raises:
        None
    """

    print_banner()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Loading history...", total=None)

        async with AsyncSqliteSaver.from_conn_string(settings.checkpoint_db) as checkpointer:
            config: dict = {"configurable": {"thread_id": thread_id}}

            checkpoints: list = [checkpoint async for checkpoint in checkpointer.alist(config)]  # ty:ignore[invalid-argument-type]

    if not checkpoints:
        console.print(
            Align.center(
                Panel(
                    f"[yellow]No history found for thread '[cyan]{thread_id}[/cyan]'[/yellow]",
                    border_style="yellow",
                    width=PANEL_WIDTH_SMALL,
                ),
            ),
        )
        return

    console.print(
        Align.center(
            Panel(
                f"[bold]Conversation History[/bold]\n"
                f"[dim]Thread:[/dim] [cyan]{thread_id}[/cyan]\n"
                f"[dim]Total Checkpoints:[/dim] [cyan]{len(checkpoints)}[/cyan]",
                border_style="cyan",
                width=PANEL_WIDTH_SMALL,
            ),
        ),
    )
    console.print()

    for i, checkpoint in enumerate(reversed(checkpoints[:limit]), 1):
        state: dict = checkpoint.checkpoint["channel_values"]
        messages: list = state.get("messages", [])

        console.print(f"[bold cyan]Checkpoint {i}[/bold cyan]")
        console.print()

        for msg in messages:
            role: str = msg.__class__.__name__
            content: str = getattr(msg, "content", "")

            if role == "HumanMessage":
                console.print(f"[bold green]User:[/bold green] {content}")
            elif role == "AIMessage":
                console.print(f"[bold cyan]Assistant:[/bold cyan] {content[:200]}...")
            else:
                console.print(f"[dim]{role}:[/dim] {content[:100]}...")

        console.print(Align.center(Rule(style="dim"), width=PANEL_WIDTH_SMALL))
        console.print()


@cli.command()
def config() -> None:
    """Config Command.

    Show application settings and environment.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """

    print_banner()

    table: Table = Table(
        title="[bold cyan]Configuration[/bold cyan]",
        show_header=True,
        header_style="bold white",
        border_style="cyan",
        padding=(0, 1),
    )
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Agent Mode", "[bold cyan]CODE[/bold cyan] [dim](Default)[/dim]")
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
    table.add_row("Log Level", f"[yellow]{settings.log_level}[/yellow]")

    console.print(Align.center(table))
    console.print()


if __name__ == "__main__":
    cli()


__all__: list[str] = ["cli"]

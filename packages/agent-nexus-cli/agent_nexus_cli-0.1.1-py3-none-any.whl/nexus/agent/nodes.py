"""Nodes Module.

Graph nodes for the LangGraph agent.
"""

from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from rich.prompt import Confirm

from nexus.agent.approval import request_tool_approval
from nexus.agent.modes import AgentMode
from nexus.agent.restrictions import (
    filter_tools_by_mode,
    get_mode_switch_suggestion,
    validate_tool_execution,
)
from nexus.agent.state import AgentState
from nexus.config.prompts import SYSTEM_PROMPT
from nexus.config.settings import settings
from nexus.ui.console import console


def create_agent_node(
    llm: ChatOpenAI,
    tools: list,
    mcp_tools: list,
    mcp_context: str = "",
) -> Callable:
    """Create Agent Node.

    Create the main agent node.

    Args:
        llm: ChatOpenAI - Language model.
        tools: list - List of internal tools.
        mcp_tools: list - List of MCP tools.
        mcp_context: str - Optional MCP context string.

    Returns:
        callable - Agent node function.

    Raises:
        None
    """

    def agent_node(state: AgentState) -> AgentState:
        """Agent Node.

        Agent reasoning node.

        Args:
            state: AgentState - Current state.

        Returns:
            AgentState - Updated state.

        Raises:
            None
        """

        current_mode_str: str = state.get("current_mode", "CODE")
        current_mode: AgentMode = AgentMode[current_mode_str]

        mode_prompt = f"\n\nCURRENT OPERATIONAL MODE: {current_mode.value}\n"
        if current_mode == AgentMode.ARCHITECT:
            mode_prompt += (
                f"You are in ARCHITECT mode. Your task is to plan and design.\n"
                f"IMPORTANT: You are RESTRICTED to writing files only within the "
                f"'{settings.plans_directory}' directory.\n"
                f"Always use the 'write_file' tool for any design documents, plans, or architectural specifications.\n"
                f"DO NOT use 'execute_shell_command' to create files (redirections like '>' are not supported).\n"
                "If you need to implement code or access files outside the plans directory, you can still "
                "attempt to use the tool, and the system will prompt the user to switch to CODE mode. "
                "Alternatively, you can ask the user to switch modes manually using the '/mode code' command."
            )
        elif current_mode == AgentMode.ASK:
            mode_prompt += (
                "You are in ASK mode. You are restricted to conversation and research.\n"
                "You cannot modify any files or execute shell commands.\n"
                "If you need to perform actions, attempt the tool to trigger a mode-switch suggestion, "
                "or ask the user to use '/mode code' or '/mode architect'."
            )
        elif current_mode == AgentMode.CODE:
            mode_prompt += (
                "You are in CODE mode. You have full access to all tools and file operations.\n"
                "If you are doing high-level architectural work, you can suggest switching to ARCHITECT "
                "mode via the '/mode architect' command to stay organized within the plans directory."
            )

        mode_system_prompt = f"{SYSTEM_PROMPT}{mode_prompt}"
        if mcp_context:
            mode_system_prompt += f"\n\n{mcp_context}"

        filtered_tools: list = filter_tools_by_mode(tools, current_mode, mcp_tools)
        llm_with_tools: Any = llm.bind_tools(filtered_tools)

        messages: list = state.get("messages", [])

        max_text_chars = 10000
        processed_messages = []
        for m in messages:
            if isinstance(m, SystemMessage):
                continue

            content = getattr(m, "content", "")
            if isinstance(content, str) and len(content) > max_text_chars:
                m.content = content[:max_text_chars] + "... (truncated for context safety)"
            processed_messages.append(m)

        max_recent_messages = 15
        if len(processed_messages) > max_recent_messages:
            processed_messages = processed_messages[-max_recent_messages:]

        final_messages = [SystemMessage(content=mode_system_prompt), *processed_messages]

        response: AIMessage = llm_with_tools.invoke(final_messages)

        return {
            "messages": [response],
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

    return agent_node


def should_continue(state: AgentState) -> str:
    """Should Continue.

    Determine if agent should continue or end.

    Args:
        state: AgentState - Current state.

    Returns:
        str - Next node name.

    Raises:
        None
    """

    messages: list = state.get("messages", [])
    if not messages:
        return "end"

    last_message: Any = messages[-1]

    if state.get("iteration_count", 0) >= settings.max_iterations:
        return "end"

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        if settings.approval_required:
            return "request_approval"
        return "continue"

    return "end"


async def approval_node(state: AgentState) -> AgentState:
    """Approval Node.

    Request human approval for tool execution with mode validation.

    Args:
        state: AgentState - Current state.

    Returns:
        AgentState - Updated state.

    Raises:
        None
    """

    messages: list = state.get("messages", [])
    if not messages:
        return state

    last_message: Any = messages[-1]

    current_mode_str: str = state.get("current_mode", "CODE")
    current_mode: AgentMode = AgentMode[current_mode_str]

    all_approved: bool = True

    for tool_call in last_message.tool_calls:
        tool_name: str = tool_call["name"]
        tool_args: dict = tool_call["args"]

        is_valid, error_msg = validate_tool_execution(
            tool_name,
            tool_args,
            current_mode,
        )

        if not is_valid:
            suggestion = get_mode_switch_suggestion(tool_name, tool_args, current_mode)
            if suggestion:
                target_mode, _ = suggestion
                console.print(f"\n[bold yellow]⚠ Mode Restriction:[/bold yellow] {error_msg}")
                if Confirm.ask(f"Switch to [bold cyan]{target_mode.value}[/bold cyan] mode and proceed?", default=True):
                    current_mode = target_mode
                    current_mode_str = target_mode.value
                    console.print(f"[green]✓[/green] Mode switched to [bold]{current_mode_str}[/bold]")
                    is_valid = True
                else:
                    all_approved = False
                    continue
            else:
                console.print(f"\n[red]✗[/red] {error_msg}")
                all_approved = False
                continue

        if settings.approval_required:
            approved: bool = await request_tool_approval(
                tool_name,
                tool_args,
                description=tool_call.get("description", ""),
            )
            if not approved:
                all_approved = False
                break

            if tool_name == "switch_mode":
                target_mode_str = tool_args.get("target_mode", "").upper()
                if target_mode_str in [m.value for m in AgentMode]:
                    current_mode_str = target_mode_str
                    current_mode = AgentMode[current_mode_str]
                    console.print(f"[green]✓[/green] Agent mode switched to [bold cyan]{current_mode_str}[/bold cyan]")

    return {
        "approval_granted": all_approved,
        "pending_approval": False,
        "current_mode": current_mode_str,
    }  # ty:ignore[missing-typed-dict-key, invalid-return-type]


__all__: list[str] = ["approval_node", "create_agent_node", "should_continue"]

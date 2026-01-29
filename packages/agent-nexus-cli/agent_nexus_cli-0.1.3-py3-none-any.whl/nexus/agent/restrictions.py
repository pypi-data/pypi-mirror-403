"""Tool Restrictions Module.

Mode-based tool filtering and validation logic.
"""

from nexus.agent.modes import (
    AgentMode,
    get_mode_config,
    is_path_in_plans_dir,
    validate_file_path,
)
from nexus.config.settings import settings


def filter_tools_by_mode(
    tools: list,
    mode: AgentMode,
    mcp_tools: list,
) -> list:
    """Filter tools based on operational mode.

    Args:
        tools: list - All available internal tools.
        mode: AgentMode - Current operational mode.
        mcp_tools: list - MCP tools.

    Returns:
        list - Filtered tools allowed in mode.

    Raises:
        None
    """

    if mode == AgentMode.CODE:
        return tools + mcp_tools

    if mode == AgentMode.ARCHITECT:
        return tools + mcp_tools

    if mode == AgentMode.ASK:
        return mcp_tools

    return tools + mcp_tools


def validate_tool_execution(
    tool_name: str,
    tool_args: dict,
    mode: AgentMode,
) -> tuple[bool, str]:
    """Validate tool execution for current mode.

    Args:
        tool_name: str - Name of tool to execute.
        tool_args: dict - Tool arguments.
        mode: AgentMode - Current operational mode.

    Returns:
        tuple[bool, str] - (is_valid, error_message).

    Raises:
        None
    """

    config = get_mode_config(mode)

    file_write_tools: set[str] = {"write_file"}
    shell_tools: set[str] = {"execute_shell_command"}
    mode_tools: set[str] = {"switch_mode"}

    if tool_name in mode_tools:
        return True, ""

    if tool_name in file_write_tools and not config.allows_file_write:
        msg: str = f"File write operations not allowed in {mode.value} mode. Switch to CODE mode for file operations."
        return False, msg

    if tool_name in shell_tools and not config.allows_shell_exec:
        msg = f"Shell execution not allowed in {mode.value} mode. Switch to CODE mode for shell commands."
        return False, msg

    if config.restricted_to_plans_dir and tool_name in file_write_tools:
        path: str = tool_args.get("path", "")
        if path:
            is_valid, error_msg = validate_file_path(
                path,
                mode,
                settings.plans_directory,
            )
            if not is_valid:
                return False, error_msg

    return True, ""


def get_mode_switch_suggestion(
    tool_name: str,
    tool_args: dict,
    current_mode: AgentMode,
) -> tuple[AgentMode, str] | None:
    """Get mode switch suggestion for restricted tool.

    Args:
        tool_name: str - Name of restricted tool.
        tool_args: dict - Tool arguments.
        current_mode: AgentMode - Current operational mode.

    Returns:
        tuple[AgentMode, str] | None - (target_mode, reason) or None.

    Raises:
        None
    """

    file_write_tools: set[str] = {"write_file"}
    shell_tools: set[str] = {"execute_shell_command"}

    if current_mode == AgentMode.ASK and (tool_name in file_write_tools or tool_name in shell_tools):
        return (
            AgentMode.CODE,
            f"Tool '{tool_name}' requires CODE mode (currently in ASK mode)",
        )

    if current_mode == AgentMode.ARCHITECT and tool_name in file_write_tools:
        path: str = tool_args.get("path", "")
        if path and not is_path_in_plans_dir(path, settings.plans_directory):
            return (
                AgentMode.CODE,
                "Writing outside .nexus/plans/ requires CODE mode",
            )

    if current_mode == AgentMode.CODE and tool_name in file_write_tools:
        path: str = tool_args.get("path", "")
        if path and is_path_in_plans_dir(path, settings.plans_directory):
            return (
                AgentMode.ARCHITECT,
                "Writing to planning directory; consider switching to ARCHITECT mode",
            )

    return None


__all__: list[str] = [
    "filter_tools_by_mode",
    "get_mode_switch_suggestion",
    "validate_tool_execution",
]

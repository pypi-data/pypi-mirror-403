"""Agent Modes Module.

Defines operational modes for the agent with tool restrictions.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class AgentMode(Enum):
    """Agent Mode Enum.

    Defines available operational modes for the agent.

    Attrs:
        CODE: Full access mode with unrestricted file operations.
        ARCHITECT: Planning mode restricted to .nexus/plans directory.
        ASK: Conversation mode with no file operations.
    """

    CODE = "CODE"
    ARCHITECT = "ARCHITECT"
    ASK = "ASK"


@dataclass
class ModeConfig:
    """Mode Configuration.

    Configuration for agent operational mode.

    Attrs:
        mode: AgentMode - The operational mode.
        name: str - Display name of the mode.
        description: str - Description of mode capabilities.
        allows_file_write: bool - Whether file write operations are allowed.
        allows_shell_exec: bool - Whether shell command execution is allowed.
        restricted_to_plans_dir: bool - Whether file ops restricted to plans dir.
    """

    mode: AgentMode
    name: str
    description: str
    allows_file_write: bool
    allows_shell_exec: bool
    restricted_to_plans_dir: bool


CODE_MODE: ModeConfig = ModeConfig(
    mode=AgentMode.CODE,
    name="CODE",
    description="Full access mode - all tools and file operations enabled",
    allows_file_write=True,
    allows_shell_exec=True,
    restricted_to_plans_dir=False,
)

ARCHITECT_MODE: ModeConfig = ModeConfig(
    mode=AgentMode.ARCHITECT,
    name="ARCHITECT",
    description="Planning mode - file operations restricted to .nexus/plans/",
    allows_file_write=True,
    allows_shell_exec=True,
    restricted_to_plans_dir=True,
)

ASK_MODE: ModeConfig = ModeConfig(
    mode=AgentMode.ASK,
    name="ASK",
    description="Conversation mode - no file operations, MCP tools only",
    allows_file_write=False,
    allows_shell_exec=False,
    restricted_to_plans_dir=False,
)

_MODE_CONFIGS: dict[AgentMode, ModeConfig] = {
    AgentMode.CODE: CODE_MODE,
    AgentMode.ARCHITECT: ARCHITECT_MODE,
    AgentMode.ASK: ASK_MODE,
}


def get_mode_config(mode: AgentMode) -> ModeConfig:
    """Get configuration for specified mode.

    Args:
        mode: AgentMode - The mode to get configuration for.

    Returns:
        ModeConfig - Configuration for the mode.

    Raises:
        None
    """

    return _MODE_CONFIGS[mode]


def is_tool_allowed(tool_name: str, mode: AgentMode) -> bool:
    """Check if tool is allowed in specified mode.

    Args:
        tool_name: str - Name of the tool to check.
        mode: AgentMode - Current operational mode.

    Returns:
        bool - True if tool is allowed in mode.

    Raises:
        None
    """

    config: ModeConfig = get_mode_config(mode)

    file_write_tools: set[str] = {"write_file"}
    shell_tools: set[str] = {"execute_shell_command"}

    return not (
        (tool_name in file_write_tools and not config.allows_file_write)
        or (tool_name in shell_tools and not config.allows_shell_exec)
    )


def validate_file_path(
    path: str,
    mode: AgentMode,
    plans_dir: Path,
) -> tuple[bool, str]:
    """Validate file path for current mode.

    Args:
        path: str - File path to validate.
        mode: AgentMode - Current operational mode.
        plans_dir: Path - Path to plans directory.

    Returns:
        tuple[bool, str] - (is_valid, error_message).

    Raises:
        None
    """

    config: ModeConfig = get_mode_config(mode)

    if not config.restricted_to_plans_dir:
        return True, ""

    if not is_path_in_plans_dir(path, plans_dir):
        msg: str = (
            f"ARCHITECT mode restricts file operations to {plans_dir}. "
            f"Switch to CODE mode for unrestricted file access."
        )
        return False, msg

    return True, ""


def is_path_in_plans_dir(path: str, plans_dir: Path) -> bool:
    """Check if path is within plans directory.

    Args:
        path: str - Path to check.
        plans_dir: Path - Plans directory path.

    Returns:
        bool - True if path is within plans directory.

    Raises:
        None
    """

    try:
        resolved_path: Path = Path(path).resolve()
        resolved_plans: Path = plans_dir.resolve()
        return resolved_path.is_relative_to(resolved_plans)
    except (ValueError, OSError):
        return False


__all__: list[str] = [
    "ARCHITECT_MODE",
    "ASK_MODE",
    "CODE_MODE",
    "AgentMode",
    "ModeConfig",
    "get_mode_config",
    "is_path_in_plans_dir",
    "is_tool_allowed",
    "validate_file_path",
]

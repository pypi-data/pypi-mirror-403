"""Mode Management Tools.

LangChain tools for managing agent operational modes.
"""

from typing import Annotated

from langchain_core.tools import tool

from nexus.agent.modes import AgentMode


@tool
def switch_mode(
    target_mode: Annotated[str, "The mode to switch to (CODE, ARCHITECT, or ASK)"],
) -> str:
    """Switch Mode Tool.

    Request to switch the agent's operational mode.
    This allows the agent to move from planning (ARCHITECT) to implementation (CODE)
    or conversation (ASK) when appropriate.

    Args:
        target_mode: str - The specific mode name to transition to.

    Returns:
        str - Transition request message.
    """

    mode_name = target_mode.upper()
    if mode_name not in [m.value for m in AgentMode]:
        return f"Error: Invalid mode '{target_mode}'. Available modes: CODE, ARCHITECT, ASK."

    return f"Requesting transition to {mode_name} mode..."


mode_tools: list = [switch_mode]

__all__: list[str] = ["mode_tools", "switch_mode"]

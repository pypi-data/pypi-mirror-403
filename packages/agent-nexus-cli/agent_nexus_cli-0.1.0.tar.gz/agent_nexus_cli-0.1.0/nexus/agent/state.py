"""State Module.

State definitions for the LangGraph agent.
"""

from typing import Annotated, NotRequired, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Agent State Class.

    State for the coding agent.

    Inherits:
        TypedDict

    Attrs:
        messages: Annotated[list[BaseMessage], add_messages] - Messages list.
        iteration_count: NotRequired[int] - Iteration count.
        working_directory: NotRequired[str] - Working directory.
        tool_calls_made: NotRequired[list[str]] - Tool calls made.
        files_modified: NotRequired[list[str]] - Files modified.
        pending_approval: NotRequired[bool] - Pending approval flag.
        approval_granted: NotRequired[bool] - Approval granted flag.
        current_mode: NotRequired[str] - Current operational mode.
        mode_switch_pending: NotRequired[dict[str, str]] - Pending mode switch.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    iteration_count: NotRequired[int]
    working_directory: NotRequired[str]
    tool_calls_made: NotRequired[list[str]]
    files_modified: NotRequired[list[str]]
    pending_approval: NotRequired[bool]
    approval_granted: NotRequired[bool]
    current_mode: NotRequired[str]
    mode_switch_pending: NotRequired[dict[str, str]]


__all__: list[str] = ["AgentState"]

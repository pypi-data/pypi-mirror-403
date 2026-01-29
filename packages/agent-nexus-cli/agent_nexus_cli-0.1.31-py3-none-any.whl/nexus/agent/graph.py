"""Graph Module.

LangGraph state machine for the agent.
Supports dynamic loading of MCP tools.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from nexus.agent.nodes import approval_node, create_agent_node, should_continue
from nexus.agent.state import AgentState
from nexus.config.settings import settings
from nexus.tools import all_tools
from nexus.tools.mcp import get_mcp_context_prompt, load_mcp_tools


@asynccontextmanager
async def create_agent_graph(checkpointer: Any | None = None) -> AsyncIterator[Any]:
    """Create Agent Graph.

    Create the Compiled LangGraph agent with MCP tool support.
    Must be used as an async context manager.

    Args:
        checkpointer: Any | None - LangGraph checkpointer.

    Yields:
        any - Compiled agent graph.

    Raises:
        None
    """

    llm = ChatOpenAI(
        model=settings.model_name,  # ty:ignore[unknown-argument]
        temperature=settings.temperature,
        api_key=settings.openai_api_key,  # ty:ignore[unknown-argument]
        base_url=settings.openai_base_url,  # ty:ignore[unknown-argument]
    )

    async with load_mcp_tools() as mcp_tools:
        all_available_tools = all_tools + mcp_tools
        mcp_context = get_mcp_context_prompt()

        agent_node = create_agent_node(
            llm,
            all_tools,
            mcp_tools,
            mcp_context=mcp_context,
        )
        tool_node = ToolNode(all_available_tools)

        workflow = StateGraph(AgentState)  # ty:ignore[invalid-argument-type]

        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)

        if settings.approval_required:
            workflow.add_node("approval", approval_node)

        workflow.set_entry_point("agent")

        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "continue": "tools",
                "request_approval": "approval" if settings.approval_required else "tools",
                "end": END,
            },
        )

        workflow.add_edge("tools", "agent")

        if settings.approval_required:
            workflow.add_conditional_edges(
                "approval",
                lambda state: "tools" if state.get("approval_granted") else END,
            )

        yield workflow.compile(checkpointer=checkpointer)


__all__: list[str] = ["create_agent_graph"]

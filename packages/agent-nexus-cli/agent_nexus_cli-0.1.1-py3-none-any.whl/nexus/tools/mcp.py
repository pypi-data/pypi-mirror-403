"""MCP Module.

Functions for loading and managing MCP servers.
"""

import json
import shutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp import StdioServerParameters

from nexus.config.settings import settings
from nexus.ui.console import console

_active_mcp_tool_counts: dict[str, int] = {}
_active_mcp_tools_info: dict[str, list[dict[str, str]]] = {}


def _find_executable(command: str) -> str:
    """Find executable path.

    Resolves the absolute path of a command (e.g., 'npx', 'uv', 'python').

    Args:
        command: str - Command to resolve.

    Returns:
        str - Absolute path to executable.

    Raises:
        FileNotFoundError - If command not found.
    """

    executable = shutil.which(command)
    if not executable:
        if command == "npx":
            executable = shutil.which("npx.cmd")
        elif command == "npm":
            executable = shutil.which("npm.cmd")

    if not executable:
        msg = f"Command '{command}' not found in PATH."
        raise FileNotFoundError(msg)
    return executable


def get_mcp_server_params() -> dict[str, StdioServerParameters]:
    """Get MCP server parameters from config.

    Reads .nexus/mcp_config.json and converts to StdioServerParameters.

    Returns:
        dict[str, StdioServerParameters] - Dictionary of server parameters.

    Raises:
        None
    """

    config_path = settings.mcp_config_path
    if not config_path.exists():
        return {}

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        mcp_servers = data.get("mcpServers", {})

        server_params = {}
        for name, config in mcp_servers.items():
            command = config.get("command")
            args = config.get("args", [])

            if not command:
                continue

            try:
                executable = _find_executable(command)
                server_params[name] = StdioServerParameters(
                    command=executable,
                    args=args,
                    env=config.get("env"),
                )
            except FileNotFoundError:
                continue

    except Exception:  # noqa: BLE001
        return {}

    return server_params


@asynccontextmanager
async def load_mcp_tools() -> AsyncIterator[list[BaseTool]]:
    """Load tools from configured MCP servers.

    Connects to MCP servers defined in configuration and retrieves their tools.
    Use this as an async context manager to ensure proper cleanup.

    Yields:
        list[BaseTool] - List of LangChain-compatible tools.

    Raises:
        None
    """

    _active_mcp_tool_counts.clear()
    _active_mcp_tools_info.clear()

    server_params = get_mcp_server_params()
    if not server_params:
        yield []
        return

    all_tools: list[BaseTool] = []

    clients = []
    try:
        for name, params in server_params.items():
            client_config = {
                name: {
                    "command": params.command,
                    "args": params.args,
                    "transport": "stdio",
                    "env": params.env,
                },
            }

            try:
                client = MultiServerMCPClient(client_config)  # ty:ignore[invalid-argument-type]
                clients.append(client)
                tools = await client.get_tools()

                _active_mcp_tool_counts[name] = len(tools)

                tool_infos = [{"name": t.name, "description": t.description} for t in tools]
                _active_mcp_tools_info[name] = tool_infos

                all_tools.extend(tools)
            except Exception as e:  # noqa: BLE001
                err_msg = str(e)
                if hasattr(e, "exceptions"):
                    sub_errors = [str(sub) for sub in e.exceptions]  # ty:ignore[not-iterable]
                    err_msg = f"{e} -> {sub_errors}"

                cmd_str = f"{client_config[name]['command']} {client_config[name]['args']}"
                console.print(f"[dim red]Error loading MCP {name}: {err_msg}[/dim red]")
                console.print(f"[dim red]Command: {cmd_str}[/dim red]")

                _active_mcp_tool_counts[name] = 0
                continue

        yield all_tools
    finally:
        pass


def get_mcp_status() -> dict[str, Any]:
    """Get MCP configuration status.

    Returns:
        dict[str, Any] - Status details including loaded servers.
    """

    status: dict[str, Any] = {"loaded": 0, "servers": [], "config_found": settings.mcp_config_path.exists()}

    if not status["config_found"]:
        return status

    try:
        data = json.loads(settings.mcp_config_path.read_text(encoding="utf-8"))
        servers = data.get("mcpServers", {})
        status["loaded"] = len(servers)

        for name, config in servers.items():
            tool_count = _active_mcp_tool_counts.get(name, 0)
            status["servers"].append(
                {
                    "name": name,
                    "command": config.get("command", "unknown"),
                    "tools": tool_count,
                },
            )

    except Exception:  # noqa: BLE001
        return status

    return status


def get_mcp_context_prompt() -> str:
    """Get prompt context for MCP tools.

    Returns a formatted string describing available MCP servers and provided tools.

    Returns:
        str - Formatted context string.
    """

    if not _active_mcp_tools_info:
        return ""

    lines = ["\n## Active MCP Servers & Tools\n"]
    for server_name, tools in _active_mcp_tools_info.items():
        if not tools:
            continue

        lines.append(f"### Server: {server_name}")
        lines.extend([f"- **{t['name']}**: {t['description']}" for t in tools])
        lines.append("")

    return "\n".join(lines)


__all__: list[str] = [
    "get_mcp_context_prompt",
    "get_mcp_server_params",
    "get_mcp_status",
    "load_mcp_tools",
]

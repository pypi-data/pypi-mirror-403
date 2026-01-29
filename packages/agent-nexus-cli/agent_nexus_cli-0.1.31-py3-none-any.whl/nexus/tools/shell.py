"""Shell Tools.

LangChain tools for shell command execution.
"""

import shlex
import subprocess
from typing import Annotated

from langchain_core.tools import tool


@tool
async def execute_shell_command(
    command: Annotated[str, "Shell command to execute"],
    timeout: Annotated[int, "Timeout in seconds"] = 30,  # noqa: ASYNC109
) -> str:
    """Execute Shell Command.

    Execute a shell command and return its output.

    IMPORTANT: This tool does NOT support shell redirections (like '>', '>>'),
    pipes ('|'), or command chaining (';', '&&'). For file creation or
    modification, ALWAYS use the 'write_file' or 'edit_file' tools.

    Args:
        command: str - Shell command to execute.
        timeout: int - Timeout in seconds.

    Returns:
        str - Command output or error message.

    Raises:
        None
    """

    try:
        dangerous_patterns: list[str] = ["rm -rf /", ":(){ :|:& };:", "mkfs"]
        if any(pattern in command for pattern in dangerous_patterns):
            return "Error: Command contains dangerous pattern and was blocked"

        result: subprocess.CompletedProcess = subprocess.run(  # noqa: ASYNC221, S603
            shlex.split(command),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        output: list[str] = []
        max_output: int = 2048

        if result.stdout:
            stdout: str = result.stdout
            if len(stdout) > max_output:
                stdout = f"{stdout[:max_output]}... (truncated)"
            output.append(f"STDOUT:\n{stdout}")

        if result.stderr:
            stderr: str = result.stderr
            if len(stderr) > max_output:
                stderr = f"{stderr[:max_output]}... (truncated)"
            output.append(f"STDERR:\n{stderr}")

        output.append(f"Exit Code: {result.returncode}")

        return "\n\n".join(output)

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:  # noqa: BLE001
        return f"Error executing command: {e!s}"


shell_tools: list = [execute_shell_command]


__all__: list[str] = ["execute_shell_command", "shell_tools"]

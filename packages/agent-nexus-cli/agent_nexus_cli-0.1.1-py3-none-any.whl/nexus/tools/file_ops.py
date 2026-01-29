"""File Operations Tools.

LangChain tools for file operations.
"""

from collections.abc import Iterable
from pathlib import Path
from typing import Annotated

import pathspec
from langchain_core.tools import tool


def _get_gitignore_spec(dir_path: Path) -> tuple[Path, pathspec.PathSpec | None]:
    """Get gitignore patterns and project root.

    Args:
        dir_path: Path - Starting directory for search.

    Returns:
        tuple[Path, pathspec.PathSpec | None] - Root path and pathspec object.

    Raises:
        None
    """

    root_path: Path = dir_path
    while root_path.parent != root_path:
        if (root_path / ".git").exists() or (root_path / ".gitignore").exists():
            break
        root_path = root_path.parent

    gitignore_path: Path = root_path / ".gitignore"
    if gitignore_path.exists():
        with gitignore_path.open("r", encoding="utf-8") as f:
            return root_path, pathspec.PathSpec.from_lines("gitwildmatch", f.read().splitlines())
    return root_path, None


def _is_ignored(p: Path, root_path: Path, spec: pathspec.PathSpec | None) -> bool:
    """Check if a path should be ignored based on gitignore.

    Args:
        p: Path - Path to check.
        root_path: Path - Project root path.
        spec: pathspec.PathSpec | None - Gitignore spec.

    Returns:
        bool - True if ignored.

    Raises:
        None
    """

    if ".git" in p.parts:
        return True

    if spec:
        try:
            git_rel_path: Path = p.relative_to(root_path)
            git_rel_str: str = git_rel_path.as_posix()
            if p.is_dir():
                git_rel_str = f"{git_rel_str}/"
            return spec.match_file(git_rel_str)
        except ValueError:
            return False
    return False


def _collect_items(
    all_paths: Iterable[Path],
    dir_path: Path,
    root_path: Path,
    spec: pathspec.PathSpec | None,
) -> list[str]:
    """Collect directory items while respecting ignore rules.

    Args:
        all_paths: Iterable[Path] - Paths to process.
        dir_path: Path - Parent directory path.
        root_path: Path - Project root path.
        spec: pathspec.PathSpec | None - Gitignore spec.

    Returns:
        list[str] - List of formatted relative paths.

    Raises:
        None
    """

    items: list[str] = []
    for p in all_paths:
        if _is_ignored(p, root_path, spec):
            continue

        rel_path: Path = p.relative_to(dir_path)
        rel_str: str = rel_path.as_posix()

        if p.is_dir():
            items.append(f"{rel_str}/")
        else:
            items.append(rel_str)
    return items


def _format_listing(items: list[str]) -> str:
    """Format and cap directory listing output.

    Args:
        items: list[str] - Collected items.

    Returns:
        str - Formatted listing.

    Raises:
        None
    """

    if not items:
        return "Directory is empty (or all files are ignored)"

    items.sort()
    max_items: int = 500
    max_chars: int = 32768

    result_items: list[str] = items[:max_items]
    result: str = "\n".join(result_items)

    if len(items) > max_items or len(result) > max_chars:
        if len(result) > max_chars:
            result = result[:max_chars] + "... (truncated due to length)"

        summary: list[str] = []
        if len(items) > max_items:
            summary.append(f"{len(items) - max_items} more items")

        return f"{result}\n\n... and {', '.join(summary)} (output capped to prevent context overflow)"

    return result


@tool
def read_file(
    path: Annotated[str, "Path to the file to read"],
    start_line: Annotated[int | None, "Starting line number (1-indexed)"] = None,
    end_line: Annotated[int | None, "Ending line number (inclusive)"] = None,
) -> str:
    """Read File.

    Read contents of a file, optionally specifying line range.

    Args:
        path: str - Path to file.
        start_line: int | None - Starting line number.
        end_line: int | None - Ending line number.

    Returns:
        str - File contents or error message.

    Raises:
        None
    """

    try:
        file_path: Path = Path(path)

        if not file_path.exists():
            return f"Error: File '{path}' does not exist"

        if not file_path.is_file():
            return f"Error: '{path}' is not a file"

        with Path(file_path).open("r", encoding="utf-8") as f:
            if start_line is None and end_line is None:
                content: str = f.read()
            else:
                lines: list[str] = f.readlines()
                start: int = (start_line - 1) if start_line else 0
                end: int = end_line if end_line else len(lines)
                content = "".join(lines[start:end])

    except Exception as e:  # noqa: BLE001
        return f"Error reading file: {e!s}"

    else:
        return content


@tool
def write_file(
    path: Annotated[str, "Path to the file to write"],
    content: Annotated[str, "Content to write to the file"],
    *,
    create_dirs: Annotated[bool, "Create parent directories if they don't exist"] = True,
) -> str:
    """Write File.

    Write content to a file, creating it if it doesn't exist.

    Args:
        path: str - Path to file.
        content: str - Content to write.
        create_dirs: bool - Create parent directories.

    Returns:
        str - Success message or error message.

    Raises:
        None
    """

    try:
        file_path: Path = Path(path)

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        with Path(file_path).open("w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully wrote {len(content)} characters to '{path}'"

    except Exception as e:  # noqa: BLE001
        return f"Error writing file: {e!s}"


@tool
def list_directory(
    path: Annotated[str, "Directory path"] = ".",
    *,
    recursive: Annotated[bool, "Recursive"] = False,
    include_gitignored: Annotated[bool, "Include ignored"] = False,
) -> str:
    """List directory contents, respecting .gitignore.

    Args:
        path: str - Directory path.
        recursive: bool - Recursive search.
        include_gitignored: bool - Include gitignored files.

    Returns:
        str - Directory listing or error message.

    Raises:
        None
    """

    try:
        dir_path: Path = Path(path).absolute()

        if not dir_path.exists():
            return f"Error: Directory '{path}' does not exist"

        if not dir_path.is_dir():
            return f"Error: '{path}' is not a directory"

        if not include_gitignored:
            root_path, spec = _get_gitignore_spec(dir_path)
        else:
            root_path, spec = dir_path, None

        all_paths = dir_path.rglob("*") if recursive else dir_path.iterdir()
        items: list[str] = _collect_items(all_paths, dir_path, root_path, spec)
        result: str = _format_listing(items)

    except Exception as e:  # noqa: BLE001
        return f"Error listing directory: {e!s}"

    else:
        return result


file_tools: list = [read_file, write_file, list_directory]


__all__: list[str] = ["file_tools", "list_directory", "read_file", "write_file"]

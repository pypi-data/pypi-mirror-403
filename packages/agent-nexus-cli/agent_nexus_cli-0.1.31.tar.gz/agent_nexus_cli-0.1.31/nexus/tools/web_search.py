"""Web Search Tools.

LangChain tools for web search functionality using DDGS.
"""

from typing import Annotated

from ddgs import DDGS
from langchain_core.tools import tool


@tool
def web_search(
    query: Annotated[str, "Search query to execute"],
    max_results: Annotated[int, "Maximum number of results to return"] = 5,
) -> str:
    """Web Search.

    Execute a web search using DuckDuckGo and return formatted results.

    Args:
        query: str - The search query string.
        max_results: int - Maximum number of results to return (default: 5).

    Returns:
        str - Formatted search results or error message.

    Raises:
        None
    """

    try:
        results: list[str] = []
        with DDGS() as ddgs:
            search_results = ddgs.text(
                query,
                max_results=max_results,
            )

            for index, result in enumerate(search_results, start=1):
                title = result.get("title", "No Title")
                href = result.get("href", "No URL")
                body = result.get("body", "No Description")
                results.append(f"{index}. {title}\n   URL: {href}\n   {body}\n")

        if not results:
            return "No results found."

        return "\n".join(results)

    except Exception as e:  # noqa: BLE001
        return f"Error performing web search: {e!s}"


search_tools: list = [web_search]


__all__: list[str] = ["search_tools", "web_search"]

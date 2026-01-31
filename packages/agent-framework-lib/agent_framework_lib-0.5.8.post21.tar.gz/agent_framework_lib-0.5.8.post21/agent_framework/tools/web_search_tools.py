"""
Web Search Tools

Tools for performing web searches using DuckDuckGo.
No API key required - uses the free DuckDuckGo search API.
"""

import logging
from typing import Any, Callable

from .base import AgentTool

logger = logging.getLogger(__name__)


class WebSearchTool(AgentTool):
    """
    Tool for performing web searches using DuckDuckGo.

    This tool allows agents to search the web for information. It uses the duckduckgo-search library.

    Features:
    - Free web search
    - Returns relevant snippets and URLs
    - Configurable number of results
    """

    def __init__(self, max_results: int = 5):
        """
        Initialize the web search tool.

        Args:
            max_results: Maximum number of search results to return (default: 5)
        """
        super().__init__()
        self.max_results = max_results

    def get_tool_function(self) -> Callable[..., Any]:
        """Return the web search function."""

        def web_search(query: str, max_results: int | None = None) -> str:
            """
            Search the web using DuckDuckGo.

            Use this tool to find current information from the internet.
            Returns titles, snippets, and URLs of relevant web pages.

            Args:
                query: The search query to look up
                max_results: Maximum number of results (default: 5, max: 10)

            Returns:
                Formatted search results with titles, snippets, and URLs
            """
            try:
                from ddgs import DDGS
            except ImportError:
                return (
                    "Web search is not available. "
                    "Install with: uv add ddgs"
                )

            num_results = min(max_results or self.max_results, 10)

            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=num_results))

                if not results:
                    return f"No results found for: {query}"

                formatted_results = []
                for i, result in enumerate(results, 1):
                    title = result.get("title", "No title")
                    body = result.get("body", "No description")
                    href = result.get("href", "")
                    formatted_results.append(
                        f"{i}. **{title}**\n   {body}\n   URL: {href}"
                    )

                return f"Search results for '{query}':\n\n" + "\n\n".join(formatted_results)

            except Exception as e:
                logger.error(f"Web search error: {e}")
                return f"Search failed: {e}"

        return web_search

    def get_tool_info(self) -> dict[str, Any]:
        """Get metadata about this tool."""
        return {
            "name": self.__class__.__name__,
            "description": "Search the web using DuckDuckGo (free, no API key)",
            "requires_file_storage": False,
            "requires_user_context": False,
        }


class WebNewsSearchTool(AgentTool):
    """
    Tool for searching news articles using DuckDuckGo News.

    This tool allows agents to search for recent news articles without
    requiring any API keys.
    """

    def __init__(self, max_results: int = 5):
        """
        Initialize the news search tool.

        Args:
            max_results: Maximum number of news results to return (default: 5)
        """
        super().__init__()
        self.max_results = max_results

    def get_tool_function(self) -> Callable[..., Any]:
        """Return the news search function."""

        def news_search(query: str, max_results: int | None = None) -> str:
            """
            Search for recent news articles using DuckDuckGo News.

            Use this tool to find current news and recent articles on a topic.

            Args:
                query: The news topic to search for
                max_results: Maximum number of results (default: 5, max: 10)

            Returns:
                Formatted news results with titles, dates, sources, and URLs
            """
            try:
                from ddgs import DDGS
            except ImportError:
                return (
                    "News search is not available. "
                    "Install with: uv add ddgs"
                )

            num_results = min(max_results or self.max_results, 10)

            try:
                with DDGS() as ddgs:
                    results = list(ddgs.news(query, max_results=num_results))

                if not results:
                    return f"No news found for: {query}"

                formatted_results = []
                for i, result in enumerate(results, 1):
                    title = result.get("title", "No title")
                    body = result.get("body", "No description")
                    source = result.get("source", "Unknown source")
                    date = result.get("date", "")
                    url = result.get("url", "")
                    formatted_results.append(
                        f"{i}. **{title}**\n"
                        f"   Source: {source} | Date: {date}\n"
                        f"   {body}\n"
                        f"   URL: {url}"
                    )

                return f"News results for '{query}':\n\n" + "\n\n".join(formatted_results)

            except Exception as e:
                logger.error(f"News search error: {e}")
                return f"News search failed: {e}"

        return news_search

    def get_tool_info(self) -> dict[str, Any]:
        """Get metadata about this tool."""
        return {
            "name": self.__class__.__name__,
            "description": "Search news articles using DuckDuckGo News (free, no API key)",
            "requires_file_storage": False,
            "requires_user_context": False,
        }


__all__ = [
    "WebSearchTool",
    "WebNewsSearchTool",
]

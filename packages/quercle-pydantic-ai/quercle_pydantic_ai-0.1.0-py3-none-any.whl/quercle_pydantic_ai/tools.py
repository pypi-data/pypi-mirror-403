"""Quercle tools for Pydantic AI agents."""

from __future__ import annotations

from typing import Any

from pydantic_ai.tools import Tool
from pydantic_ai.toolsets import FunctionToolset
from quercle import (
    FETCH_PROMPT_DESCRIPTION,
    FETCH_TOOL_DESCRIPTION,
    FETCH_URL_DESCRIPTION,
    SEARCH_QUERY_DESCRIPTION,
    SEARCH_TOOL_DESCRIPTION,
    AsyncQuercleClient,
)


def quercle_search_tool(
    api_key: str | None = None,
    allowed_domains: list[str] | None = None,
    blocked_domains: list[str] | None = None,
    timeout: float | None = None,
) -> Tool[Any]:
    """Create a Quercle web search tool for Pydantic AI agents.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        allowed_domains: Only include results from these domains.
        blocked_domains: Exclude results from these domains.
        timeout: Request timeout in seconds.

    Returns:
        A Pydantic AI Tool configured for web search.
    """
    client: AsyncQuercleClient | None = None

    async def quercle_search(query: str) -> str:
        nonlocal client
        if client is None:
            client = AsyncQuercleClient(api_key=api_key, timeout=timeout)
        return await client.search(
            query,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
        )

    # Set docstring dynamically using imported descriptions
    quercle_search.__doc__ = f"""Search the web and get AI-synthesized answers with citations.

    Args:
        query: {SEARCH_QUERY_DESCRIPTION}

    Returns:
        AI-synthesized answer with source citations.
    """

    return Tool(
        quercle_search,
        name="quercle_search",
        description=SEARCH_TOOL_DESCRIPTION,
        takes_ctx=False,
    )


def quercle_fetch_tool(
    api_key: str | None = None,
    timeout: float | None = None,
) -> Tool[Any]:
    """Create a Quercle URL fetch tool for Pydantic AI agents.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        timeout: Request timeout in seconds.

    Returns:
        A Pydantic AI Tool configured for URL fetching.
    """
    client: AsyncQuercleClient | None = None

    async def quercle_fetch(url: str, prompt: str) -> str:
        nonlocal client
        if client is None:
            client = AsyncQuercleClient(api_key=api_key, timeout=timeout)
        return await client.fetch(url=url, prompt=prompt)

    # Set docstring dynamically using imported descriptions
    quercle_fetch.__doc__ = f"""Fetch a URL and analyze its content with AI.

    Args:
        url: {FETCH_URL_DESCRIPTION}
        prompt: {FETCH_PROMPT_DESCRIPTION}

    Returns:
        AI-processed analysis of the page content.
    """

    return Tool(
        quercle_fetch,
        name="quercle_fetch",
        description=FETCH_TOOL_DESCRIPTION,
        takes_ctx=False,
    )


def quercle_tools(
    api_key: str | None = None,
    timeout: float | None = None,
) -> list[Tool[Any]]:
    """Create both Quercle search and fetch tools for Pydantic AI agents.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        timeout: Request timeout in seconds.

    Returns:
        A list containing the search and fetch tools.
    """
    return [
        quercle_search_tool(api_key=api_key, timeout=timeout),
        quercle_fetch_tool(api_key=api_key, timeout=timeout),
    ]


class QuercleToolset(FunctionToolset):
    """A Pydantic AI toolset providing Quercle web search and URL fetch capabilities.

    This toolset can be composed with other toolsets using Pydantic AI's
    CombinedToolset or passed directly to agents.

    Example:
        >>> from pydantic_ai import Agent
        >>> from pydantic_ai_quercle import QuercleToolset
        >>> toolset = QuercleToolset()
        >>> agent = Agent('openai:gpt-4o', toolsets=[toolset])
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float | None = None,
        *,
        include_search: bool = True,
        include_fetch: bool = True,
        search_allowed_domains: list[str] | None = None,
        search_blocked_domains: list[str] | None = None,
    ):
        """Initialize the Quercle toolset.

        Args:
            api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
            timeout: Request timeout in seconds.
            include_search: Include the web search tool (default: True).
            include_fetch: Include the URL fetch tool (default: True).
            search_allowed_domains: Only include search results from these domains.
            search_blocked_domains: Exclude search results from these domains.
        """
        tools: list[Tool[Any]] = []

        if include_search:
            tools.append(
                quercle_search_tool(
                    api_key=api_key,
                    allowed_domains=search_allowed_domains,
                    blocked_domains=search_blocked_domains,
                    timeout=timeout,
                )
            )

        if include_fetch:
            tools.append(quercle_fetch_tool(api_key=api_key, timeout=timeout))

        super().__init__(tools=tools)

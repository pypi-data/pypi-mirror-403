"""Google ADK tools for Quercle web search and URL fetching."""

from google_adk_quercle.tools import (
    # Async tools (recommended for Google ADK)
    async_quercle_fetch,
    async_quercle_search,
    create_async_quercle_fetch,
    create_async_quercle_search,
    # Sync tools
    create_quercle_fetch,
    create_quercle_search,
    get_async_quercle_tools,
    get_quercle_tools,
    quercle_fetch,
    quercle_search,
)

__all__ = [
    # Async tools (recommended for Google ADK)
    "async_quercle_fetch",
    "async_quercle_search",
    "create_async_quercle_fetch",
    "create_async_quercle_search",
    "get_async_quercle_tools",
    # Sync tools
    "quercle_fetch",
    "quercle_search",
    "create_quercle_fetch",
    "create_quercle_search",
    "get_quercle_tools",
]

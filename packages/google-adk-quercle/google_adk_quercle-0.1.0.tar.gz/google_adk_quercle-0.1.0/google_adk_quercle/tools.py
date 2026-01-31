"""Google ADK tools for Quercle web search and URL fetching."""

from __future__ import annotations

from typing import Callable, Coroutine

from quercle import (
    FETCH_PROMPT_DESCRIPTION,
    FETCH_TOOL_DESCRIPTION,
    FETCH_URL_DESCRIPTION,
    SEARCH_ALLOWED_DOMAINS_DESCRIPTION,
    SEARCH_BLOCKED_DOMAINS_DESCRIPTION,
    SEARCH_QUERY_DESCRIPTION,
    SEARCH_TOOL_DESCRIPTION,
    AsyncQuercleClient,
    QuercleClient,
)

# Build docstrings from quercle SDK descriptions (DRY)
_FETCH_DOCSTRING = f"""{FETCH_TOOL_DESCRIPTION}

    Args:
        url: {FETCH_URL_DESCRIPTION}
        prompt: {FETCH_PROMPT_DESCRIPTION}

    Returns:
        The AI-processed result from the fetched content.
    """

_SEARCH_DOCSTRING = f"""{SEARCH_TOOL_DESCRIPTION}

    Args:
        query: {SEARCH_QUERY_DESCRIPTION}
        allowed_domains: {SEARCH_ALLOWED_DOMAINS_DESCRIPTION}
        blocked_domains: {SEARCH_BLOCKED_DOMAINS_DESCRIPTION}

    Returns:
        AI-synthesized answer based on search results.
    """

# Module-level default clients (lazy initialized)
_default_client: QuercleClient | None = None
_default_async_client: AsyncQuercleClient | None = None


def _get_default_client() -> QuercleClient:
    """Get or create the default sync Quercle client."""
    global _default_client
    if _default_client is None:
        _default_client = QuercleClient()
    return _default_client


def _get_default_async_client() -> AsyncQuercleClient:
    """Get or create the default async Quercle client."""
    global _default_async_client
    if _default_async_client is None:
        _default_async_client = AsyncQuercleClient()
    return _default_async_client


# =============================================================================
# Sync Tools
# =============================================================================


def quercle_fetch(url: str, prompt: str) -> str:
    return _get_default_client().fetch(url=url, prompt=prompt)


quercle_fetch.__doc__ = _FETCH_DOCSTRING


def quercle_search(
    query: str,
    allowed_domains: list[str] | None = None,
    blocked_domains: list[str] | None = None,
) -> str:
    return _get_default_client().search(
        query,
        allowed_domains=allowed_domains,
        blocked_domains=blocked_domains,
    )


quercle_search.__doc__ = _SEARCH_DOCSTRING


# =============================================================================
# Async Tools
# =============================================================================


async def async_quercle_fetch(url: str, prompt: str) -> str:
    return await _get_default_async_client().fetch(url=url, prompt=prompt)


async_quercle_fetch.__doc__ = _FETCH_DOCSTRING


async def async_quercle_search(
    query: str,
    allowed_domains: list[str] | None = None,
    blocked_domains: list[str] | None = None,
) -> str:
    return await _get_default_async_client().search(
        query,
        allowed_domains=allowed_domains,
        blocked_domains=blocked_domains,
    )


async_quercle_search.__doc__ = _SEARCH_DOCSTRING


# =============================================================================
# Sync Factory Functions
# =============================================================================


def create_quercle_fetch(
    api_key: str | None = None,
    timeout: float = 120.0,
) -> Callable[[str, str], str]:
    """Create a quercle_fetch tool with custom configuration.

    Use this factory function when you need to customize the API key or timeout
    settings for the fetch tool.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        timeout: Request timeout in seconds. Defaults to 120.0.

    Returns:
        A quercle_fetch function configured with the specified settings.
    """
    client = QuercleClient(api_key=api_key, timeout=timeout)

    def quercle_fetch(url: str, prompt: str) -> str:
        return client.fetch(url=url, prompt=prompt)

    quercle_fetch.__doc__ = _FETCH_DOCSTRING
    return quercle_fetch


def create_quercle_search(
    api_key: str | None = None,
    timeout: float = 120.0,
) -> Callable[[str, list[str] | None, list[str] | None], str]:
    """Create a quercle_search tool with custom configuration.

    Use this factory function when you need to customize the API key or timeout
    settings for the search tool.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        timeout: Request timeout in seconds. Defaults to 120.0.

    Returns:
        A quercle_search function configured with the specified settings.
    """
    client = QuercleClient(api_key=api_key, timeout=timeout)

    def quercle_search(
        query: str,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
    ) -> str:
        return client.search(
            query,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
        )

    quercle_search.__doc__ = _SEARCH_DOCSTRING
    return quercle_search


def get_quercle_tools(
    api_key: str | None = None,
    timeout: float = 120.0,
) -> list[Callable]:
    """Get all sync Quercle tools configured with the specified settings.

    This is a convenience function that returns both quercle_fetch and
    quercle_search tools configured with the same settings.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        timeout: Request timeout in seconds. Defaults to 120.0.

    Returns:
        A list containing quercle_fetch and quercle_search functions.
    """
    return [
        create_quercle_fetch(api_key=api_key, timeout=timeout),
        create_quercle_search(api_key=api_key, timeout=timeout),
    ]


# =============================================================================
# Async Factory Functions
# =============================================================================


def create_async_quercle_fetch(
    api_key: str | None = None,
    timeout: float = 120.0,
) -> Callable[[str, str], Coroutine[None, None, str]]:
    """Create an async quercle_fetch tool with custom configuration.

    Use this factory function when you need to customize the API key or timeout
    settings for the async fetch tool.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        timeout: Request timeout in seconds. Defaults to 120.0.

    Returns:
        An async quercle_fetch function configured with the specified settings.
    """
    client = AsyncQuercleClient(api_key=api_key, timeout=timeout)

    async def async_quercle_fetch(url: str, prompt: str) -> str:
        return await client.fetch(url=url, prompt=prompt)

    async_quercle_fetch.__doc__ = _FETCH_DOCSTRING
    return async_quercle_fetch


def create_async_quercle_search(
    api_key: str | None = None,
    timeout: float = 120.0,
) -> Callable[[str, list[str] | None, list[str] | None], Coroutine[None, None, str]]:
    """Create an async quercle_search tool with custom configuration.

    Use this factory function when you need to customize the API key or timeout
    settings for the async search tool.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        timeout: Request timeout in seconds. Defaults to 120.0.

    Returns:
        An async quercle_search function configured with the specified settings.
    """
    client = AsyncQuercleClient(api_key=api_key, timeout=timeout)

    async def async_quercle_search(
        query: str,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
    ) -> str:
        return await client.search(
            query,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
        )

    async_quercle_search.__doc__ = _SEARCH_DOCSTRING
    return async_quercle_search


def get_async_quercle_tools(
    api_key: str | None = None,
    timeout: float = 120.0,
) -> list[Callable]:
    """Get all async Quercle tools configured with the specified settings.

    This is a convenience function that returns both async_quercle_fetch and
    async_quercle_search tools configured with the same settings. Use these
    for optimal performance with Google ADK's async runners.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        timeout: Request timeout in seconds. Defaults to 120.0.

    Returns:
        A list containing async_quercle_fetch and async_quercle_search functions.
    """
    return [
        create_async_quercle_fetch(api_key=api_key, timeout=timeout),
        create_async_quercle_search(api_key=api_key, timeout=timeout),
    ]

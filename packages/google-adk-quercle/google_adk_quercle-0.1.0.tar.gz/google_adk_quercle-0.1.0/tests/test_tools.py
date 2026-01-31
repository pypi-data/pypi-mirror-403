"""Tests for Quercle Google ADK tools."""

import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from google_adk_quercle import (
    async_quercle_fetch,
    async_quercle_search,
    create_async_quercle_fetch,
    create_async_quercle_search,
    create_quercle_fetch,
    create_quercle_search,
    get_async_quercle_tools,
    get_quercle_tools,
    quercle_fetch,
    quercle_search,
)

# =============================================================================
# Sync Tool Tests
# =============================================================================


class TestQuercleFetch:
    """Tests for quercle_fetch function."""

    def test_has_correct_signature(self):
        """Test that quercle_fetch has the correct function signature."""
        sig = inspect.signature(quercle_fetch)
        params = list(sig.parameters.keys())
        assert params == ["url", "prompt"]

        annotations = quercle_fetch.__annotations__
        assert "url" in annotations
        assert "prompt" in annotations
        assert "return" in annotations

    def test_has_docstring(self):
        """Test that quercle_fetch has a docstring for ADK schema generation."""
        assert quercle_fetch.__doc__ is not None
        assert len(quercle_fetch.__doc__) > 0
        assert "url" in quercle_fetch.__doc__.lower()
        assert "prompt" in quercle_fetch.__doc__.lower()

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_fetch_execution(self, mock_client_class):
        """Test that quercle_fetch calls the client correctly."""
        import google_adk_quercle.tools as tools_module

        tools_module._default_client = None

        mock_client = MagicMock()
        mock_client.fetch.return_value = "Processed content"
        mock_client_class.return_value = mock_client

        result = quercle_fetch(url="https://example.com", prompt="Summarize this")

        assert result == "Processed content"
        mock_client.fetch.assert_called_once_with(
            url="https://example.com",
            prompt="Summarize this",
        )


class TestQuercleSearch:
    """Tests for quercle_search function."""

    def test_has_correct_signature(self):
        """Test that quercle_search has the correct function signature."""
        sig = inspect.signature(quercle_search)
        params = list(sig.parameters.keys())
        assert params == ["query", "allowed_domains", "blocked_domains"]

        annotations = quercle_search.__annotations__
        assert "query" in annotations
        assert "return" in annotations

    def test_has_docstring(self):
        """Test that quercle_search has a docstring for ADK schema generation."""
        assert quercle_search.__doc__ is not None
        assert len(quercle_search.__doc__) > 0
        assert "query" in quercle_search.__doc__.lower()
        assert "search" in quercle_search.__doc__.lower()

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_search_basic(self, mock_client_class):
        """Test basic search execution."""
        import google_adk_quercle.tools as tools_module

        tools_module._default_client = None

        mock_client = MagicMock()
        mock_client.search.return_value = "Search results"
        mock_client_class.return_value = mock_client

        result = quercle_search(query="What is Python?")

        assert result == "Search results"
        mock_client.search.assert_called_once_with(
            "What is Python?",
            allowed_domains=None,
            blocked_domains=None,
        )

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_search_with_domain_filters(self, mock_client_class):
        """Test search with domain filtering."""
        import google_adk_quercle.tools as tools_module

        tools_module._default_client = None

        mock_client = MagicMock()
        mock_client.search.return_value = "Filtered results"
        mock_client_class.return_value = mock_client

        result = quercle_search(
            query="TypeScript tutorial",
            allowed_domains=["*.org", "*.edu"],
            blocked_domains=["spam.com"],
        )

        assert result == "Filtered results"
        mock_client.search.assert_called_once_with(
            "TypeScript tutorial",
            allowed_domains=["*.org", "*.edu"],
            blocked_domains=["spam.com"],
        )


class TestCreateQuercleFetch:
    """Tests for create_quercle_fetch factory function."""

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_returns_callable(self, mock_client_class):
        """Test that factory returns a callable."""
        mock_client_class.return_value = MagicMock()
        fetch_fn = create_quercle_fetch()
        assert callable(fetch_fn)

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_custom_api_key(self, mock_client_class):
        """Test that custom api_key is passed to client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        create_quercle_fetch(api_key="qk_custom_key")

        mock_client_class.assert_called_once_with(api_key="qk_custom_key", timeout=120.0)

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_custom_timeout(self, mock_client_class):
        """Test that custom timeout is passed to client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        create_quercle_fetch(timeout=60.0)

        mock_client_class.assert_called_once_with(api_key=None, timeout=60.0)

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_created_function_has_docstring(self, mock_client_class):
        """Test that created function has docstring for ADK."""
        mock_client_class.return_value = MagicMock()

        fetch_fn = create_quercle_fetch()

        assert fetch_fn.__doc__ is not None
        assert "url" in fetch_fn.__doc__.lower()

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_created_function_executes(self, mock_client_class):
        """Test that created function executes correctly."""
        mock_client = MagicMock()
        mock_client.fetch.return_value = "Custom fetch result"
        mock_client_class.return_value = mock_client

        fetch_fn = create_quercle_fetch(api_key="qk_test")
        result = fetch_fn("https://example.com", "Extract data")

        assert result == "Custom fetch result"
        mock_client.fetch.assert_called_once_with(
            url="https://example.com",
            prompt="Extract data",
        )


class TestCreateQuercleSearch:
    """Tests for create_quercle_search factory function."""

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_returns_callable(self, mock_client_class):
        """Test that factory returns a callable."""
        mock_client_class.return_value = MagicMock()
        search_fn = create_quercle_search()
        assert callable(search_fn)

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_custom_api_key(self, mock_client_class):
        """Test that custom api_key is passed to client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        create_quercle_search(api_key="qk_custom_key")

        mock_client_class.assert_called_once_with(api_key="qk_custom_key", timeout=120.0)

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_custom_timeout(self, mock_client_class):
        """Test that custom timeout is passed to client."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        create_quercle_search(timeout=30.0)

        mock_client_class.assert_called_once_with(api_key=None, timeout=30.0)

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_created_function_has_docstring(self, mock_client_class):
        """Test that created function has docstring for ADK."""
        mock_client_class.return_value = MagicMock()

        search_fn = create_quercle_search()

        assert search_fn.__doc__ is not None
        assert "query" in search_fn.__doc__.lower()

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_created_function_executes(self, mock_client_class):
        """Test that created function executes correctly."""
        mock_client = MagicMock()
        mock_client.search.return_value = "Custom search result"
        mock_client_class.return_value = mock_client

        search_fn = create_quercle_search(api_key="qk_test")
        result = search_fn("test query", None, None)

        assert result == "Custom search result"
        mock_client.search.assert_called_once_with(
            "test query",
            allowed_domains=None,
            blocked_domains=None,
        )


class TestGetQuercleTools:
    """Tests for get_quercle_tools convenience function."""

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_returns_list_of_two_callables(self, mock_client_class):
        """Test that get_quercle_tools returns a list of 2 callables."""
        mock_client_class.return_value = MagicMock()

        tools = get_quercle_tools()

        assert isinstance(tools, list)
        assert len(tools) == 2
        assert all(callable(tool) for tool in tools)

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_tools_have_docstrings(self, mock_client_class):
        """Test that all returned tools have docstrings."""
        mock_client_class.return_value = MagicMock()

        tools = get_quercle_tools()

        for tool in tools:
            assert tool.__doc__ is not None
            assert len(tool.__doc__) > 0

    @patch("google_adk_quercle.tools.QuercleClient")
    def test_passes_configuration(self, mock_client_class):
        """Test that api_key and timeout are passed to both tools."""
        mock_client_class.return_value = MagicMock()

        get_quercle_tools(api_key="qk_shared_key", timeout=90.0)

        assert mock_client_class.call_count == 2
        for call in mock_client_class.call_args_list:
            assert call.kwargs["api_key"] == "qk_shared_key"
            assert call.kwargs["timeout"] == 90.0


# =============================================================================
# Async Tool Tests
# =============================================================================


class TestAsyncQuercleFetch:
    """Tests for async_quercle_fetch function."""

    def test_is_coroutine_function(self):
        """Test that async_quercle_fetch is an async function."""
        assert asyncio.iscoroutinefunction(async_quercle_fetch)

    def test_has_correct_signature(self):
        """Test that async_quercle_fetch has the correct function signature."""
        sig = inspect.signature(async_quercle_fetch)
        params = list(sig.parameters.keys())
        assert params == ["url", "prompt"]

    def test_has_docstring(self):
        """Test that async_quercle_fetch has a docstring for ADK schema generation."""
        assert async_quercle_fetch.__doc__ is not None
        assert len(async_quercle_fetch.__doc__) > 0
        assert "url" in async_quercle_fetch.__doc__.lower()

    @pytest.mark.asyncio
    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    async def test_fetch_execution(self, mock_client_class):
        """Test that async_quercle_fetch calls the client correctly."""
        import google_adk_quercle.tools as tools_module

        tools_module._default_async_client = None

        mock_client = AsyncMock()
        mock_client.fetch.return_value = "Async processed content"
        mock_client_class.return_value = mock_client

        result = await async_quercle_fetch(url="https://example.com", prompt="Summarize")

        assert result == "Async processed content"
        mock_client.fetch.assert_called_once_with(
            url="https://example.com",
            prompt="Summarize",
        )


class TestAsyncQuercleSearch:
    """Tests for async_quercle_search function."""

    def test_is_coroutine_function(self):
        """Test that async_quercle_search is an async function."""
        assert asyncio.iscoroutinefunction(async_quercle_search)

    def test_has_correct_signature(self):
        """Test that async_quercle_search has the correct function signature."""
        sig = inspect.signature(async_quercle_search)
        params = list(sig.parameters.keys())
        assert params == ["query", "allowed_domains", "blocked_domains"]

    def test_has_docstring(self):
        """Test that async_quercle_search has a docstring for ADK schema generation."""
        assert async_quercle_search.__doc__ is not None
        assert len(async_quercle_search.__doc__) > 0
        assert "query" in async_quercle_search.__doc__.lower()

    @pytest.mark.asyncio
    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    async def test_search_execution(self, mock_client_class):
        """Test that async_quercle_search calls the client correctly."""
        import google_adk_quercle.tools as tools_module

        tools_module._default_async_client = None

        mock_client = AsyncMock()
        mock_client.search.return_value = "Async search results"
        mock_client_class.return_value = mock_client

        result = await async_quercle_search(query="What is Python?")

        assert result == "Async search results"
        mock_client.search.assert_called_once_with(
            "What is Python?",
            allowed_domains=None,
            blocked_domains=None,
        )


class TestCreateAsyncQuercleFetch:
    """Tests for create_async_quercle_fetch factory function."""

    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    def test_returns_coroutine_function(self, mock_client_class):
        """Test that factory returns a coroutine function."""
        mock_client_class.return_value = AsyncMock()
        fetch_fn = create_async_quercle_fetch()
        assert asyncio.iscoroutinefunction(fetch_fn)

    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    def test_custom_api_key(self, mock_client_class):
        """Test that custom api_key is passed to async client."""
        mock_client_class.return_value = AsyncMock()

        create_async_quercle_fetch(api_key="qk_async_key")

        mock_client_class.assert_called_once_with(api_key="qk_async_key", timeout=120.0)

    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    def test_created_function_has_docstring(self, mock_client_class):
        """Test that created async function has docstring for ADK."""
        mock_client_class.return_value = AsyncMock()

        fetch_fn = create_async_quercle_fetch()

        assert fetch_fn.__doc__ is not None
        assert "url" in fetch_fn.__doc__.lower()

    @pytest.mark.asyncio
    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    async def test_created_function_executes(self, mock_client_class):
        """Test that created async function executes correctly."""
        mock_client = AsyncMock()
        mock_client.fetch.return_value = "Async custom fetch result"
        mock_client_class.return_value = mock_client

        fetch_fn = create_async_quercle_fetch(api_key="qk_test")
        result = await fetch_fn("https://example.com", "Extract data")

        assert result == "Async custom fetch result"
        mock_client.fetch.assert_called_once_with(
            url="https://example.com",
            prompt="Extract data",
        )


class TestCreateAsyncQuercleSearch:
    """Tests for create_async_quercle_search factory function."""

    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    def test_returns_coroutine_function(self, mock_client_class):
        """Test that factory returns a coroutine function."""
        mock_client_class.return_value = AsyncMock()
        search_fn = create_async_quercle_search()
        assert asyncio.iscoroutinefunction(search_fn)

    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    def test_custom_api_key(self, mock_client_class):
        """Test that custom api_key is passed to async client."""
        mock_client_class.return_value = AsyncMock()

        create_async_quercle_search(api_key="qk_async_key")

        mock_client_class.assert_called_once_with(api_key="qk_async_key", timeout=120.0)

    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    def test_created_function_has_docstring(self, mock_client_class):
        """Test that created async function has docstring for ADK."""
        mock_client_class.return_value = AsyncMock()

        search_fn = create_async_quercle_search()

        assert search_fn.__doc__ is not None
        assert "query" in search_fn.__doc__.lower()

    @pytest.mark.asyncio
    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    async def test_created_function_executes(self, mock_client_class):
        """Test that created async function executes correctly."""
        mock_client = AsyncMock()
        mock_client.search.return_value = "Async custom search result"
        mock_client_class.return_value = mock_client

        search_fn = create_async_quercle_search(api_key="qk_test")
        result = await search_fn("test query", None, None)

        assert result == "Async custom search result"
        mock_client.search.assert_called_once_with(
            "test query",
            allowed_domains=None,
            blocked_domains=None,
        )


class TestGetAsyncQuercleTools:
    """Tests for get_async_quercle_tools convenience function."""

    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    def test_returns_list_of_two_coroutine_functions(self, mock_client_class):
        """Test that get_async_quercle_tools returns 2 async callables."""
        mock_client_class.return_value = AsyncMock()

        tools = get_async_quercle_tools()

        assert isinstance(tools, list)
        assert len(tools) == 2
        assert all(asyncio.iscoroutinefunction(tool) for tool in tools)

    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    def test_tools_have_docstrings(self, mock_client_class):
        """Test that all returned async tools have docstrings."""
        mock_client_class.return_value = AsyncMock()

        tools = get_async_quercle_tools()

        for tool in tools:
            assert tool.__doc__ is not None
            assert len(tool.__doc__) > 0

    @patch("google_adk_quercle.tools.AsyncQuercleClient")
    def test_passes_configuration(self, mock_client_class):
        """Test that api_key and timeout are passed to both async tools."""
        mock_client_class.return_value = AsyncMock()

        get_async_quercle_tools(api_key="qk_async_shared", timeout=90.0)

        assert mock_client_class.call_count == 2
        for call in mock_client_class.call_args_list:
            assert call.kwargs["api_key"] == "qk_async_shared"
            assert call.kwargs["timeout"] == 90.0

"""Tests for Quercle LlamaIndex tools."""

from unittest.mock import AsyncMock, MagicMock, patch

from llama_index.core.tools import FunctionTool

from llama_index.tools.quercle import (
    QuercleToolSpec,
    create_quercle_fetch_tool,
    create_quercle_search_tool,
)


class TestQuercleToolSpec:
    """Tests for QuercleToolSpec."""

    def test_init_default(self) -> None:
        """Test initialization with default parameters."""
        spec = QuercleToolSpec()
        assert spec._api_key is None
        assert spec._timeout is None
        assert spec._sync_client is None
        assert spec._async_client is None

    def test_init_with_params(self) -> None:
        """Test initialization with custom parameters."""
        spec = QuercleToolSpec(api_key="test_key", timeout=30.0)
        assert spec._api_key == "test_key"
        assert spec._timeout == 30.0

    def test_spec_functions(self) -> None:
        """Test that spec_functions lists the expected methods with async counterparts."""
        assert QuercleToolSpec.spec_functions == [("fetch", "afetch"), ("search", "asearch")]

    @patch("llama_index.tools.quercle.base.QuercleClient")
    def test_get_sync_client_creates_once(self, mock_client_class: MagicMock) -> None:
        """Test that sync client is created lazily and reused."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        spec = QuercleToolSpec(api_key="test_key", timeout=30.0)

        # First call creates client
        client1 = spec._get_sync_client()
        assert client1 is mock_client
        mock_client_class.assert_called_once_with(api_key="test_key", timeout=30.0)

        # Second call reuses client
        client2 = spec._get_sync_client()
        assert client2 is mock_client
        assert mock_client_class.call_count == 1

    @patch("llama_index.tools.quercle.base.AsyncQuercleClient")
    def test_get_async_client_creates_once(self, mock_client_class: MagicMock) -> None:
        """Test that async client is created lazily and reused."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        spec = QuercleToolSpec(api_key="test_key", timeout=30.0)

        # First call creates client
        client1 = spec._get_async_client()
        assert client1 is mock_client
        mock_client_class.assert_called_once_with(api_key="test_key", timeout=30.0)

        # Second call reuses client
        client2 = spec._get_async_client()
        assert client2 is mock_client
        assert mock_client_class.call_count == 1

    @patch("llama_index.tools.quercle.base.QuercleClient")
    def test_fetch(self, mock_client_class: MagicMock) -> None:
        """Test synchronous fetch."""
        mock_client = MagicMock()
        mock_client.fetch.return_value = "Fetched content"
        mock_client_class.return_value = mock_client

        spec = QuercleToolSpec()
        result = spec.fetch(url="https://example.com", prompt="Summarize this page")

        assert result == "Fetched content"
        mock_client.fetch.assert_called_once_with(
            url="https://example.com", prompt="Summarize this page"
        )

    @patch("llama_index.tools.quercle.base.AsyncQuercleClient")
    async def test_afetch(self, mock_client_class: MagicMock) -> None:
        """Test asynchronous fetch."""
        mock_client = MagicMock()
        mock_client.fetch = AsyncMock(return_value="Async fetched content")
        mock_client_class.return_value = mock_client

        spec = QuercleToolSpec()
        result = await spec.afetch(url="https://example.com", prompt="Summarize this page")

        assert result == "Async fetched content"
        mock_client.fetch.assert_called_once_with(
            url="https://example.com", prompt="Summarize this page"
        )

    @patch("llama_index.tools.quercle.base.QuercleClient")
    def test_search(self, mock_client_class: MagicMock) -> None:
        """Test synchronous search."""
        mock_client = MagicMock()
        mock_client.search.return_value = "Search results"
        mock_client_class.return_value = mock_client

        spec = QuercleToolSpec()
        result = spec.search(query="Python news")

        assert result == "Search results"
        mock_client.search.assert_called_once_with(
            "Python news", allowed_domains=None, blocked_domains=None
        )

    @patch("llama_index.tools.quercle.base.QuercleClient")
    def test_search_with_domains(self, mock_client_class: MagicMock) -> None:
        """Test synchronous search with domain filters."""
        mock_client = MagicMock()
        mock_client.search.return_value = "Filtered search results"
        mock_client_class.return_value = mock_client

        spec = QuercleToolSpec()
        result = spec.search(
            query="Python news",
            allowed_domains=["python.org"],
            blocked_domains=["spam.com"],
        )

        assert result == "Filtered search results"
        mock_client.search.assert_called_once_with(
            "Python news",
            allowed_domains=["python.org"],
            blocked_domains=["spam.com"],
        )

    @patch("llama_index.tools.quercle.base.AsyncQuercleClient")
    async def test_asearch(self, mock_client_class: MagicMock) -> None:
        """Test asynchronous search."""
        mock_client = MagicMock()
        mock_client.search = AsyncMock(return_value="Async search results")
        mock_client_class.return_value = mock_client

        spec = QuercleToolSpec()
        result = await spec.asearch(query="Python news")

        assert result == "Async search results"
        mock_client.search.assert_called_once_with(
            "Python news", allowed_domains=None, blocked_domains=None
        )

    @patch("llama_index.tools.quercle.base.AsyncQuercleClient")
    async def test_asearch_with_domains(self, mock_client_class: MagicMock) -> None:
        """Test asynchronous search with domain filters."""
        mock_client = MagicMock()
        mock_client.search = AsyncMock(return_value="Async filtered results")
        mock_client_class.return_value = mock_client

        spec = QuercleToolSpec()
        result = await spec.asearch(
            query="Python news",
            allowed_domains=["python.org"],
            blocked_domains=["spam.com"],
        )

        assert result == "Async filtered results"
        mock_client.search.assert_called_once_with(
            "Python news",
            allowed_domains=["python.org"],
            blocked_domains=["spam.com"],
        )

    def test_to_tool_list(self) -> None:
        """Test that to_tool_list returns FunctionTools."""
        spec = QuercleToolSpec()
        tools = spec.to_tool_list()

        assert len(tools) == 2
        assert all(isinstance(tool, FunctionTool) for tool in tools)

        tool_names = [tool.metadata.name for tool in tools]
        assert "fetch" in tool_names
        assert "search" in tool_names

    def test_to_tool_list_has_native_async(self) -> None:
        """Test that to_tool_list wires up native async methods, not sync_to_async wrappers."""
        spec = QuercleToolSpec()
        tools = spec.to_tool_list()

        for tool in tools:
            # async_fn should be the actual async method, not a sync_to_async wrapper
            assert tool.async_fn is not None
            assert "sync_to_async" not in str(tool.async_fn)
            # Verify it's a bound method of the spec
            assert hasattr(tool.async_fn, "__self__")
            assert tool.async_fn.__self__ is spec


class TestFactoryFunctions:
    """Tests for standalone tool factory functions."""

    def test_create_quercle_fetch_tool(self) -> None:
        """Test creating a standalone fetch tool."""
        tool = create_quercle_fetch_tool(api_key="test_key", timeout=30.0)

        assert isinstance(tool, FunctionTool)
        assert tool.metadata.name == "quercle_fetch"
        assert tool.metadata.description is not None

    def test_create_quercle_search_tool(self) -> None:
        """Test creating a standalone search tool."""
        tool = create_quercle_search_tool(api_key="test_key", timeout=30.0)

        assert isinstance(tool, FunctionTool)
        assert tool.metadata.name == "quercle_search"
        assert tool.metadata.description is not None

    @patch("llama_index.tools.quercle.base.QuercleClient")
    def test_fetch_tool_callable(self, mock_client_class: MagicMock) -> None:
        """Test that fetch tool is callable."""
        mock_client = MagicMock()
        mock_client.fetch.return_value = "Tool result"
        mock_client_class.return_value = mock_client

        tool = create_quercle_fetch_tool()
        result = tool.call(url="https://example.com", prompt="Summarize")

        # tool.call() returns a ToolOutput object
        assert result.raw_output == "Tool result"

    @patch("llama_index.tools.quercle.base.QuercleClient")
    def test_search_tool_callable(self, mock_client_class: MagicMock) -> None:
        """Test that search tool is callable."""
        mock_client = MagicMock()
        mock_client.search.return_value = "Search result"
        mock_client_class.return_value = mock_client

        tool = create_quercle_search_tool()
        result = tool.call(query="test query")

        # tool.call() returns a ToolOutput object
        assert result.raw_output == "Search result"

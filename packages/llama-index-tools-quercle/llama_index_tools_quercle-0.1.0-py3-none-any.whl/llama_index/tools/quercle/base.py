"""Quercle tool implementations for LlamaIndex."""

from typing import Annotated

from llama_index.core.tools import FunctionTool
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from pydantic import Field

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


class QuercleToolSpec(BaseToolSpec):
    """Quercle tool specification for web fetch and search.

    This tool spec provides access to Quercle's AI-powered web fetch and search APIs.
    Use `to_tool_list()` to get LlamaIndex tools for use with agents.

    Example:
        >>> from llama_index.tools.quercle import QuercleToolSpec
        >>> from llama_index.core.agent import ReActAgent
        >>> from llama_index.llms.openai import OpenAI
        >>>
        >>> quercle = QuercleToolSpec(api_key="qk_...")
        >>> agent = ReActAgent.from_tools(quercle.to_tool_list(), llm=OpenAI())
        >>> response = agent.chat("Search for Python news")
    """

    spec_functions = [("fetch", "afetch"), ("search", "asearch")]

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        """Initialize the Quercle tool spec.

        Args:
            api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
            timeout: Request timeout in seconds.
        """
        self._api_key = api_key
        self._timeout = timeout
        self._sync_client: QuercleClient | None = None
        self._async_client: AsyncQuercleClient | None = None

    def _get_sync_client(self) -> QuercleClient:
        """Get or create the synchronous Quercle client."""
        if self._sync_client is None:
            self._sync_client = QuercleClient(
                api_key=self._api_key,
                timeout=self._timeout,
            )
        return self._sync_client

    def _get_async_client(self) -> AsyncQuercleClient:
        """Get or create the asynchronous Quercle client."""
        if self._async_client is None:
            self._async_client = AsyncQuercleClient(
                api_key=self._api_key,
                timeout=self._timeout,
            )
        return self._async_client

    def fetch(
        self,
        url: Annotated[str, Field(description=FETCH_URL_DESCRIPTION)],
        prompt: Annotated[str, Field(description=FETCH_PROMPT_DESCRIPTION)],
    ) -> str:
        """Fetch a web page and analyze its content using AI."""
        return self._get_sync_client().fetch(url=url, prompt=prompt)

    async def afetch(
        self,
        url: Annotated[str, Field(description=FETCH_URL_DESCRIPTION)],
        prompt: Annotated[str, Field(description=FETCH_PROMPT_DESCRIPTION)],
    ) -> str:
        """Async fetch a web page and analyze its content using AI."""
        return await self._get_async_client().fetch(url=url, prompt=prompt)

    def search(
        self,
        query: Annotated[str, Field(description=SEARCH_QUERY_DESCRIPTION)],
        allowed_domains: Annotated[
            list[str] | None, Field(description=SEARCH_ALLOWED_DOMAINS_DESCRIPTION)
        ] = None,
        blocked_domains: Annotated[
            list[str] | None, Field(description=SEARCH_BLOCKED_DOMAINS_DESCRIPTION)
        ] = None,
    ) -> str:
        """Search the web and get AI-synthesized answers with citations."""
        return self._get_sync_client().search(
            query,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
        )

    async def asearch(
        self,
        query: Annotated[str, Field(description=SEARCH_QUERY_DESCRIPTION)],
        allowed_domains: Annotated[
            list[str] | None, Field(description=SEARCH_ALLOWED_DOMAINS_DESCRIPTION)
        ] = None,
        blocked_domains: Annotated[
            list[str] | None, Field(description=SEARCH_BLOCKED_DOMAINS_DESCRIPTION)
        ] = None,
    ) -> str:
        """Async search the web and get AI-synthesized answers with citations."""
        return await self._get_async_client().search(
            query,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
        )


def create_quercle_fetch_tool(
    api_key: str | None = None,
    timeout: float | None = None,
) -> FunctionTool:
    """Create a standalone Quercle fetch tool.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        timeout: Request timeout in seconds.

    Returns:
        A FunctionTool for fetching and analyzing web pages.
    """
    spec = QuercleToolSpec(api_key=api_key, timeout=timeout)
    return FunctionTool.from_defaults(
        fn=spec.fetch,
        async_fn=spec.afetch,
        name="quercle_fetch",
        description=FETCH_TOOL_DESCRIPTION,
    )


def create_quercle_search_tool(
    api_key: str | None = None,
    timeout: float | None = None,
) -> FunctionTool:
    """Create a standalone Quercle search tool.

    Args:
        api_key: Quercle API key. Falls back to QUERCLE_API_KEY env var if not provided.
        timeout: Request timeout in seconds.

    Returns:
        A FunctionTool for web search with AI-synthesized answers.
    """
    spec = QuercleToolSpec(api_key=api_key, timeout=timeout)
    return FunctionTool.from_defaults(
        fn=spec.search,
        async_fn=spec.asearch,
        name="quercle_search",
        description=SEARCH_TOOL_DESCRIPTION,
    )

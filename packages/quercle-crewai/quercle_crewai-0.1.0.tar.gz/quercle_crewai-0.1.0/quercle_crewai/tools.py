"""CrewAI tools for Quercle web search and URL fetching."""

from typing import Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
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


class QuercleFetchInput(BaseModel):
    """Input schema for QuercleFetchTool."""

    url: str = Field(description=FETCH_URL_DESCRIPTION)
    prompt: str = Field(description=FETCH_PROMPT_DESCRIPTION)


class QuercleSearchInput(BaseModel):
    """Input schema for QuercleSearchTool."""

    query: str = Field(description=SEARCH_QUERY_DESCRIPTION)
    allowed_domains: Optional[list[str]] = Field(
        default=None,
        description=SEARCH_ALLOWED_DOMAINS_DESCRIPTION,
    )
    blocked_domains: Optional[list[str]] = Field(
        default=None,
        description=SEARCH_BLOCKED_DOMAINS_DESCRIPTION,
    )


class QuercleBaseTool(BaseTool):
    """Base class for Quercle tools with shared client management."""

    api_key: Optional[str] = Field(
        default=None,
        description="Quercle API key. Falls back to QUERCLE_API_KEY env var.",
    )
    timeout: Optional[float] = Field(
        default=None,
        description="Request timeout in seconds.",
    )

    _sync_client: Optional[QuercleClient] = PrivateAttr(default=None)
    _async_client: Optional[AsyncQuercleClient] = PrivateAttr(default=None)

    def _get_sync_client(self) -> QuercleClient:
        """Get or create the synchronous Quercle client."""
        if self._sync_client is None:
            self._sync_client = QuercleClient(
                api_key=self.api_key,
                timeout=self.timeout,
            )
        return self._sync_client

    def _get_async_client(self) -> AsyncQuercleClient:
        """Get or create the asynchronous Quercle client."""
        if self._async_client is None:
            self._async_client = AsyncQuercleClient(
                api_key=self.api_key,
                timeout=self.timeout,
            )
        return self._async_client


class QuercleFetchTool(QuercleBaseTool):
    """Tool for fetching a URL and analyzing its content with AI.

    This tool uses the Quercle API to fetch web pages and analyze
    their content based on a provided prompt.

    Example:
        >>> tool = QuercleFetchTool()
        >>> result = tool.run(url="https://example.com", prompt="Summarize this page")
    """

    name: str = "quercle_fetch"
    description: str = FETCH_TOOL_DESCRIPTION
    args_schema: Type[BaseModel] = QuercleFetchInput

    def _run(self, url: str, prompt: str) -> str:
        """Execute a synchronous URL fetch and analysis.

        Args:
            url: The URL to fetch.
            prompt: Instructions for content analysis.

        Returns:
            AI-processed content based on the prompt.
        """
        return self._get_sync_client().fetch(url=url, prompt=prompt)

    async def _arun(self, url: str, prompt: str) -> str:
        """Execute an asynchronous URL fetch and analysis.

        Args:
            url: The URL to fetch.
            prompt: Instructions for content analysis.

        Returns:
            AI-processed content based on the prompt.
        """
        return await self._get_async_client().fetch(url=url, prompt=prompt)


class QuercleSearchTool(QuercleBaseTool):
    """Tool for searching the web and getting AI-synthesized answers with citations.

    This tool uses the Quercle API to perform web searches and return
    AI-synthesized answers with source citations.

    Example:
        >>> tool = QuercleSearchTool()
        >>> result = tool.run(query="What is TypeScript?")
    """

    name: str = "quercle_search"
    description: str = SEARCH_TOOL_DESCRIPTION
    args_schema: Type[BaseModel] = QuercleSearchInput

    def _run(
        self,
        query: str,
        allowed_domains: Optional[list[str]] = None,
        blocked_domains: Optional[list[str]] = None,
    ) -> str:
        """Execute a synchronous web search.

        Args:
            query: The search query.
            allowed_domains: Optional list of domains to include.
            blocked_domains: Optional list of domains to exclude.

        Returns:
            AI-synthesized answer with citations.
        """
        return self._get_sync_client().search(
            query,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
        )

    async def _arun(
        self,
        query: str,
        allowed_domains: Optional[list[str]] = None,
        blocked_domains: Optional[list[str]] = None,
    ) -> str:
        """Execute an asynchronous web search.

        Args:
            query: The search query.
            allowed_domains: Optional list of domains to include.
            blocked_domains: Optional list of domains to exclude.

        Returns:
            AI-synthesized answer with citations.
        """
        return await self._get_async_client().search(
            query,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
        )

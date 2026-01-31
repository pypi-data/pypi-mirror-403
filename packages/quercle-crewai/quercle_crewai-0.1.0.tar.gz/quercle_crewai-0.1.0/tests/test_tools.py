"""Tests for Quercle CrewAI tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from quercle_crewai import QuercleFetchTool, QuercleSearchTool


class TestQuercleSearchTool:
    """Tests for QuercleSearchTool."""

    def test_tool_attributes(self):
        """Test that tool has correct name and description."""
        tool = QuercleSearchTool(api_key="qk_test")
        assert tool.name == "quercle_search"
        assert "search" in tool.description.lower()
        assert tool.args_schema is not None

    def test_tool_initialization_with_api_key(self):
        """Test tool initialization with explicit API key."""
        tool = QuercleSearchTool(api_key="qk_test123")
        assert tool.api_key == "qk_test123"

    def test_tool_initialization_with_timeout(self):
        """Test tool initialization with timeout parameter."""
        tool = QuercleSearchTool(api_key="qk_test", timeout=60.0)
        assert tool.timeout == 60.0

    @patch("quercle_crewai.tools.QuercleClient")
    def test_run_basic_search(self, mock_client_class: MagicMock):
        """Test synchronous search execution."""
        mock_client = MagicMock()
        mock_client.search.return_value = "AI answer with citations"
        mock_client_class.return_value = mock_client

        tool = QuercleSearchTool(api_key="qk_test")
        result = tool._run(query="What is Python?")

        assert result == "AI answer with citations"
        mock_client.search.assert_called_once_with(
            "What is Python?",
            allowed_domains=None,
            blocked_domains=None,
        )

    @patch("quercle_crewai.tools.QuercleClient")
    def test_run_search_with_domain_filters(self, mock_client_class: MagicMock):
        """Test synchronous search with domain filtering."""
        mock_client = MagicMock()
        mock_client.search.return_value = "Filtered results"
        mock_client_class.return_value = mock_client

        tool = QuercleSearchTool(api_key="qk_test")
        result = tool._run(
            query="TypeScript",
            allowed_domains=["*.org", "*.edu"],
            blocked_domains=["spam.com"],
        )

        assert result == "Filtered results"
        mock_client.search.assert_called_once_with(
            "TypeScript",
            allowed_domains=["*.org", "*.edu"],
            blocked_domains=["spam.com"],
        )

    @pytest.mark.asyncio
    @patch("quercle_crewai.tools.AsyncQuercleClient")
    async def test_arun_basic_search(self, mock_client_class: MagicMock):
        """Test asynchronous search execution."""
        mock_client = AsyncMock()
        mock_client.search.return_value = "Async AI answer"
        mock_client_class.return_value = mock_client

        tool = QuercleSearchTool(api_key="qk_test")
        result = await tool._arun(query="What is Rust?")

        assert result == "Async AI answer"
        mock_client.search.assert_called_once_with(
            "What is Rust?",
            allowed_domains=None,
            blocked_domains=None,
        )

    @pytest.mark.asyncio
    @patch("quercle_crewai.tools.AsyncQuercleClient")
    async def test_arun_search_with_domain_filters(self, mock_client_class: MagicMock):
        """Test asynchronous search with domain filtering."""
        mock_client = AsyncMock()
        mock_client.search.return_value = "Async filtered results"
        mock_client_class.return_value = mock_client

        tool = QuercleSearchTool(api_key="qk_test")
        result = await tool._arun(
            query="Go programming",
            allowed_domains=["*.dev"],
            blocked_domains=["ads.com"],
        )

        assert result == "Async filtered results"
        mock_client.search.assert_called_once_with(
            "Go programming",
            allowed_domains=["*.dev"],
            blocked_domains=["ads.com"],
        )


class TestQuercleFetchTool:
    """Tests for QuercleFetchTool."""

    def test_tool_attributes(self):
        """Test that tool has correct name and description."""
        tool = QuercleFetchTool(api_key="qk_test")
        assert tool.name == "quercle_fetch"
        assert "fetch" in tool.description.lower()
        assert tool.args_schema is not None

    def test_tool_initialization_with_api_key(self):
        """Test tool initialization with explicit API key."""
        tool = QuercleFetchTool(api_key="qk_test456")
        assert tool.api_key == "qk_test456"

    def test_tool_initialization_with_timeout(self):
        """Test tool initialization with timeout parameter."""
        tool = QuercleFetchTool(api_key="qk_test", timeout=120.0)
        assert tool.timeout == 120.0

    @patch("quercle_crewai.tools.QuercleClient")
    def test_run_fetch(self, mock_client_class: MagicMock):
        """Test synchronous fetch execution."""
        mock_client = MagicMock()
        mock_client.fetch.return_value = "Page summary content"
        mock_client_class.return_value = mock_client

        tool = QuercleFetchTool(api_key="qk_test")
        result = tool._run(url="https://example.com", prompt="Summarize this page")

        assert result == "Page summary content"
        mock_client.fetch.assert_called_once_with(
            url="https://example.com",
            prompt="Summarize this page",
        )

    @pytest.mark.asyncio
    @patch("quercle_crewai.tools.AsyncQuercleClient")
    async def test_arun_fetch(self, mock_client_class: MagicMock):
        """Test asynchronous fetch execution."""
        mock_client = AsyncMock()
        mock_client.fetch.return_value = "Async page analysis"
        mock_client_class.return_value = mock_client

        tool = QuercleFetchTool(api_key="qk_test")
        result = await tool._arun(
            url="https://docs.python.org",
            prompt="Extract the key features",
        )

        assert result == "Async page analysis"
        mock_client.fetch.assert_called_once_with(
            url="https://docs.python.org",
            prompt="Extract the key features",
        )


class TestToolIntegration:
    """Integration tests for tool usage patterns."""

    @patch("quercle_crewai.tools.QuercleClient")
    def test_search_tool_run_interface(self, mock_client_class: MagicMock):
        """Test that search tool works with CrewAI's run interface."""
        mock_client = MagicMock()
        mock_client.search.return_value = "Search result"
        mock_client_class.return_value = mock_client

        tool = QuercleSearchTool(api_key="qk_test")
        result = tool.run(query="test query")

        assert result == "Search result"

    @patch("quercle_crewai.tools.QuercleClient")
    def test_fetch_tool_run_interface(self, mock_client_class: MagicMock):
        """Test that fetch tool works with CrewAI's run interface."""
        mock_client = MagicMock()
        mock_client.fetch.return_value = "Fetch result"
        mock_client_class.return_value = mock_client

        tool = QuercleFetchTool(api_key="qk_test")
        result = tool.run(url="https://example.com", prompt="Summarize")

        assert result == "Fetch result"

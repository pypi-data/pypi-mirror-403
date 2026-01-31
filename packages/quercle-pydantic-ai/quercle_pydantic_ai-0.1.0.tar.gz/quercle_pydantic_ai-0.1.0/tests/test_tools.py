"""Tests for Quercle Pydantic AI tools."""

from unittest.mock import AsyncMock, patch

import pytest
from pydantic_ai.tools import Tool

from quercle_pydantic_ai import (
    QuercleToolset,
    quercle_fetch_tool,
    quercle_search_tool,
    quercle_tools,
)


class TestQuercleSearchTool:
    """Tests for quercle_search_tool."""

    def test_returns_tool_instance(self):
        """Test that factory returns a Tool instance."""
        tool = quercle_search_tool(api_key="qk_test")
        assert isinstance(tool, Tool)

    def test_tool_has_correct_name(self):
        """Test that tool has the correct name."""
        tool = quercle_search_tool(api_key="qk_test")
        assert tool.name == "quercle_search"

    def test_tool_has_description(self):
        """Test that tool has a description."""
        tool = quercle_search_tool(api_key="qk_test")
        assert tool.description is not None
        assert len(tool.description) > 0

    def test_lazy_client_initialization(self):
        """Test that client is not created until first call."""
        with patch("quercle_pydantic_ai.tools.AsyncQuercleClient") as mock_client_class:
            _ = quercle_search_tool(api_key="qk_test")
            # Client should not be created yet
            mock_client_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_execution(self):
        """Test that search tool executes correctly."""
        with patch("quercle_pydantic_ai.tools.AsyncQuercleClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search.return_value = "AI answer with citations"
            mock_client_class.return_value = mock_client

            tool = quercle_search_tool(api_key="qk_test")
            # Get the inner function from the tool
            result = await tool.function(query="What is Python?")

            assert result == "AI answer with citations"
            mock_client.search.assert_called_once_with(
                "What is Python?",
                allowed_domains=None,
                blocked_domains=None,
            )

    @pytest.mark.asyncio
    async def test_search_with_domain_filters(self):
        """Test search with domain filtering."""
        with patch("quercle_pydantic_ai.tools.AsyncQuercleClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search.return_value = "Filtered results"
            mock_client_class.return_value = mock_client

            tool = quercle_search_tool(
                api_key="qk_test",
                allowed_domains=["*.org", "*.edu"],
                blocked_domains=["spam.com"],
            )
            result = await tool.function(query="TypeScript")

            assert result == "Filtered results"
            mock_client.search.assert_called_once_with(
                "TypeScript",
                allowed_domains=["*.org", "*.edu"],
                blocked_domains=["spam.com"],
            )


class TestQuercleFetchTool:
    """Tests for quercle_fetch_tool."""

    def test_returns_tool_instance(self):
        """Test that factory returns a Tool instance."""
        tool = quercle_fetch_tool(api_key="qk_test")
        assert isinstance(tool, Tool)

    def test_tool_has_correct_name(self):
        """Test that tool has the correct name."""
        tool = quercle_fetch_tool(api_key="qk_test")
        assert tool.name == "quercle_fetch"

    def test_tool_has_description(self):
        """Test that tool has a description."""
        tool = quercle_fetch_tool(api_key="qk_test")
        assert tool.description is not None
        assert len(tool.description) > 0

    def test_lazy_client_initialization(self):
        """Test that client is not created until first call."""
        with patch("quercle_pydantic_ai.tools.AsyncQuercleClient") as mock_client_class:
            _ = quercle_fetch_tool(api_key="qk_test")
            # Client should not be created yet
            mock_client_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_execution(self):
        """Test that fetch tool executes correctly."""
        with patch("quercle_pydantic_ai.tools.AsyncQuercleClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.fetch.return_value = "Page summary content"
            mock_client_class.return_value = mock_client

            tool = quercle_fetch_tool(api_key="qk_test")
            result = await tool.function(
                url="https://example.com",
                prompt="Summarize this page",
            )

            assert result == "Page summary content"
            mock_client.fetch.assert_called_once_with(
                url="https://example.com",
                prompt="Summarize this page",
            )


class TestQuercleTools:
    """Tests for quercle_tools convenience function."""

    def test_returns_list_of_tools(self):
        """Test that function returns a list of Tool instances."""
        tools = quercle_tools(api_key="qk_test")
        assert isinstance(tools, list)
        assert len(tools) == 2
        assert all(isinstance(t, Tool) for t in tools)

    def test_includes_search_and_fetch(self):
        """Test that list includes both search and fetch tools."""
        tools = quercle_tools(api_key="qk_test")
        names = {t.name for t in tools}
        assert names == {"quercle_search", "quercle_fetch"}


class TestQuercleToolset:
    """Tests for QuercleToolset class."""

    def test_toolset_creation(self):
        """Test that toolset can be created."""
        toolset = QuercleToolset(api_key="qk_test")
        assert toolset is not None

    def test_default_includes_both_tools(self):
        """Test that default toolset includes both tools."""
        toolset = QuercleToolset(api_key="qk_test")
        # FunctionToolset stores tools in a dict keyed by name
        tool_names = set(toolset.tools.keys())
        assert "quercle_search" in tool_names
        assert "quercle_fetch" in tool_names

    def test_exclude_search(self):
        """Test that search can be excluded."""
        toolset = QuercleToolset(api_key="qk_test", include_search=False)
        tool_names = set(toolset.tools.keys())
        assert "quercle_search" not in tool_names
        assert "quercle_fetch" in tool_names

    def test_exclude_fetch(self):
        """Test that fetch can be excluded."""
        toolset = QuercleToolset(api_key="qk_test", include_fetch=False)
        tool_names = set(toolset.tools.keys())
        assert "quercle_search" in tool_names
        assert "quercle_fetch" not in tool_names

    def test_exclude_both(self):
        """Test that both tools can be excluded."""
        toolset = QuercleToolset(
            api_key="qk_test",
            include_search=False,
            include_fetch=False,
        )
        assert len(toolset.tools) == 0

    def test_domain_filter_configuration(self):
        """Test that domain filters can be configured."""
        toolset = QuercleToolset(
            api_key="qk_test",
            search_allowed_domains=["*.org"],
            search_blocked_domains=["spam.com"],
        )
        # Verify toolset was created (filters are applied at call time)
        assert toolset is not None
        assert len(toolset.tools) == 2

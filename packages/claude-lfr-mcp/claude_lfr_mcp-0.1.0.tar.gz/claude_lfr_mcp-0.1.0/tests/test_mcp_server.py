"""Tests for mcp_server.py - MCP tool handlers and server functionality."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from claude_lfr_mcp.mcp_server import (
    list_tools,
    call_tool,
    check_qdrant_health,
    server,
)


class TestListTools:
    """Tests for list_tools handler."""

    @pytest.mark.asyncio
    async def test_returns_three_tools(self):
        """Test that list_tools returns exactly 3 tools."""
        tools = await list_tools()
        assert len(tools) == 3

    @pytest.mark.asyncio
    async def test_search_code_tool_exists(self):
        """Test that search_code tool is defined."""
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "search_code" in tool_names

    @pytest.mark.asyncio
    async def test_index_directory_tool_exists(self):
        """Test that index_directory tool is defined."""
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "index_directory" in tool_names

    @pytest.mark.asyncio
    async def test_get_index_status_tool_exists(self):
        """Test that get_index_status tool is defined."""
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "get_index_status" in tool_names

    @pytest.mark.asyncio
    async def test_search_code_schema(self):
        """Test search_code tool has correct schema."""
        tools = await list_tools()
        search_tool = next(t for t in tools if t.name == "search_code")

        schema = search_tool.inputSchema
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "top_k" in schema["properties"]
        assert "required" in schema
        assert "query" in schema["required"]

    @pytest.mark.asyncio
    async def test_index_directory_schema(self):
        """Test index_directory tool has correct schema."""
        tools = await list_tools()
        index_tool = next(t for t in tools if t.name == "index_directory")

        schema = index_tool.inputSchema
        assert "properties" in schema
        assert "directory" in schema["properties"]
        assert "max_files" in schema["properties"]
        assert "use_gitignore" in schema["properties"]
        assert "extra_ignore_patterns" in schema["properties"]
        assert "required" in schema
        assert "directory" in schema["required"]

    @pytest.mark.asyncio
    async def test_tools_have_descriptions(self):
        """Test that all tools have descriptions."""
        tools = await list_tools()
        for tool in tools:
            assert tool.description
            assert len(tool.description) > 10


class TestCallToolSearchCode:
    """Tests for call_tool with search_code."""

    @pytest.mark.asyncio
    async def test_search_code_requires_query(self):
        """Test that empty query returns error."""
        result = await call_tool("search_code", {"query": ""})

        assert len(result) == 1
        assert "Error: query is required" in result[0].text

    @pytest.mark.asyncio
    async def test_search_code_with_valid_query(self):
        """Test search_code with valid query (mocked)."""
        mock_result = MagicMock()
        mock_result.score = 0.85
        mock_result.payload = {
            "path": "src/main.py",
            "start_line": 1,
            "end_line": 10,
            "snippet": "def main():\n    pass",
        }

        with patch("claude_lfr_mcp.mcp_server.search", return_value=[mock_result]):
            result = await call_tool("search_code", {"query": "main function"})

            assert len(result) == 1
            assert "Found 1 results" in result[0].text
            assert "src/main.py" in result[0].text
            assert "0.850" in result[0].text

    @pytest.mark.asyncio
    async def test_search_code_no_results(self):
        """Test search_code with no results."""
        with patch("claude_lfr_mcp.mcp_server.search", return_value=[]):
            result = await call_tool("search_code", {"query": "nonexistent"})

            assert len(result) == 1
            assert "No results found" in result[0].text

    @pytest.mark.asyncio
    async def test_search_code_handles_exception(self):
        """Test search_code handles exceptions gracefully."""
        with patch(
            "claude_lfr_mcp.mcp_server.search",
            side_effect=Exception("Connection failed"),
        ):
            result = await call_tool("search_code", {"query": "test"})

            assert len(result) == 1
            assert "Search error:" in result[0].text
            assert "Connection failed" in result[0].text

    @pytest.mark.asyncio
    async def test_search_code_respects_top_k(self):
        """Test that top_k parameter is passed to search."""
        with patch("claude_lfr_mcp.mcp_server.search", return_value=[]) as mock_search:
            await call_tool("search_code", {"query": "test", "top_k": 20})

            mock_search.assert_called_once_with("test", top_k=20)

    @pytest.mark.asyncio
    async def test_search_code_default_top_k(self):
        """Test that default top_k is 10."""
        with patch("claude_lfr_mcp.mcp_server.search", return_value=[]) as mock_search:
            await call_tool("search_code", {"query": "test"})

            mock_search.assert_called_once_with("test", top_k=10)


class TestCallToolIndexDirectory:
    """Tests for call_tool with index_directory."""

    @pytest.mark.asyncio
    async def test_index_directory_requires_directory(self):
        """Test that empty directory returns error."""
        result = await call_tool("index_directory", {"directory": ""})

        assert len(result) == 1
        assert "Error: directory is required" in result[0].text

    @pytest.mark.asyncio
    async def test_index_directory_nonexistent_path(self):
        """Test that nonexistent path returns error."""
        result = await call_tool(
            "index_directory",
            {"directory": "/nonexistent/path/to/directory"},
        )

        assert len(result) == 1
        assert "Error: directory does not exist" in result[0].text

    @pytest.mark.asyncio
    async def test_index_directory_not_a_directory(self, tmp_path):
        """Test that file path returns error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = await call_tool(
            "index_directory",
            {"directory": str(test_file)},
        )

        assert len(result) == 1
        assert "Error: not a directory" in result[0].text

    @pytest.mark.asyncio
    async def test_index_directory_success(self, tmp_path):
        """Test successful directory indexing (mocked)."""
        with patch("claude_lfr_mcp.mcp_server.index_repo") as mock_index:
            with patch("claude_lfr_mcp.mcp_server.get_ignore_handler"):
                result = await call_tool(
                    "index_directory",
                    {"directory": str(tmp_path)},
                )

                assert len(result) == 1
                assert "Successfully indexed" in result[0].text
                mock_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_directory_handles_exception(self, tmp_path):
        """Test index_directory handles exceptions gracefully."""
        with patch(
            "claude_lfr_mcp.mcp_server.get_ignore_handler",
            side_effect=Exception("Permission denied"),
        ):
            result = await call_tool(
                "index_directory",
                {"directory": str(tmp_path)},
            )

            assert len(result) == 1
            assert "Indexing error:" in result[0].text

    @pytest.mark.asyncio
    async def test_index_directory_respects_max_files(self, tmp_path):
        """Test that max_files parameter is passed."""
        with patch("claude_lfr_mcp.mcp_server.index_repo") as mock_index:
            with patch("claude_lfr_mcp.mcp_server.get_ignore_handler"):
                await call_tool(
                    "index_directory",
                    {"directory": str(tmp_path), "max_files": 100},
                )

                call_args = mock_index.call_args
                assert call_args.kwargs.get("max_files") == 100

    @pytest.mark.asyncio
    async def test_index_directory_respects_use_gitignore(self, tmp_path):
        """Test that use_gitignore parameter is passed."""
        with patch("claude_lfr_mcp.mcp_server.index_repo"):
            with patch(
                "claude_lfr_mcp.mcp_server.get_ignore_handler"
            ) as mock_handler:
                await call_tool(
                    "index_directory",
                    {"directory": str(tmp_path), "use_gitignore": False},
                )

                call_args = mock_handler.call_args
                assert call_args.kwargs.get("use_gitignore") is False


class TestCallToolGetIndexStatus:
    """Tests for call_tool with get_index_status."""

    @pytest.mark.asyncio
    async def test_get_index_status_success(self):
        """Test successful status retrieval."""
        mock_client = MagicMock()
        mock_collections = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "code_bge_base_en_v15"
        mock_collections.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections

        mock_info = MagicMock()
        mock_info.points_count = 1000
        mock_info.indexed_vectors_count = 1000
        mock_info.status = "green"
        mock_client.get_collection.return_value = mock_info

        with patch(
            "claude_lfr_mcp.mcp_server.get_qdrant_client",
            return_value=mock_client,
        ):
            result = await call_tool("get_index_status", {})

            assert len(result) == 1
            text = result[0].text
            assert "Code Index Status" in text
            assert "Points indexed:" in text
            assert "1000" in text

    @pytest.mark.asyncio
    async def test_get_index_status_no_collection(self):
        """Test status when collection doesn't exist."""
        mock_client = MagicMock()
        mock_collections = MagicMock()
        mock_collections.collections = []  # Empty collections
        mock_client.get_collections.return_value = mock_collections

        with patch(
            "claude_lfr_mcp.mcp_server.get_qdrant_client",
            return_value=mock_client,
        ):
            result = await call_tool("get_index_status", {})

            assert len(result) == 1
            assert "Collection does not exist" in result[0].text
            assert "Run index_directory first" in result[0].text

    @pytest.mark.asyncio
    async def test_get_index_status_handles_exception(self):
        """Test that connection errors are handled."""
        with patch(
            "claude_lfr_mcp.mcp_server.get_qdrant_client",
            side_effect=ConnectionError("Cannot connect"),
        ):
            result = await call_tool("get_index_status", {})

            assert len(result) == 1
            assert "Status check error:" in result[0].text

    @pytest.mark.asyncio
    async def test_get_index_status_shows_model_info(self):
        """Test that model information is shown."""
        mock_client = MagicMock()
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections

        with patch(
            "claude_lfr_mcp.mcp_server.get_qdrant_client",
            return_value=mock_client,
        ):
            result = await call_tool("get_index_status", {})

            text = result[0].text
            assert "Embedding Model:" in text
            assert "Model Dimension:" in text


class TestCallToolUnknown:
    """Tests for unknown tool handling."""

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        """Test that unknown tool name returns error."""
        result = await call_tool("nonexistent_tool", {})

        assert len(result) == 1
        assert "Unknown tool: nonexistent_tool" in result[0].text


class TestCheckQdrantHealth:
    """Tests for check_qdrant_health function."""

    def test_returns_true_when_connected(self):
        """Test that health check returns True when Qdrant is available."""
        mock_client = MagicMock()
        mock_client.get_collections.return_value = MagicMock()

        with patch(
            "claude_lfr_mcp.mcp_server.get_qdrant_client",
            return_value=mock_client,
        ):
            result = check_qdrant_health()
            assert result is True

    def test_returns_false_when_disconnected(self):
        """Test that health check returns False when Qdrant is unavailable."""
        with patch(
            "claude_lfr_mcp.mcp_server.get_qdrant_client",
            side_effect=ConnectionError("Cannot connect"),
        ):
            result = check_qdrant_health()
            assert result is False

    def test_returns_false_on_exception(self):
        """Test that health check returns False on any exception."""
        with patch(
            "claude_lfr_mcp.mcp_server.get_qdrant_client",
            side_effect=Exception("Unexpected error"),
        ):
            result = check_qdrant_health()
            assert result is False


class TestServerInstance:
    """Tests for MCP server instance."""

    def test_server_has_name(self):
        """Test that server has correct name."""
        assert server.name == "code-indexer"


class TestSearchCodeOutputFormat:
    """Tests for search_code output formatting."""

    @pytest.mark.asyncio
    async def test_output_includes_file_path(self):
        """Test that output includes file path."""
        mock_result = MagicMock()
        mock_result.score = 0.9
        mock_result.payload = {
            "path": "src/utils/helper.py",
            "start_line": 10,
            "end_line": 20,
            "snippet": "code here",
        }

        with patch("claude_lfr_mcp.mcp_server.search", return_value=[mock_result]):
            result = await call_tool("search_code", {"query": "test"})
            assert "src/utils/helper.py" in result[0].text

    @pytest.mark.asyncio
    async def test_output_includes_line_numbers(self):
        """Test that output includes line numbers."""
        mock_result = MagicMock()
        mock_result.score = 0.9
        mock_result.payload = {
            "path": "file.py",
            "start_line": 42,
            "end_line": 55,
            "snippet": "code",
        }

        with patch("claude_lfr_mcp.mcp_server.search", return_value=[mock_result]):
            result = await call_tool("search_code", {"query": "test"})
            assert "42-55" in result[0].text

    @pytest.mark.asyncio
    async def test_output_includes_score(self):
        """Test that output includes similarity score."""
        mock_result = MagicMock()
        mock_result.score = 0.876
        mock_result.payload = {
            "path": "file.py",
            "start_line": 1,
            "end_line": 10,
            "snippet": "code",
        }

        with patch("claude_lfr_mcp.mcp_server.search", return_value=[mock_result]):
            result = await call_tool("search_code", {"query": "test"})
            assert "0.876" in result[0].text

    @pytest.mark.asyncio
    async def test_output_includes_code_snippet(self):
        """Test that output includes code snippet."""
        mock_result = MagicMock()
        mock_result.score = 0.9
        mock_result.payload = {
            "path": "file.py",
            "start_line": 1,
            "end_line": 10,
            "snippet": "def unique_function_name():\n    return 42",
        }

        with patch("claude_lfr_mcp.mcp_server.search", return_value=[mock_result]):
            result = await call_tool("search_code", {"query": "test"})
            assert "unique_function_name" in result[0].text

    @pytest.mark.asyncio
    async def test_output_truncates_long_snippets(self):
        """Test that long snippets are truncated."""
        long_snippet = "x" * 600  # More than 500 chars
        mock_result = MagicMock()
        mock_result.score = 0.9
        mock_result.payload = {
            "path": "file.py",
            "start_line": 1,
            "end_line": 10,
            "snippet": long_snippet,
        }

        with patch("claude_lfr_mcp.mcp_server.search", return_value=[mock_result]):
            result = await call_tool("search_code", {"query": "test"})
            assert "..." in result[0].text
            # Should have 500 chars + "..."
            assert len(result[0].text) < len(long_snippet) + 200

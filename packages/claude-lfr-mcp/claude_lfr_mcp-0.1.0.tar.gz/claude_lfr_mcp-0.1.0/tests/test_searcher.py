"""Tests for searcher.py - search functionality with mocked dependencies."""

import pytest
from unittest.mock import MagicMock, patch

from claude_lfr_mcp.searcher import search


class TestSearch:
    """Tests for the search function."""

    def test_search_calls_embed_texts_with_query(self):
        """Test that search calls embed_texts with is_query=True."""
        mock_client = MagicMock()
        mock_client.search.return_value = []

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                return_value=[[0.1] * 768],
            ) as mock_embed:
                search("test query")

                mock_embed.assert_called_once_with(["test query"], is_query=True)

    def test_search_uses_correct_collection(self):
        """Test that search uses the correct collection name."""
        mock_client = MagicMock()
        mock_client.search.return_value = []

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                return_value=[[0.1] * 768],
            ):
                with patch(
                    "claude_lfr_mcp.searcher.get_collection_name",
                    return_value="test_collection",
                ):
                    search("test query")

                    mock_client.search.assert_called_once()
                    call_kwargs = mock_client.search.call_args.kwargs
                    assert call_kwargs["collection_name"] == "test_collection"

    def test_search_respects_top_k(self):
        """Test that search respects the top_k parameter."""
        mock_client = MagicMock()
        mock_client.search.return_value = []

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                return_value=[[0.1] * 768],
            ):
                search("test query", top_k=25)

                call_kwargs = mock_client.search.call_args.kwargs
                assert call_kwargs["limit"] == 25

    def test_search_default_top_k(self):
        """Test that default top_k is 10."""
        mock_client = MagicMock()
        mock_client.search.return_value = []

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                return_value=[[0.1] * 768],
            ):
                search("test query")

                call_kwargs = mock_client.search.call_args.kwargs
                assert call_kwargs["limit"] == 10

    def test_search_requests_payload(self):
        """Test that search requests payload in results."""
        mock_client = MagicMock()
        mock_client.search.return_value = []

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                return_value=[[0.1] * 768],
            ):
                search("test query")

                call_kwargs = mock_client.search.call_args.kwargs
                assert call_kwargs["with_payload"] is True

    def test_search_returns_results(self):
        """Test that search returns the Qdrant results."""
        mock_result = MagicMock()
        mock_result.score = 0.95
        mock_result.payload = {"path": "file.py", "snippet": "code"}

        mock_client = MagicMock()
        mock_client.search.return_value = [mock_result]

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                return_value=[[0.1] * 768],
            ):
                results = search("test query")

                assert len(results) == 1
                assert results[0].score == 0.95
                assert results[0].payload["path"] == "file.py"

    def test_search_with_empty_query(self):
        """Test search with empty query."""
        mock_client = MagicMock()
        mock_client.search.return_value = []

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                return_value=[[0.1] * 768],
            ):
                results = search("")

                # Should still call embed_texts with empty string
                assert results == []

    def test_search_passes_embedding_to_qdrant(self):
        """Test that the embedding vector is passed to Qdrant."""
        mock_client = MagicMock()
        mock_client.search.return_value = []
        expected_embedding = [0.5] * 768

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                return_value=[expected_embedding],
            ):
                search("test query")

                call_kwargs = mock_client.search.call_args.kwargs
                assert call_kwargs["query_vector"] == expected_embedding


class TestSearchWithMultipleResults:
    """Tests for search returning multiple results."""

    def test_search_returns_multiple_results(self):
        """Test that search can return multiple results."""
        mock_results = []
        for i in range(5):
            result = MagicMock()
            result.score = 0.9 - i * 0.1
            result.payload = {
                "path": f"file{i}.py",
                "start_line": i * 10,
                "end_line": i * 10 + 10,
                "snippet": f"code {i}",
            }
            mock_results.append(result)

        mock_client = MagicMock()
        mock_client.search.return_value = mock_results

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                return_value=[[0.1] * 768],
            ):
                results = search("test query", top_k=5)

                assert len(results) == 5
                # Results should be in order of score
                assert results[0].score > results[4].score

    def test_search_results_contain_correct_payload(self):
        """Test that results contain expected payload fields."""
        mock_result = MagicMock()
        mock_result.score = 0.85
        mock_result.payload = {
            "path": "src/module/file.py",
            "start_line": 42,
            "end_line": 55,
            "snippet": "def function():\n    pass",
        }

        mock_client = MagicMock()
        mock_client.search.return_value = [mock_result]

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                return_value=[[0.1] * 768],
            ):
                results = search("test")

                payload = results[0].payload
                assert "path" in payload
                assert "start_line" in payload
                assert "end_line" in payload
                assert "snippet" in payload


class TestSearchErrorHandling:
    """Tests for search error handling."""

    def test_search_propagates_qdrant_errors(self):
        """Test that Qdrant errors are propagated."""
        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            side_effect=ConnectionError("Connection failed"),
        ):
            with pytest.raises(ConnectionError):
                search("test query")

    def test_search_propagates_embedding_errors(self):
        """Test that embedding errors are propagated."""
        mock_client = MagicMock()

        with patch(
            "claude_lfr_mcp.searcher.get_qdrant_client",
            return_value=mock_client,
        ):
            with patch(
                "claude_lfr_mcp.searcher.embed_texts",
                side_effect=RuntimeError("Model loading failed"),
            ):
                with pytest.raises(RuntimeError):
                    search("test query")

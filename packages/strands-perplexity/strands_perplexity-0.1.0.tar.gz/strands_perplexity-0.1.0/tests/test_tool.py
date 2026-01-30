"""Tests for the Perplexity Search tool."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from strands_perplexity import PerplexitySearchError, perplexity_multi_search, perplexity_search
from strands_perplexity.tool import _format_results, _format_single_result, _get_api_key


class TestGetApiKey:
    """Tests for the _get_api_key function."""

    def test_returns_api_key_when_set(self, monkeypatch):
        """Test that the function returns the API key when it's set."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-api-key")
        assert _get_api_key() == "test-api-key"

    def test_raises_error_when_not_set(self, monkeypatch):
        """Test that the function raises an error when the key is not set."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        with pytest.raises(PerplexitySearchError) as exc_info:
            _get_api_key()
        assert "PERPLEXITY_API_KEY environment variable is not set" in str(exc_info.value)


class TestFormatSingleResult:
    """Tests for the _format_single_result function."""

    def test_formats_complete_result(self):
        """Test formatting a result with all fields."""
        result = {
            "title": "Test Title",
            "url": "https://example.com",
            "snippet": "Test snippet content",
            "date": "2024-01-15",
            "last_updated": "2024-01-20",
        }
        formatted = _format_single_result(result)
        assert formatted["title"] == "Test Title"
        assert formatted["url"] == "https://example.com"
        assert formatted["snippet"] == "Test snippet content"
        assert formatted["date"] == "2024-01-15"
        assert formatted["last_updated"] == "2024-01-20"

    def test_handles_missing_fields(self):
        """Test formatting a result with missing fields."""
        result = {"title": "Test Title"}
        formatted = _format_single_result(result)
        assert formatted["title"] == "Test Title"
        assert formatted["url"] == ""
        assert formatted["snippet"] == ""
        assert formatted["date"] is None
        assert formatted["last_updated"] is None


class TestFormatResults:
    """Tests for the _format_results function."""

    def test_formats_single_query_response(self):
        """Test formatting a single query response."""
        api_response = {
            "id": "test-id-123",
            "results": [
                {"title": "Result 1", "url": "https://example1.com", "snippet": "Snippet 1"},
                {"title": "Result 2", "url": "https://example2.com", "snippet": "Snippet 2"},
            ],
        }
        formatted = _format_results(api_response, "test query")
        assert formatted["query"] == "test query"
        assert formatted["search_id"] == "test-id-123"
        assert formatted["result_count"] == 2
        assert len(formatted["results"]) == 2
        assert formatted["results"][0]["title"] == "Result 1"

    def test_formats_multi_query_response(self):
        """Test formatting a multi-query response."""
        api_response = {
            "id": "test-id-456",
            "results": [
                [
                    {"title": "Query1 Result1", "url": "https://q1r1.com", "snippet": "Q1R1"},
                ],
                [
                    {"title": "Query2 Result1", "url": "https://q2r1.com", "snippet": "Q2R1"},
                    {"title": "Query2 Result2", "url": "https://q2r2.com", "snippet": "Q2R2"},
                ],
            ],
        }
        formatted = _format_results(api_response, ["query1", "query2"])
        assert formatted["query"] == ["query1", "query2"]
        assert formatted["search_id"] == "test-id-456"
        assert formatted["result_count"] == 3
        assert len(formatted["results"]) == 2
        assert len(formatted["results"][0]) == 1
        assert len(formatted["results"][1]) == 2


class TestPerplexitySearch:
    """Tests for the perplexity_search function."""

    @pytest.fixture
    def mock_api_response(self):
        """Return a mock API response."""
        return {
            "id": "search-123",
            "results": [
                {
                    "title": "AI News Article",
                    "url": "https://technews.com/ai-article",
                    "snippet": "Latest developments in AI...",
                    "date": "2024-01-15",
                    "last_updated": "2024-01-16",
                },
            ],
        }

    def test_basic_search(self, monkeypatch, mock_api_response):
        """Test a basic search request."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

        with patch("strands_perplexity.tool.httpx.Client") as mock_client_class:
            # Create a proper mock for the response
            mock_response = MagicMock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status.return_value = None

            # Set up the client mock
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = perplexity_search(query="AI news")

            assert result["query"] == "AI news"
            assert result["search_id"] == "search-123"
            assert result["result_count"] == 1
            assert result["results"][0]["title"] == "AI News Article"

    def test_search_with_all_parameters(self, monkeypatch, mock_api_response):
        """Test search with all optional parameters."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

        with patch("strands_perplexity.tool.httpx.Client") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status.return_value = None

            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            perplexity_search(
                query="AI news",
                max_results=10,
                max_tokens_per_page=1024,
                max_tokens=50000,
                search_domain_filter=["example.com"],
                search_language_filter=["en"],
                country="US",
            )

            # Verify the call was made with correct parameters
            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["query"] == "AI news"
            assert payload["max_results"] == 10
            assert payload["max_tokens_per_page"] == 1024
            assert payload["max_tokens"] == 50000
            assert payload["search_domain_filter"] == ["example.com"]
            assert payload["search_language_filter"] == ["en"]
            assert payload["country"] == "US"

    def test_search_without_api_key(self, monkeypatch):
        """Test that search fails without an API key."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)

        with pytest.raises(PerplexitySearchError) as exc_info:
            perplexity_search(query="test")
        assert "PERPLEXITY_API_KEY" in str(exc_info.value)

    def test_search_handles_http_error(self, monkeypatch):
        """Test that HTTP errors are handled properly."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

        with patch("strands_perplexity.tool.httpx.Client") as mock_client_class:
            # Create a mock that raises HTTPStatusError
            mock_request = httpx.Request("POST", "https://api.perplexity.ai/search")
            mock_response = httpx.Response(429, json={"error": "Rate limit exceeded"}, request=mock_request)

            mock_client = MagicMock()
            mock_client.post.return_value = mock_response

            def raise_for_status():
                raise httpx.HTTPStatusError(
                    "429 Too Many Requests",
                    request=mock_request,
                    response=mock_response,
                )

            mock_response.raise_for_status = raise_for_status
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            with pytest.raises(PerplexitySearchError) as exc_info:
                perplexity_search(query="test")
            assert "429" in str(exc_info.value)

    def test_search_handles_network_error(self, monkeypatch):
        """Test that network errors are handled properly."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

        with patch("strands_perplexity.tool.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.side_effect = httpx.RequestError("Connection failed")
            mock_client_class.return_value.__enter__.return_value = mock_client

            with pytest.raises(PerplexitySearchError) as exc_info:
                perplexity_search(query="test")
            assert "Network error" in str(exc_info.value)


class TestPerplexityMultiSearch:
    """Tests for the perplexity_multi_search function."""

    @pytest.fixture
    def mock_multi_response(self):
        """Return a mock multi-query API response."""
        return {
            "id": "multi-search-123",
            "results": [
                [
                    {"title": "Query1 Result", "url": "https://q1.com", "snippet": "Q1 content"},
                ],
                [
                    {"title": "Query2 Result", "url": "https://q2.com", "snippet": "Q2 content"},
                ],
            ],
        }

    def test_multi_search_basic(self, monkeypatch, mock_multi_response):
        """Test basic multi-query search."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

        with patch("strands_perplexity.tool.httpx.Client") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_multi_response
            mock_response.raise_for_status.return_value = None

            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = perplexity_multi_search(queries=["query1", "query2"])

            assert result["queries"] == ["query1", "query2"]
            assert result["search_id"] == "multi-search-123"
            assert result["result_count"] == 2
            assert len(result["results"]) == 2

    def test_multi_search_rejects_more_than_5_queries(self, monkeypatch):
        """Test that more than 5 queries are rejected."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

        with pytest.raises(ValueError) as exc_info:
            perplexity_multi_search(queries=["q1", "q2", "q3", "q4", "q5", "q6"])
        assert "Maximum of 5 queries" in str(exc_info.value)

    def test_multi_search_rejects_empty_queries(self, monkeypatch):
        """Test that empty queries list is rejected."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

        with pytest.raises(ValueError) as exc_info:
            perplexity_multi_search(queries=[])
        assert "At least one query is required" in str(exc_info.value)


class TestToolDecorator:
    """Tests to ensure the tool decorator is properly applied."""

    def test_perplexity_search_has_tool_metadata(self):
        """Test that perplexity_search has the tool decorator metadata."""
        # The @tool decorator adds specific attributes
        assert hasattr(perplexity_search, "__name__")
        assert perplexity_search.__name__ == "perplexity_search"

    def test_perplexity_multi_search_has_tool_metadata(self):
        """Test that perplexity_multi_search has the tool decorator metadata."""
        assert hasattr(perplexity_multi_search, "__name__")
        assert perplexity_multi_search.__name__ == "perplexity_multi_search"

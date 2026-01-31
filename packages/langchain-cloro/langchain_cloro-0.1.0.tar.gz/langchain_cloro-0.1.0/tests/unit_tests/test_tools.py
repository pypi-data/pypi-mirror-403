"""Unit tests for Cloro tools."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_cloro.tools import CloroSearchRun


class TestCloroSearchRun:
    """Test CloroSearchRun tool."""

    @patch("langchain_cloro.tools.initialize_client")
    def test_initialization_with_api_key(self, mock_init: MagicMock) -> None:
        """Test initialization with API key."""
        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": MagicMock(),
        }

        tool = CloroSearchRun(cloro_api_key="test-api-key")

        assert tool.name == "cloro_search"
        assert "Cloro.dev Search API" in tool.description
        mock_init.assert_called_once()

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_success(self, mock_init: MagicMock) -> None:
        """Test successful search execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [{"title": "Test Result"}]}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroSearchRun(cloro_api_key="test-api-key")
        result = tool._run(query="test query", num_results=5)

        # Verify the API call was made correctly
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/search"
        assert "params" in call_args[1]
        assert call_args[1]["params"]["query"] == "test query"
        assert call_args[1]["params"]["num_results"] == 5

        # Verify result
        assert "Test Result" in result

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_with_http_error(self, mock_init: MagicMock) -> None:
        """Test handling of HTTP errors."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=MagicMock()
        )

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroSearchRun(cloro_api_key="test-api-key")
        result = tool._run(query="test query")

        assert "Error searching with Cloro" in result

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_with_unexpected_error(self, mock_init: MagicMock) -> None:
        """Test handling of unexpected errors."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Unexpected error")

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroSearchRun(cloro_api_key="test-api-key")
        result = tool._run(query="test query")

        assert "Unexpected error" in result

    @patch("langchain_cloro.tools.initialize_client")
    def test_run_with_additional_params(self, mock_init: MagicMock) -> None:
        """Test search with additional parameters."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": mock_client,
        }

        tool = CloroSearchRun(cloro_api_key="test-api-key")
        result = tool._run(
            query="test query",
            num_results=10,
            domain="example.com",
            language="en",
        )

        # Verify additional params were passed
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["domain"] == "example.com"
        assert call_args[1]["params"]["language"] == "en"

    @patch("langchain_cloro.tools.initialize_client")
    def test_default_timeout(self, mock_init: MagicMock) -> None:
        """Test default timeout is set correctly."""
        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": MagicMock(),
        }

        tool = CloroSearchRun(cloro_api_key="test-api-key")

        # Check that initialize_client was called with default timeout
        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args[1]
        assert call_kwargs["timeout"] == 10.0

    @patch("langchain_cloro.tools.initialize_client")
    def test_custom_timeout(self, mock_init: MagicMock) -> None:
        """Test custom timeout can be set."""
        mock_init.return_value = {
            "cloro_api_key": "test-key",
            "client": MagicMock(),
        }

        tool = CloroSearchRun(cloro_api_key="test-api-key", timeout=30.0)

        # Check that initialize_client was called with custom timeout
        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args[1]
        assert call_kwargs["timeout"] == 30.0

"""Shared test fixtures for the Canny SDK."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from canny import CannyClient


@pytest.fixture
def mock_api_key() -> str:
    """Return a mock API key for unit tests."""
    return "test_api_key_12345"


@pytest.fixture
def mock_http_client() -> Generator[MagicMock, None, None]:
    """Create a mock HTTP client for unit tests."""
    with patch("canny.http.CannyHTTPClient") as mock:
        yield mock


@pytest.fixture
def mock_client(mock_api_key: str) -> Generator[CannyClient, None, None]:
    """Create a client with mocked HTTP for unit tests."""
    with patch("canny.client.CannyHTTPClient") as mock_http:
        # Configure mock to return itself
        mock_instance = MagicMock()
        mock_http.return_value = mock_instance

        client = CannyClient(api_key=mock_api_key)
        client._http = mock_instance
        yield client

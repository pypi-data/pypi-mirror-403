"""Integration test fixtures.

IMPORTANT: Integration tests are READ-ONLY. They should never modify
production data.
"""

import os
from collections.abc import Generator

import pytest

from canny import CannyClient


@pytest.fixture
def live_client() -> Generator[CannyClient, None, None]:
    """Create a client connected to the real Canny API.

    This fixture:
    - Requires CANNY_API_KEY environment variable
    - Creates a client in read_only=True mode (enforced)
    - Skips tests if no API key is available

    IMPORTANT: This client is read-only. Write operations will raise errors.
    """
    api_key = os.environ.get("CANNY_API_KEY")
    if not api_key:
        pytest.skip("CANNY_API_KEY environment variable not set")

    # Always use read_only=True for integration tests
    client = CannyClient(api_key=api_key, read_only=True)
    yield client
    client.close()

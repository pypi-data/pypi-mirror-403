"""Configuration management for the Canny SDK."""

import os
from dataclasses import dataclass, field
from typing import Optional

from .exceptions import CannyValidationError


@dataclass
class CannyConfig:
    """Configuration for the Canny client.

    Attributes:
        api_key: Your Canny API key. If not provided, reads from CANNY_API_KEY env var.
        base_url_v1: Base URL for v1 API endpoints.
        base_url_v2: Base URL for v2 API endpoints.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retries for failed requests.
        read_only: If True, blocks all write operations (create, update, delete).
                   Defaults to True for safety with production data.
    """

    api_key: Optional[str] = None
    base_url_v1: str = "https://canny.io/api/v1/"
    base_url_v2: str = "https://canny.io/api/v2/"
    timeout: float = 30.0
    max_retries: int = 3
    read_only: bool = field(default=True)

    def __post_init__(self) -> None:
        # Try to get API key from environment if not provided
        if self.api_key is None:
            self.api_key = os.environ.get("CANNY_API_KEY")

        if self.api_key is None:
            raise CannyValidationError(
                "API key is required. Set CANNY_API_KEY env var or pass api_key directly."
            )

        # Ensure base URLs end with /
        if not self.base_url_v1.endswith("/"):
            self.base_url_v1 += "/"
        if not self.base_url_v2.endswith("/"):
            self.base_url_v2 += "/"

    def get_url(self, endpoint: str, api_version: int = 1) -> str:
        """Get the full URL for an endpoint.

        Args:
            endpoint: The API endpoint path (e.g., "boards/list").
            api_version: The API version to use (1 or 2).

        Returns:
            The full URL for the endpoint.
        """
        base_url = self.base_url_v1 if api_version == 1 else self.base_url_v2
        # Remove leading slash from endpoint if present
        endpoint = endpoint.lstrip("/")
        return f"{base_url}{endpoint}"

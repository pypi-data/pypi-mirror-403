"""HTTP transport layer for the Canny SDK."""

from typing import Any, Optional

import httpx

from .config import CannyConfig
from .exceptions import (
    CannyAPIError,
    CannyAuthenticationError,
    CannyNotFoundError,
    CannyRateLimitError,
)


class CannyHTTPClient:
    """Synchronous HTTP client for Canny API."""

    def __init__(self, config: CannyConfig):
        self._config = config
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=self._config.timeout)
        return self._client

    def post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        api_version: int = 1,
    ) -> dict[str, Any]:
        """Make an authenticated POST request to the Canny API.

        Args:
            endpoint: The API endpoint path (e.g., "boards/list").
            data: Additional data to send in the request body.
            api_version: The API version to use (1 or 2).

        Returns:
            The JSON response from the API.

        Raises:
            CannyAuthenticationError: If the API key is invalid.
            CannyNotFoundError: If the requested resource is not found.
            CannyRateLimitError: If the rate limit is exceeded.
            CannyAPIError: For other API errors.
        """
        url = self._config.get_url(endpoint, api_version)

        # Build request body with API key
        body: dict[str, Any] = {"apiKey": self._config.api_key}
        if data:
            body.update(data)

        client = self._get_client()
        response = client.post(
            url,
            json=body,
            headers={"Content-Type": "application/json"},
        )

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle the API response and raise appropriate exceptions."""
        try:
            data = response.json()
        except Exception:
            data = {"error": response.text}

        if response.status_code == 200:
            return data

        error_message = data.get("error", str(data))

        if response.status_code == 401:
            raise CannyAuthenticationError(
                message=error_message,
                status_code=response.status_code,
                response_body=data,
            )
        elif response.status_code == 404:
            raise CannyNotFoundError(
                message=error_message,
                status_code=response.status_code,
                response_body=data,
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise CannyRateLimitError(
                message=error_message,
                status_code=response.status_code,
                response_body=data,
                retry_after=int(retry_after) if retry_after else None,
            )
        else:
            raise CannyAPIError(
                message=error_message,
                status_code=response.status_code,
                response_body=data,
            )

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "CannyHTTPClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class CannyAsyncHTTPClient:
    """Asynchronous HTTP client for Canny API."""

    def __init__(self, config: CannyConfig):
        self._config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._config.timeout)
        return self._client

    async def post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        api_version: int = 1,
    ) -> dict[str, Any]:
        """Make an authenticated POST request to the Canny API.

        Args:
            endpoint: The API endpoint path (e.g., "boards/list").
            data: Additional data to send in the request body.
            api_version: The API version to use (1 or 2).

        Returns:
            The JSON response from the API.

        Raises:
            CannyAuthenticationError: If the API key is invalid.
            CannyNotFoundError: If the requested resource is not found.
            CannyRateLimitError: If the rate limit is exceeded.
            CannyAPIError: For other API errors.
        """
        url = self._config.get_url(endpoint, api_version)

        # Build request body with API key
        body: dict[str, Any] = {"apiKey": self._config.api_key}
        if data:
            body.update(data)

        client = await self._get_client()
        response = await client.post(
            url,
            json=body,
            headers={"Content-Type": "application/json"},
        )

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle the API response and raise appropriate exceptions."""
        try:
            data = response.json()
        except Exception:
            data = {"error": response.text}

        if response.status_code == 200:
            return data

        error_message = data.get("error", str(data))

        if response.status_code == 401:
            raise CannyAuthenticationError(
                message=error_message,
                status_code=response.status_code,
                response_body=data,
            )
        elif response.status_code == 404:
            raise CannyNotFoundError(
                message=error_message,
                status_code=response.status_code,
                response_body=data,
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise CannyRateLimitError(
                message=error_message,
                status_code=response.status_code,
                response_body=data,
                retry_after=int(retry_after) if retry_after else None,
            )
        else:
            raise CannyAPIError(
                message=error_message,
                status_code=response.status_code,
                response_body=data,
            )

    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "CannyAsyncHTTPClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

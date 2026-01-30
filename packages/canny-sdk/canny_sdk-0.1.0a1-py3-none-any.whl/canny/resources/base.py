"""Base resource class for the Canny SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..exceptions import CannyReadOnlyError

if TYPE_CHECKING:
    from ..config import CannyConfig
    from ..http import CannyAsyncHTTPClient, CannyHTTPClient


class BaseResource:
    """Base class for all API resources.

    Provides common functionality for making API requests and
    enforcing read-only mode.
    """

    def __init__(
        self,
        http_client: CannyHTTPClient,
        config: CannyConfig,
    ):
        """Initialize the resource.

        Args:
            http_client: The HTTP client to use for requests.
            config: The SDK configuration.
        """
        self._http = http_client
        self._config = config

    def _check_write_allowed(self, operation: str) -> None:
        """Check if write operations are allowed.

        Args:
            operation: Description of the write operation.

        Raises:
            CannyReadOnlyError: If the client is in read-only mode.
        """
        if self._config.read_only:
            raise CannyReadOnlyError(operation)


class BaseAsyncResource:
    """Base class for async API resources.

    Provides common functionality for making async API requests and
    enforcing read-only mode.
    """

    def __init__(
        self,
        http_client: CannyAsyncHTTPClient,
        config: CannyConfig,
    ):
        """Initialize the resource.

        Args:
            http_client: The async HTTP client to use for requests.
            config: The SDK configuration.
        """
        self._http = http_client
        self._config = config

    def _check_write_allowed(self, operation: str) -> None:
        """Check if write operations are allowed.

        Args:
            operation: Description of the write operation.

        Raises:
            CannyReadOnlyError: If the client is in read-only mode.
        """
        if self._config.read_only:
            raise CannyReadOnlyError(operation)

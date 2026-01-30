"""Unofficial Python SDK for Canny API.

This SDK provides both synchronous and asynchronous clients for interacting
with the Canny API.

Example:
    ```python
    from canny import CannyClient

    # Initialize client (reads CANNY_API_KEY from environment)
    client = CannyClient()

    # List all boards
    boards = client.boards.list()
    for board in boards.boards:
        print(f"{board.name}: {board.post_count} posts")

    # List posts with automatic pagination
    for post in client.posts.list_all(board_id="..."):
        print(post.title)
    ```

Safety Features:
    The client defaults to read_only=True, which blocks all write operations.
    This is a safety feature to prevent accidental modifications to production data.

    To enable write operations:
    ```python
    client = CannyClient(read_only=False)
    ```
"""

from .async_client import CannyAsyncClient
from .client import CannyClient
from .config import CannyConfig
from .exceptions import (
    CannyAPIError,
    CannyAuthenticationError,
    CannyError,
    CannyNotFoundError,
    CannyRateLimitError,
    CannyReadOnlyError,
    CannyValidationError,
    CannyWebhookVerificationError,
)
from .webhooks import WebhookVerifier, verify_webhook

__version__ = "0.1.0a1"

__all__ = [
    # Clients
    "CannyClient",
    "CannyAsyncClient",
    # Configuration
    "CannyConfig",
    # Exceptions
    "CannyError",
    "CannyAPIError",
    "CannyAuthenticationError",
    "CannyNotFoundError",
    "CannyRateLimitError",
    "CannyValidationError",
    "CannyReadOnlyError",
    "CannyWebhookVerificationError",
    # Webhooks
    "WebhookVerifier",
    "verify_webhook",
]

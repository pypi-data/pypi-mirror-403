"""Webhook verification utilities for the Canny SDK."""

import base64
import hashlib
import hmac
import time
from typing import Optional

from .exceptions import CannyWebhookVerificationError
from .models.webhooks import WebhookEvent


class WebhookVerifier:
    """Utility for verifying Canny webhook signatures.

    Example:
        ```python
        from canny import WebhookVerifier

        verifier = WebhookVerifier(api_key="your_api_key")

        # In your webhook handler (Flask example)
        @app.route("/webhook", methods=["POST"])
        def handle_webhook():
            try:
                verifier.verify(
                    nonce=request.headers.get("Canny-Nonce"),
                    signature=request.headers.get("Canny-Signature"),
                    timestamp=int(request.headers.get("Canny-Timestamp", 0))
                )
            except CannyWebhookVerificationError as e:
                return {"error": str(e)}, 401

            event = verifier.parse_event(request.json)
            # Handle the event...
            return {"status": "ok"}
        ```
    """

    def __init__(self, api_key: str):
        """Initialize the webhook verifier.

        Args:
            api_key: Your Canny API key.
        """
        self._api_key = api_key

    def verify(
        self,
        nonce: Optional[str],
        signature: Optional[str],
        timestamp: Optional[int] = None,
        max_age_seconds: int = 300,
    ) -> bool:
        """Verify a webhook signature.

        Args:
            nonce: Value from Canny-Nonce header.
            signature: Value from Canny-Signature header.
            timestamp: Value from Canny-Timestamp header (milliseconds since epoch).
            max_age_seconds: Maximum age of webhook to accept (default: 5 minutes).

        Returns:
            True if the signature is valid.

        Raises:
            CannyWebhookVerificationError: If verification fails.
        """
        if not nonce:
            raise CannyWebhookVerificationError("Missing Canny-Nonce header")
        if not signature:
            raise CannyWebhookVerificationError("Missing Canny-Signature header")

        # Calculate expected signature
        expected = base64.b64encode(
            hmac.new(
                self._api_key.encode(),
                nonce.encode(),
                hashlib.sha256,
            ).digest()
        ).decode()

        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(signature, expected):
            raise CannyWebhookVerificationError("Invalid signature")

        # Check timestamp for replay protection
        if timestamp:
            current_time_ms = int(time.time() * 1000)
            age_ms = current_time_ms - timestamp
            max_age_ms = max_age_seconds * 1000

            if age_ms > max_age_ms:
                raise CannyWebhookVerificationError(
                    f"Webhook too old (age: {age_ms}ms, max: {max_age_ms}ms)"
                )
            if age_ms < 0:
                raise CannyWebhookVerificationError("Webhook timestamp is in the future")

        return True

    def parse_event(self, payload: dict) -> WebhookEvent:
        """Parse a webhook payload into a typed event object.

        Args:
            payload: The JSON payload from the webhook.

        Returns:
            A WebhookEvent object.
        """
        return WebhookEvent.model_validate(payload)


def verify_webhook(
    api_key: str,
    nonce: Optional[str],
    signature: Optional[str],
    timestamp: Optional[int] = None,
    max_age_seconds: int = 300,
) -> bool:
    """Standalone function to verify a webhook signature.

    Args:
        api_key: Your Canny API key.
        nonce: Value from Canny-Nonce header.
        signature: Value from Canny-Signature header.
        timestamp: Value from Canny-Timestamp header (milliseconds).
        max_age_seconds: Maximum age of webhook to accept.

    Returns:
        True if the signature is valid.

    Raises:
        CannyWebhookVerificationError: If verification fails.

    Example:
        ```python
        from canny import verify_webhook

        # In your webhook handler
        is_valid = verify_webhook(
            api_key="your_api_key",
            nonce=request.headers.get("Canny-Nonce"),
            signature=request.headers.get("Canny-Signature"),
            timestamp=int(request.headers.get("Canny-Timestamp", 0))
        )
        ```
    """
    return WebhookVerifier(api_key).verify(nonce, signature, timestamp, max_age_seconds)

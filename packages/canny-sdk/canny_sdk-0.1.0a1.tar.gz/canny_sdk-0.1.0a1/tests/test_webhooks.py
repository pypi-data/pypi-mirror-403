"""Unit tests for webhook verification."""

import base64
import hashlib
import hmac
import time

import pytest

from canny import WebhookVerifier, verify_webhook
from canny.exceptions import CannyWebhookVerificationError


class TestWebhookVerification:
    """Test webhook signature verification."""

    def test_valid_signature(self) -> None:
        """Test verification of a valid signature."""
        api_key = "test_api_key"
        nonce = "test_nonce_value"

        # Calculate expected signature
        expected_sig = base64.b64encode(
            hmac.new(api_key.encode(), nonce.encode(), hashlib.sha256).digest()
        ).decode()

        # Should not raise
        result = verify_webhook(api_key, nonce, expected_sig)
        assert result is True

    def test_invalid_signature(self) -> None:
        """Test that invalid signatures are rejected."""
        with pytest.raises(CannyWebhookVerificationError, match="Invalid signature"):
            verify_webhook("api_key", "nonce", "invalid_signature_12345")

    def test_missing_nonce(self) -> None:
        """Test that missing nonce is rejected."""
        with pytest.raises(CannyWebhookVerificationError, match="Missing Canny-Nonce"):
            verify_webhook("api_key", None, "some_signature")

    def test_missing_signature(self) -> None:
        """Test that missing signature is rejected."""
        with pytest.raises(CannyWebhookVerificationError, match="Missing Canny-Signature"):
            verify_webhook("api_key", "some_nonce", None)

    def test_expired_webhook(self) -> None:
        """Test that old webhooks are rejected."""
        api_key = "test_api_key"
        nonce = "test_nonce"
        sig = base64.b64encode(
            hmac.new(api_key.encode(), nonce.encode(), hashlib.sha256).digest()
        ).decode()

        # Timestamp from 10 minutes ago
        old_timestamp = int((time.time() - 600) * 1000)

        with pytest.raises(CannyWebhookVerificationError, match="too old"):
            verify_webhook(api_key, nonce, sig, timestamp=old_timestamp, max_age_seconds=300)

    def test_future_timestamp(self) -> None:
        """Test that future timestamps are rejected."""
        api_key = "test_api_key"
        nonce = "test_nonce"
        sig = base64.b64encode(
            hmac.new(api_key.encode(), nonce.encode(), hashlib.sha256).digest()
        ).decode()

        # Timestamp from the future
        future_timestamp = int((time.time() + 3600) * 1000)

        with pytest.raises(CannyWebhookVerificationError, match="future"):
            verify_webhook(api_key, nonce, sig, timestamp=future_timestamp)

    def test_valid_with_timestamp(self) -> None:
        """Test verification with valid timestamp."""
        api_key = "test_api_key"
        nonce = "test_nonce"
        sig = base64.b64encode(
            hmac.new(api_key.encode(), nonce.encode(), hashlib.sha256).digest()
        ).decode()

        # Current timestamp
        current_timestamp = int(time.time() * 1000)

        result = verify_webhook(api_key, nonce, sig, timestamp=current_timestamp)
        assert result is True


class TestWebhookVerifierClass:
    """Test the WebhookVerifier class."""

    def test_parse_event(self) -> None:
        """Test parsing a webhook event."""
        verifier = WebhookVerifier("test_api_key")

        payload = {
            "created": "2024-01-26T12:00:00.000Z",
            "object": {"id": "123", "title": "Test Post"},
            "objectType": "post",
            "type": "post.created",
        }

        event = verifier.parse_event(payload)

        assert event.type == "post.created"
        assert event.object_type == "post"
        assert event.object["id"] == "123"

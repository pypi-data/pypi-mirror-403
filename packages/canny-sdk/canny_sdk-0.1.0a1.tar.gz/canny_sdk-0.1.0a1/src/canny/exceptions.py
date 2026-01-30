"""Custom exceptions for the Canny SDK."""

from typing import Optional


class CannyError(Exception):
    """Base exception for all Canny SDK errors."""

    pass


class CannyAPIError(CannyError):
    """API returned an error response."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[dict] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class CannyAuthenticationError(CannyAPIError):
    """Invalid or missing API key."""

    pass


class CannyNotFoundError(CannyAPIError):
    """Requested resource not found."""

    pass


class CannyRateLimitError(CannyAPIError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[dict] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message, status_code, response_body)
        self.retry_after = retry_after


class CannyValidationError(CannyError):
    """Request validation failed (client-side)."""

    pass


class CannyReadOnlyError(CannyError):
    """Attempted write operation in read-only mode."""

    def __init__(self, operation: str):
        self.operation = operation
        super().__init__(f"Cannot {operation} in read-only mode")


class CannyWebhookVerificationError(CannyError):
    """Webhook signature verification failed."""

    pass

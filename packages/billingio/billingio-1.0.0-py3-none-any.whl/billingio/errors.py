"""Exception types for the billing.io SDK."""

from __future__ import annotations

from typing import Optional


class BillingIOError(Exception):
    """Raised when the billing.io API returns a structured error response.

    Attributes:
        type: Machine-readable error category (e.g. ``"invalid_request"``).
        code: Machine-readable error code (e.g. ``"missing_required_field"``).
        status_code: HTTP status code of the response.
        message: Human-readable description of the error.
        param: The request parameter that caused the error, if applicable.
    """

    def __init__(
        self,
        message: str,
        *,
        type: str = "unknown_error",
        code: str = "unknown",
        status_code: int = 0,
        param: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.type = type
        self.code = code
        self.status_code = status_code
        self.message = message
        self.param = param

    def __repr__(self) -> str:
        return (
            f"BillingIOError(type={self.type!r}, code={self.code!r}, "
            f"status_code={self.status_code!r}, message={self.message!r}, "
            f"param={self.param!r})"
        )


class WebhookVerificationError(Exception):
    """Raised when webhook signature verification fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

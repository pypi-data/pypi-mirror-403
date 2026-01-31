"""
Custom exception classes for Veri SDK
"""

from __future__ import annotations


class VeriError(Exception):
    """Base exception for all Veri errors"""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class VeriAPIError(VeriError):
    """Exception raised when the API returns an error response"""

    def __init__(
        self,
        message: str,
        status_code: int,
        code: str,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.request_id = request_id

    @property
    def is_retryable(self) -> bool:
        """Whether the error is retryable"""
        return (
            self.status_code >= 500
            or self.status_code == 429
            or self.code in ("RATE_LIMITED", "SERVICE_UNAVAILABLE")
        )

    def __str__(self) -> str:
        base = f"[{self.code}] {self.message} (HTTP {self.status_code})"
        if self.request_id:
            base += f" [Request ID: {self.request_id}]"
        return base


class VeriValidationError(VeriError):
    """Exception raised when input validation fails"""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field

    def __str__(self) -> str:
        if self.field:
            return f"Validation error on '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


class VeriTimeoutError(VeriError):
    """Exception raised when a request times out"""

    def __init__(self, message: str, timeout_ms: int) -> None:
        super().__init__(message)
        self.timeout_ms = timeout_ms

    def __str__(self) -> str:
        return f"Timeout after {self.timeout_ms}ms: {self.message}"


class VeriRateLimitError(VeriAPIError):
    """Exception raised when rate limit is exceeded"""

    def __init__(
        self,
        message: str,
        retry_after: int,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, 429, "RATE_LIMITED", request_id)
        self.retry_after = retry_after

    def __str__(self) -> str:
        return f"Rate limited. Retry after {self.retry_after} seconds: {self.message}"


class VeriInsufficientCreditsError(VeriAPIError):
    """Exception raised when user has insufficient credits (402 Payment Required)"""

    def __init__(
        self,
        message: str,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, 402, "INSUFFICIENT_CREDITS", request_id)

    def __str__(self) -> str:
        return f"Insufficient credits: {self.message}"

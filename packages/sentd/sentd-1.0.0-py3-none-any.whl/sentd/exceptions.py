"""Custom exceptions for the SENTD SDK."""

from typing import Any, Optional


class SentdError(Exception):
    """Base exception for all SENTD errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(SentdError):
    """Raised when authentication fails (401)."""

    def __init__(self, message: str = "Invalid API key") -> None:
        super().__init__(message, status_code=401)


class RateLimitError(SentdError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ValidationError(SentdError):
    """Raised when request validation fails (400)."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message, status_code=400, details=details)


class NotFoundError(SentdError):
    """Raised when a resource is not found (404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)

"""Precogs SDK exception classes."""


class PrecogsError(Exception):
    """Base exception for all Precogs SDK errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(PrecogsError):
    """Raised when API key is invalid or missing."""

    pass


class RateLimitError(PrecogsError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class NotFoundError(PrecogsError):
    """Raised when a requested resource is not found."""

    pass


class ValidationError(PrecogsError):
    """Raised when request validation fails."""

    pass


class InsufficientTokensError(PrecogsError):
    """Raised when user has insufficient tokens for the operation."""

    pass


class ServerError(PrecogsError):
    """Raised when server returns 5xx error."""

    pass

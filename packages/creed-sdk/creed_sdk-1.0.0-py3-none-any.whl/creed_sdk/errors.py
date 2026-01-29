"""
Error definitions for Creed Space SDK.
"""


class CreedError(Exception):
    """Base error for Creed SDK."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.code}:{self.status_code}] {self.message}"
        return f"[{self.code}] {self.message}"


class AuthenticationError(CreedError):
    """Error for authentication failures."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR", 401)


class RateLimitError(CreedError):
    """Error for rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        super().__init__(message, "RATE_LIMIT", 429)
        self.retry_after = retry_after


class TimeoutError(CreedError):
    """Error for request timeout."""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message, "TIMEOUT")


class ValidationError(CreedError):
    """Error for validation failures."""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 400)

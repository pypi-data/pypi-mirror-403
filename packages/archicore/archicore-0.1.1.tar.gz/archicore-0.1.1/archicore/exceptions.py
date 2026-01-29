"""
ArchiCore SDK Exceptions
"""


class ArchiCoreError(Exception):
    """Base exception for ArchiCore SDK errors."""

    def __init__(self, message: str, code: str = None, status_code: int = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class AuthenticationError(ArchiCoreError):
    """Raised when authentication fails (401)."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)


class RateLimitError(ArchiCoreError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = None,
        limit: int = None,
        remaining: int = None,
    ):
        super().__init__(message, code="RATE_LIMITED", status_code=429)
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining


class NotFoundError(ArchiCoreError):
    """Raised when a resource is not found (404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="NOT_FOUND", status_code=404)


class ValidationError(ArchiCoreError):
    """Raised when request validation fails (400)."""

    def __init__(self, message: str = "Invalid request parameters"):
        super().__init__(message, code="VALIDATION_ERROR", status_code=400)


class ServerError(ArchiCoreError):
    """Raised when server returns 5xx error."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, code="SERVER_ERROR", status_code=500)

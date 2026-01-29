"""Custom exceptions for the PyBob SDK."""

from typing import Any


class BobAPIError(Exception):
    """Base exception for all Bob API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class BobAuthenticationError(BobAPIError):
    """Raised when authentication fails (401)."""

    def __init__(
        self,
        message: str = "Authentication failed. Check your service account credentials.",
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=401, response_body=response_body)


class BobForbiddenError(BobAPIError):
    """Raised when access is forbidden (403)."""

    def __init__(
        self,
        message: str = "Access forbidden. Check your permissions.",
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=403, response_body=response_body)


class BobNotFoundError(BobAPIError):
    """Raised when a resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found.",
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=404, response_body=response_body)


class BobValidationError(BobAPIError):
    """Raised when request validation fails (400)."""

    def __init__(
        self,
        message: str = "Request validation failed.",
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=400, response_body=response_body)


class BobRateLimitError(BobAPIError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please retry later.",
        retry_after: int | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=429, response_body=response_body)
        self.retry_after = retry_after


class BobServerError(BobAPIError):
    """Raised when a server error occurs (5xx)."""

    def __init__(
        self,
        message: str = "Server error occurred.",
        status_code: int = 500,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)

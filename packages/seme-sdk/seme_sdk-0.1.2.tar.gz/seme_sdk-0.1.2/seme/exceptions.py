"""Custom exceptions for SecondMe SDK."""

from typing import Any, Optional


class SecondMeError(Exception):
    """Base exception for all SecondMe SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(SecondMeError):
    """Authentication failed (401)."""

    pass


class PermissionDeniedError(SecondMeError):
    """Permission denied (403)."""

    pass


class NotFoundError(SecondMeError):
    """Resource not found (404)."""

    pass


class InvalidParameterError(SecondMeError):
    """Invalid parameter (400)."""

    pass


class RateLimitError(SecondMeError):
    """Rate limit exceeded (429)."""

    pass


class ServerError(SecondMeError):
    """Server error (5xx)."""

    pass


class TokenExpiredError(AuthenticationError):
    """Access token has expired."""

    pass

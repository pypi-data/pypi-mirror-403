"""
Cubit API Exceptions.

Custom exception classes for handling API errors in a Pythonic way.
"""

from typing import Optional, Dict, Any


class CubitError(Exception):
    """Base exception for all Cubit API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(CubitError):
    """Raised when API key is invalid or missing."""
    pass


class AuthorizationError(CubitError):
    """Raised when API key lacks permission for the requested resource."""
    pass


class NotFoundError(CubitError):
    """Raised when the requested resource doesn't exist."""
    pass


class RateLimitError(CubitError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 429,
        response_body: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message, status_code, response_body)
        self.retry_after = retry_after


class ValidationError(CubitError):
    """Raised when request parameters are invalid."""
    pass


class ServerError(CubitError):
    """Raised when the API returns a 5xx error."""
    pass


"""Exception classes for the MemoryLayer SDK."""

from typing import Any, Dict, List, Optional


class MemoryLayerError(Exception):
    """Base exception for all MemoryLayer SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.details = details


class AuthenticationError(MemoryLayerError):
    """Raised when authentication fails (401)."""

    def __init__(self, message: str, request_id: Optional[str] = None):
        super().__init__(message, status_code=401, request_id=request_id)


class RateLimitError(MemoryLayerError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, message: str, retry_after: int, request_id: Optional[str] = None):
        super().__init__(message, status_code=429, request_id=request_id)
        self.retry_after = retry_after


class ValidationError(MemoryLayerError):
    """Raised when request validation fails (400)."""

    def __init__(
        self,
        message: str,
        errors: List[Dict[str, str]],
        request_id: Optional[str] = None,
    ):
        super().__init__(message, status_code=400, request_id=request_id)
        self.errors = errors


class NetworkError(MemoryLayerError):
    """Raised when network request fails."""

    def __init__(self, message: str, cause: Exception):
        super().__init__(message)
        self.cause = cause


class APIError(MemoryLayerError):
    """Raised for other API errors."""

    def __init__(
        self,
        message: str,
        status_code: int,
        request_id: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message, status_code, request_id, details)

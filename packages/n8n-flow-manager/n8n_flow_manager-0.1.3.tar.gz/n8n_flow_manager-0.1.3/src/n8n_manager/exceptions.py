"""Custom exceptions for n8n-flow-manager."""

from typing import Any, Dict, Optional


class N8NError(Exception):
    """Base exception for all n8n-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class N8NAuthError(N8NError):
    """Raised when authentication fails (invalid API key, expired token, etc.)."""

    pass


class N8NNotFoundError(N8NError):
    """Raised when a requested resource is not found (404)."""

    pass


class N8NValidationError(N8NError):
    """Raised when request validation fails (invalid workflow structure, etc.)."""

    pass


class N8NAPIError(N8NError):
    """Raised when the n8n API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.response = response or {}
        super().__init__(message, details={"status_code": status_code, "response": response})


class N8NTimeoutError(N8NError):
    """Raised when a request or polling operation times out."""

    pass


class N8NRateLimitError(N8NError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, details={"retry_after": retry_after})

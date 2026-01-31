"""
OpenAI-compatible error classes.

These error classes match OpenAI's SDK error hierarchy for drop-in compatibility.
"""

from typing import Any, Dict, Optional


class APIError(Exception):
    """Base exception for all API errors."""

    def __init__(
        self,
        message: str,
        status: Optional[int] = None,
        code: Optional[str] = None,
        param: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.param = param
        self.type = error_type


class AuthenticationError(APIError):
    """Exception for authentication failures (401)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status=401,
            code="invalid_api_key",
            error_type="authentication_error",
        )


class RateLimitError(APIError):
    """Exception for rate limit errors (429)."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status=429,
            code="rate_limit_exceeded",
            error_type="rate_limit_error",
        )


class BadRequestError(APIError):
    """Exception for bad request errors (400)."""

    def __init__(self, message: str = "Bad request", param: Optional[str] = None):
        super().__init__(
            message=message,
            status=400,
            code="invalid_request_error",
            param=param,
            error_type="invalid_request_error",
        )


class NotFoundError(APIError):
    """Exception for not found errors (404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status=404,
            code="not_found",
            error_type="invalid_request_error",
        )


class InternalServerError(APIError):
    """Exception for internal server errors (500+)."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            message=message,
            status=500,
            code="internal_error",
            error_type="internal_server_error",
        )


def create_error_from_response(
    status: int,
    message: str,
    error_data: Optional[Dict[str, Any]] = None,
) -> APIError:
    """
    Create an appropriate error class based on HTTP status code.

    Args:
        status: HTTP status code
        message: Error message
        error_data: Additional error data (code, param, type)

    Returns:
        An appropriate APIError subclass instance
    """
    param = error_data.get("param") if error_data else None
    code = error_data.get("code") if error_data else None
    error_type = error_data.get("type") if error_data else None

    if status == 401:
        return AuthenticationError(message)
    elif status == 429:
        return RateLimitError(message)
    elif status == 400:
        return BadRequestError(message, param=param)
    elif status == 404:
        return NotFoundError(message)
    elif status >= 500:
        return InternalServerError(message)
    else:
        return APIError(message, status=status, code=code, param=param, error_type=error_type)

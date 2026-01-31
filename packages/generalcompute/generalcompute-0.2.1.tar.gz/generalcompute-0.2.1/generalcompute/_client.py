"""
Core HTTP clients for making requests to the GeneralCompute API.
"""

import asyncio
import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx

from ._errors import create_error_from_response

DEFAULT_BASE_URL = "https://api.generalcompute.com/v1"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2


class BaseClient:
    """Synchronous HTTP client for GeneralCompute API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        self.api_key = api_key or os.getenv("GENERALCOMPUTE_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "API key is required. Pass it as api_key or set GENERALCOMPUTE_API_KEY "
                "environment variable."
            )

        self.base_url = base_url or DEFAULT_BASE_URL
        self.timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else DEFAULT_MAX_RETRIES
        self.default_headers = default_headers or {}

        self._client = httpx.Client(timeout=self.timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> Any:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API endpoint path
            body: Request body
            headers: Additional headers
            stream: Whether to return a streaming response

        Returns:
            Response data (JSON parsed or httpx.Response for streaming)
        """
        retries = 0 if stream else self.max_retries
        last_error = None

        for attempt in range(retries + 1):
            try:
                return self._make_request(method, path, body, headers, stream)
            except Exception as error:
                last_error = error

                # Don't retry on client errors (4xx) except 429
                if isinstance(error, httpx.HTTPStatusError):
                    if 400 <= error.response.status_code < 500 and error.response.status_code != 429:
                        raise

                # Re-raise APIError immediately
                if hasattr(error, 'status'):
                    raise

                # Don't retry on last attempt
                if attempt == retries:
                    raise

                # Exponential backoff
                delay = min(2 ** attempt, 10)
                import time
                time.sleep(delay)

        raise last_error  # type: ignore

    def _make_request(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> Any:
        """Make a single HTTP request."""
        url = urljoin(self.base_url, path)

        request_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.default_headers,
            **(headers or {}),
        }

        kwargs: Dict[str, Any] = {
            "method": method,
            "url": url,
            "headers": request_headers,
        }

        if body is not None:
            kwargs["json"] = body

        response = self._client.request(**kwargs)

        # For streaming responses, return the response object
        if stream:
            if not response.is_success:
                self._handle_error_response(response)
            return response

        # For non-streaming responses, parse JSON
        if not response.is_success:
            self._handle_error_response(response)

        try:
            return response.json()
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse response: {response.text}")

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API."""
        message = f"HTTP {response.status_code} error"
        error_data = None

        try:
            parsed = response.json()
            if "error" in parsed:
                message = parsed["error"].get("message", message)
                error_data = {
                    "code": parsed["error"].get("code"),
                    "param": parsed["error"].get("param"),
                    "type": parsed["error"].get("type"),
                }
        except Exception:
            message = response.text or message

        raise create_error_from_response(response.status_code, message, error_data)


class AsyncBaseClient:
    """Asynchronous HTTP client for GeneralCompute API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        self.api_key = api_key or os.getenv("GENERALCOMPUTE_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "API key is required. Pass it as api_key or set GENERALCOMPUTE_API_KEY "
                "environment variable."
            )

        self.base_url = base_url or DEFAULT_BASE_URL
        self.timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else DEFAULT_MAX_RETRIES
        self.default_headers = default_headers or {}

        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> Any:
        """
        Make an async HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API endpoint path
            body: Request body
            headers: Additional headers
            stream: Whether to return a streaming response

        Returns:
            Response data (JSON parsed or httpx.Response for streaming)
        """
        retries = 0 if stream else self.max_retries
        last_error = None

        for attempt in range(retries + 1):
            try:
                return await self._make_request(method, path, body, headers, stream)
            except Exception as error:
                last_error = error

                # Don't retry on client errors (4xx) except 429
                if isinstance(error, httpx.HTTPStatusError):
                    if 400 <= error.response.status_code < 500 and error.response.status_code != 429:
                        raise

                # Re-raise APIError immediately
                if hasattr(error, 'status'):
                    raise

                # Don't retry on last attempt
                if attempt == retries:
                    raise

                # Exponential backoff
                delay = min(2 ** attempt, 10)
                await asyncio.sleep(delay)

        raise last_error  # type: ignore

    async def _make_request(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> Any:
        """Make a single async HTTP request."""
        url = urljoin(self.base_url, path)

        request_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.default_headers,
            **(headers or {}),
        }

        kwargs: Dict[str, Any] = {
            "method": method,
            "url": url,
            "headers": request_headers,
        }

        if body is not None:
            kwargs["json"] = body

        response = await self._client.request(**kwargs)

        # For streaming responses, return the response object
        if stream:
            if not response.is_success:
                await self._handle_error_response(response)
            return response

        # For non-streaming responses, parse JSON
        if not response.is_success:
            await self._handle_error_response(response)

        try:
            return response.json()
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse response: {response.text}")

    async def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API."""
        message = f"HTTP {response.status_code} error"
        error_data = None

        try:
            parsed = response.json()
            if "error" in parsed:
                message = parsed["error"].get("message", message)
                error_data = {
                    "code": parsed["error"].get("code"),
                    "param": parsed["error"].get("param"),
                    "type": parsed["error"].get("type"),
                }
        except Exception:
            message = response.text or message

        raise create_error_from_response(response.status_code, message, error_data)

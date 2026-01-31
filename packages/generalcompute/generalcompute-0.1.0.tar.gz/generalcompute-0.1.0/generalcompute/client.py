"""
GeneralCompute API client.

OpenAI-compatible client for the GeneralCompute API.
"""

import os
from typing import Dict, Optional

from ._client import AsyncBaseClient, BaseClient
from .resources.chat.completions import AsyncCompletions, Completions
from .resources.models import AsyncModels, Models


class Chat:
    """Chat resource namespace."""

    def __init__(self, completions: Completions):
        self.completions = completions


class AsyncChat:
    """Async chat resource namespace."""

    def __init__(self, completions: AsyncCompletions):
        self.completions = completions


class GeneralCompute:
    """
    Synchronous GeneralCompute API client.

    OpenAI-compatible client for the GeneralCompute API.

    Args:
        api_key: API key (or set GENERALCOMPUTE_API_KEY env var)
        base_url: Custom base URL
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        default_headers: Additional headers to send with every request

    Example:
        >>> from generalcompute import GeneralCompute
        >>> client = GeneralCompute(api_key="gc_your_api_key")
        >>> response = client.chat.completions.create(
        ...     model="llama-3.1-8b",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        # Initialize HTTP client
        self._client = BaseClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )

        # Initialize resources
        self.models = Models(self._client)
        completions = Completions(self._client)
        self.chat = Chat(completions)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client."""
        self._client.close()


class AsyncGeneralCompute:
    """
    Asynchronous GeneralCompute API client.

    OpenAI-compatible async client for the GeneralCompute API.

    Args:
        api_key: API key (or set GENERALCOMPUTE_API_KEY env var)
        base_url: Custom base URL
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        default_headers: Additional headers to send with every request

    Example:
        >>> from generalcompute import AsyncGeneralCompute
        >>> async with AsyncGeneralCompute(api_key="gc_your_api_key") as client:
        ...     response = await client.chat.completions.create(
        ...         model="llama-3.1-8b",
        ...         messages=[{"role": "user", "content": "Hello!"}]
        ...     )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        # Initialize HTTP client
        self._client = AsyncBaseClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )

        # Initialize resources
        self.models = AsyncModels(self._client)
        completions = AsyncCompletions(self._client)
        self.chat = AsyncChat(completions)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self._client.close()

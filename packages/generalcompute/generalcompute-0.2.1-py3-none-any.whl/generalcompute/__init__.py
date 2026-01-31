"""
generalcompute - OpenAI-compatible Python SDK for GeneralCompute API

A drop-in replacement for OpenAI's SDK with the same API surface.

Example:
    >>> from generalcompute import GeneralCompute
    >>> client = GeneralCompute(api_key="gc_your_api_key")
    >>> completion = client.chat.completions.create(
    ...     model="llama-3.1-8b",
    ...     messages=[{"role": "user", "content": "Hello!"}]
    ... )
"""

from .client import GeneralCompute, AsyncGeneralCompute
from ._errors import (
    APIError,
    AuthenticationError,
    RateLimitError,
    BadRequestError,
    NotFoundError,
    InternalServerError,
)
from ._streaming import Stream, AsyncStream
from .types.chat import (
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionChunk,
    Usage,
)
from .types.models import ModelObject, ModelsListResponse

__version__ = "0.1.0"

__all__ = [
    # Clients
    "GeneralCompute",
    "AsyncGeneralCompute",
    # Errors
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "BadRequestError",
    "NotFoundError",
    "InternalServerError",
    # Streaming
    "Stream",
    "AsyncStream",
    # Types
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatCompletionChoice",
    "ChatCompletionChunk",
    "Usage",
    "ModelObject",
    "ModelsListResponse",
]

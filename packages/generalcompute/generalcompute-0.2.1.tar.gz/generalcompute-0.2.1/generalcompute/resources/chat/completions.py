"""
Chat completions resource.
"""

from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Union, overload

from ..._streaming import AsyncStream, Stream
from ...types.chat import (
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)

if TYPE_CHECKING:
    from ..._client import AsyncBaseClient, BaseClient


class Completions:
    """Synchronous chat completions resource."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    @overload
    def create(
        self,
        *,
        model: str,
        messages: List[ChatMessage],
        stream: Literal[False] = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        ...

    @overload
    def create(
        self,
        *,
        model: str,
        messages: List[ChatMessage],
        stream: Literal[True],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        **kwargs,
    ) -> Stream[ChatCompletionChunk]:
        ...

    def create(
        self,
        *,
        model: str,
        messages: List[ChatMessage],
        stream: bool = False,
        **kwargs,
    ) -> Union[ChatCompletionResponse, Stream[ChatCompletionChunk]]:
        """
        Create a chat completion.

        Args:
            model: Model ID to use
            messages: List of chat messages
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            ChatCompletionResponse for non-streaming, Stream for streaming

        Example:
            >>> response = client.chat.completions.create(
            ...     model="llama-3.1-8b",
            ...     messages=[{"role": "user", "content": "Hello!"}]
            ... )
        """
        # Build request body
        request_dict = {
            "model": model,
            "messages": [msg.model_dump() if hasattr(msg, "model_dump") else msg for msg in messages],
            "stream": stream,
            **kwargs,
        }

        if stream:
            response = self._client.request(
                method="POST",
                path="/chat/completions",
                body=request_dict,
                stream=True,
            )
            return Stream[ChatCompletionChunk](response)
        else:
            response = self._client.request(
                method="POST",
                path="/chat/completions",
                body=request_dict,
            )
            return ChatCompletionResponse(**response)


class AsyncCompletions:
    """Asynchronous chat completions resource."""

    def __init__(self, client: "AsyncBaseClient"):
        self._client = client

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: List[ChatMessage],
        stream: Literal[False] = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        ...

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: List[ChatMessage],
        stream: Literal[True],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        **kwargs,
    ) -> AsyncStream[ChatCompletionChunk]:
        ...

    async def create(
        self,
        *,
        model: str,
        messages: List[ChatMessage],
        stream: bool = False,
        **kwargs,
    ) -> Union[ChatCompletionResponse, AsyncStream[ChatCompletionChunk]]:
        """
        Create a chat completion asynchronously.

        Args:
            model: Model ID to use
            messages: List of chat messages
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            ChatCompletionResponse for non-streaming, AsyncStream for streaming

        Example:
            >>> response = await client.chat.completions.create(
            ...     model="llama-3.1-8b",
            ...     messages=[{"role": "user", "content": "Hello!"}]
            ... )
        """
        # Build request body
        request_dict = {
            "model": model,
            "messages": [msg.model_dump() if hasattr(msg, "model_dump") else msg for msg in messages],
            "stream": stream,
            **kwargs,
        }

        if stream:
            response = await self._client.request(
                method="POST",
                path="/chat/completions",
                body=request_dict,
                stream=True,
            )
            return AsyncStream[ChatCompletionChunk](response)
        else:
            response = await self._client.request(
                method="POST",
                path="/chat/completions",
                body=request_dict,
            )
            return ChatCompletionResponse(**response)

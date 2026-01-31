"""
Pydantic models for chat completions.

These models mirror the Zod schemas from @generalcompute/types
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: Literal["system", "user", "assistant", "function", "tool"]
    content: Optional[Union[str, List[Any], None]] = None
    name: Optional[str] = None
    function_call: Optional[Any] = None
    tool_calls: Optional[Any] = None


class ChatCompletionRequest(BaseModel):
    """Request parameters for creating a chat completion."""

    model: str
    messages: List[ChatMessage] = Field(..., min_length=1)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    n: Optional[int] = Field(None, gt=0)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = Field(None, gt=0)
    presence_penalty: Optional[float] = Field(None, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(None, ge=-2, le=2)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    # Additional fields that might be passed through
    top_k: Optional[float] = None
    repetition_penalty: Optional[float] = None


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionMessage(BaseModel):
    """A message in a chat completion response."""

    role: str
    content: Optional[str]
    function_call: Optional[Any] = None
    tool_calls: Optional[Any] = None


class ChatCompletionChoice(BaseModel):
    """A choice in a chat completion response."""

    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str]
    logprobs: Optional[Any] = None


class ChatCompletionResponse(BaseModel):
    """Response from a chat completion request."""

    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None


class ChatCompletionChunkDelta(BaseModel):
    """Delta information in a streaming chunk."""

    role: Optional[str] = None
    content: Optional[str] = None


class ChatCompletionChunkChoice(BaseModel):
    """A choice in a streaming chunk."""

    index: int
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[str]


class ChatCompletionChunk(BaseModel):
    """A chunk in a streaming chat completion response."""

    id: str
    object: Literal["chat.completion.chunk"]
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]
    usage: Optional[Usage] = None

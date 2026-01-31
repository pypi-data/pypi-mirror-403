"""
Server-Sent Events (SSE) streaming support.

Handles parsing of SSE streams from the API and provides iterator interfaces.
"""

import json
from typing import AsyncIterator, Generic, Iterator, TypeVar

import httpx

T = TypeVar("T")


class Stream(Generic[T]):
    """Synchronous SSE stream parser."""

    def __init__(self, response: httpx.Response):
        self.response = response

    def __iter__(self) -> Iterator[T]:
        """Iterate over streaming chunks."""
        buffer = ""

        for chunk in self.response.iter_bytes():
            buffer += chunk.decode("utf-8")

            # Process complete lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith(":"):
                    continue

                # Parse SSE data lines
                if line.startswith("data: "):
                    data = line[6:]  # Remove 'data: ' prefix

                    # Check for [DONE] sentinel
                    if data == "[DONE]":
                        return

                    # Parse JSON chunk
                    try:
                        parsed = json.loads(data)
                        yield parsed
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse SSE chunk: {data}, {e}")
                        continue

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.response.close()


class AsyncStream(Generic[T]):
    """Asynchronous SSE stream parser."""

    def __init__(self, response: httpx.Response):
        self.response = response

    async def __aiter__(self) -> AsyncIterator[T]:
        """Async iterate over streaming chunks."""
        buffer = ""

        async for chunk in self.response.aiter_bytes():
            buffer += chunk.decode("utf-8")

            # Process complete lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith(":"):
                    continue

                # Parse SSE data lines
                if line.startswith("data: "):
                    data = line[6:]  # Remove 'data: ' prefix

                    # Check for [DONE] sentinel
                    if data == "[DONE]":
                        return

                    # Parse JSON chunk
                    try:
                        parsed = json.loads(data)
                        yield parsed
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse SSE chunk: {data}, {e}")
                        continue

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.response.aclose()

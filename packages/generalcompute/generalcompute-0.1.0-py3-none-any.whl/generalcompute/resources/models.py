"""
Models resource for listing available models.
"""

from typing import TYPE_CHECKING

from ..types.models import ModelsListResponse

if TYPE_CHECKING:
    from .._client import AsyncBaseClient, BaseClient


class Models:
    """Synchronous models resource."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def list(self) -> ModelsListResponse:
        """
        List available models.

        Returns:
            ModelsListResponse with list of available models

        Example:
            >>> models = client.models.list()
            >>> print(models.data)
        """
        response = self._client.request(method="GET", path="/models")
        return ModelsListResponse(**response)


class AsyncModels:
    """Asynchronous models resource."""

    def __init__(self, client: "AsyncBaseClient"):
        self._client = client

    async def list(self) -> ModelsListResponse:
        """
        List available models.

        Returns:
            ModelsListResponse with list of available models

        Example:
            >>> models = await client.models.list()
            >>> print(models.data)
        """
        response = await self._client.request(method="GET", path="/models")
        return ModelsListResponse(**response)

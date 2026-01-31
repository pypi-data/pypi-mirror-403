"""Tests for client initialization."""

import pytest
from generalcompute import GeneralCompute, AsyncGeneralCompute


def test_client_requires_api_key():
    """Test that client raises error when API key is missing."""
    with pytest.raises(ValueError, match="API key is required"):
        GeneralCompute(api_key="")


def test_client_initialization():
    """Test basic client initialization."""
    client = GeneralCompute(api_key="test-key")
    assert client is not None
    assert hasattr(client, "chat")
    assert hasattr(client, "models")


def test_async_client_requires_api_key():
    """Test that async client raises error when API key is missing."""
    with pytest.raises(ValueError, match="API key is required"):
        AsyncGeneralCompute(api_key="")


def test_async_client_initialization():
    """Test basic async client initialization."""
    client = AsyncGeneralCompute(api_key="test-key")
    assert client is not None
    assert hasattr(client, "chat")
    assert hasattr(client, "models")


def test_client_context_manager():
    """Test client as context manager."""
    with GeneralCompute(api_key="test-key") as client:
        assert client is not None


@pytest.mark.asyncio
async def test_async_client_context_manager():
    """Test async client as context manager."""
    async with AsyncGeneralCompute(api_key="test-key") as client:
        assert client is not None

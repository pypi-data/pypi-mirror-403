"""Tests for Pydantic models."""

from generalcompute.types import (
    ChatMessage,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ModelObject,
    ModelsListResponse,
)


def test_chat_message():
    """Test ChatMessage model."""
    message = ChatMessage(role="user", content="Hello!")
    assert message.role == "user"
    assert message.content == "Hello!"


def test_chat_message_with_optional_fields():
    """Test ChatMessage with optional fields."""
    message = ChatMessage(
        role="assistant",
        content="Hi there!",
        name="assistant-1"
    )
    assert message.name == "assistant-1"


def test_model_object():
    """Test ModelObject model."""
    model = ModelObject(
        id="llama-3.1-8b",
        object="model",
        created=1234567890,
        owned_by="meta"
    )
    assert model.id == "llama-3.1-8b"
    assert model.owned_by == "meta"


def test_models_list_response():
    """Test ModelsListResponse model."""
    response = ModelsListResponse(
        object="list",
        data=[
            ModelObject(
                id="llama-3.1-8b",
                object="model",
                created=1234567890,
                owned_by="meta"
            )
        ]
    )
    assert response.object == "list"
    assert len(response.data) == 1
    assert response.data[0].id == "llama-3.1-8b"

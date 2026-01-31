"""
Pydantic models for model listing.
"""

from typing import List, Literal
from pydantic import BaseModel


class ModelObject(BaseModel):
    """A model object."""

    id: str
    object: Literal["model"]
    created: int
    owned_by: str


class ModelsListResponse(BaseModel):
    """Response from listing models."""

    object: Literal["list"]
    data: List[ModelObject]

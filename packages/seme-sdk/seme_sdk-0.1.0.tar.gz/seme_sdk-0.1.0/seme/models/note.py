"""Note-related models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Note(BaseModel):
    """Note model."""

    id: str
    title: Optional[str] = None
    content: Optional[str] = None
    urls: List[str] = Field(default_factory=list)
    memory_type: str = Field(default="TEXT", alias="memoryType")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = {"populate_by_name": True}


class AddNoteRequest(BaseModel):
    """Request to add a note."""

    content: Optional[str] = None
    title: Optional[str] = None
    urls: Optional[List[str]] = None
    memory_type: str = Field(default="TEXT", alias="memoryType")

    model_config = {"populate_by_name": True}


class AddNoteResponse(BaseModel):
    """Response from adding a note."""

    id: str
    success: bool = True
    message: Optional[str] = None

    model_config = {"populate_by_name": True}

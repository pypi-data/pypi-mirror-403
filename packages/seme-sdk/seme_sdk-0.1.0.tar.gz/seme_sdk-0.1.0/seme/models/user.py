"""User-related models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """User information."""

    name: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    self_introduction: Optional[str] = Field(None, alias="selfIntroduction")
    voice_id: Optional[str] = Field(None, alias="voiceId")
    profile_completeness: Optional[float] = Field(None, alias="profileCompleteness")

    model_config = {"populate_by_name": True}


class Shade(BaseModel):
    """User interest shade/tag."""

    id: str
    shade_name: str = Field(..., alias="shadeName")
    confidence_level: Optional[float] = Field(None, alias="confidenceLevel")
    public_content: Optional[str] = Field(None, alias="publicContent")
    private_content: Optional[str] = Field(None, alias="privateContent")

    model_config = {"populate_by_name": True}


class SoftMemory(BaseModel):
    """User soft memory item."""

    id: str
    content: str
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    memory_type: Optional[str] = Field(None, alias="memoryType")

    model_config = {"populate_by_name": True}


class SoftMemoryResponse(BaseModel):
    """Paginated soft memory response."""

    items: List[SoftMemory] = Field(default_factory=list)
    total: int = 0
    page_no: int = Field(default=1, alias="pageNo")
    page_size: int = Field(default=20, alias="pageSize")
    has_more: bool = Field(default=False, alias="hasMore")

    model_config = {"populate_by_name": True}

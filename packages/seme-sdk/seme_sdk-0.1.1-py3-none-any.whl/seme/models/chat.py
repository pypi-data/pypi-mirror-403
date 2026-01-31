"""Chat-related models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message."""

    message_id: str = Field(..., alias="messageId")
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = Field(None, alias="sessionId")

    model_config = {"populate_by_name": True}


class Session(BaseModel):
    """Chat session."""

    session_id: str = Field(..., alias="sessionId")
    app_id: Optional[str] = Field(None, alias="appId")
    last_message: Optional[str] = Field(None, alias="lastMessage")
    last_update_time: Optional[datetime] = Field(None, alias="lastUpdateTime")
    message_count: int = Field(default=0, alias="messageCount")
    title: Optional[str] = None

    model_config = {"populate_by_name": True}


class ChatChunk(BaseModel):
    """Streaming chat chunk."""

    content: str = ""
    delta: str = ""
    done: bool = False
    session_id: Optional[str] = Field(None, alias="sessionId")
    message_id: Optional[str] = Field(None, alias="messageId")
    event_type: str = Field(default="message", alias="eventType")

    model_config = {"populate_by_name": True}


class ChatRequest(BaseModel):
    """Chat request."""

    message: str
    session_id: Optional[str] = Field(None, alias="sessionId")
    app_id: Optional[str] = Field(None, alias="appId")
    system_prompt: Optional[str] = Field(None, alias="systemPrompt")

    model_config = {"populate_by_name": True}


class SessionListResponse(BaseModel):
    """Session list response."""

    sessions: List[Session] = Field(default_factory=list)
    total: int = 0

    model_config = {"populate_by_name": True}


class SessionMessagesResponse(BaseModel):
    """Session messages response."""

    messages: List[ChatMessage] = Field(default_factory=list)
    session_id: str = Field(..., alias="sessionId")

    model_config = {"populate_by_name": True}

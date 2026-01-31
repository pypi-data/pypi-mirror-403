"""Chat API module."""

import json
from typing import Iterator, List, Optional

from .._http import HTTPClient
from ..models.chat import ChatChunk, ChatMessage, Session


class ChatAPI:
    """Chat-related API operations."""

    CHAT_STREAM_ENDPOINT = "/api/secondme/chat/stream"
    SESSION_LIST_ENDPOINT = "/api/secondme/chat/session/list"
    SESSION_MESSAGES_ENDPOINT = "/api/secondme/chat/session/messages"

    def __init__(self, http_client: HTTPClient):
        """
        Initialize Chat API.

        Args:
            http_client: HTTP client for making requests
        """
        self._http = http_client

    def stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        app_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Iterator[ChatChunk]:
        """
        Send a chat message and receive streaming response.

        Args:
            message: The user's message
            session_id: Optional session ID for conversation continuity
            app_id: Optional app ID
            system_prompt: Optional system prompt to customize behavior

        Yields:
            ChatChunk objects containing response content
        """
        if not message:
            raise ValueError("Message cannot be empty")

        data = {
            "message": message,
        }
        if session_id:
            data["sessionId"] = session_id
        if app_id:
            data["appId"] = app_id
        if system_prompt:
            data["systemPrompt"] = system_prompt

        accumulated_content = ""
        current_session_id = session_id
        current_message_id = None

        for line in self._http.stream_post(self.CHAT_STREAM_ENDPOINT, json_data=data):
            chunk = self._parse_sse_line(line)
            if chunk:
                # Accumulate content
                if chunk.delta:
                    accumulated_content += chunk.delta
                    chunk.content = accumulated_content

                # Track session and message IDs
                if chunk.session_id:
                    current_session_id = chunk.session_id
                if chunk.message_id:
                    current_message_id = chunk.message_id

                # Ensure IDs are propagated
                chunk.session_id = current_session_id
                chunk.message_id = current_message_id

                yield chunk

    def _parse_sse_line(self, line: str) -> Optional[ChatChunk]:
        """Parse an SSE line into a ChatChunk."""
        if not line:
            return None

        # Handle SSE format: "data: {...}"
        if line.startswith("data:"):
            data_str = line[5:].strip()
            if not data_str or data_str == "[DONE]":
                return ChatChunk(done=True)

            try:
                data = json.loads(data_str)
                return ChatChunk(
                    content=data.get("content", ""),
                    delta=data.get("delta", data.get("content", "")),
                    done=data.get("done", False),
                    sessionId=data.get("sessionId"),
                    messageId=data.get("messageId"),
                    eventType=data.get("eventType", "message"),
                )
            except json.JSONDecodeError:
                # Treat as plain text delta
                return ChatChunk(delta=data_str)

        # Handle event type
        if line.startswith("event:"):
            event_type = line[6:].strip()
            return ChatChunk(eventType=event_type)

        return None

    def get_session_list(self, app_id: Optional[str] = None) -> List[Session]:
        """
        Get list of chat sessions.

        Args:
            app_id: Optional app ID to filter sessions

        Returns:
            List of Session objects
        """
        params = {}
        if app_id:
            params["appId"] = app_id

        response = self._http.get(self.SESSION_LIST_ENDPOINT, params=params or None)
        data = response.get("data", response)

        if isinstance(data, list):
            return [Session.model_validate(item) for item in data]

        sessions = data.get("sessions", data.get("list", []))
        return [Session.model_validate(item) for item in sessions]

    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """
        Get messages for a specific session.

        Args:
            session_id: The session ID

        Returns:
            List of ChatMessage objects
        """
        if not session_id:
            raise ValueError("Session ID cannot be empty")

        params = {"sessionId": session_id}
        response = self._http.get(self.SESSION_MESSAGES_ENDPOINT, params=params)
        data = response.get("data", response)

        if isinstance(data, list):
            return [ChatMessage.model_validate(item) for item in data]

        messages = data.get("messages", data.get("list", []))
        return [ChatMessage.model_validate(item) for item in messages]

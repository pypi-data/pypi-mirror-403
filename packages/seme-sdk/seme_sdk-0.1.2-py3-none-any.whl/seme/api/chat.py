"""Chat API module."""

import json
import logging
from typing import Iterator, List, Optional

from .._http import HTTPClient
from ..exceptions import PermissionDeniedError, SecondMeError
from ..models.chat import ChatChunk, ChatMessage, Session

logger = logging.getLogger(__name__)


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

        logger.info(f"[ChatAPI] stream request to {self.CHAT_STREAM_ENDPOINT}")
        logger.info(f"[ChatAPI] stream request data: {data}")

        accumulated_content = ""
        current_session_id = session_id
        current_message_id = None
        line_count = 0
        first_line_checked = False

        for line in self._http.stream_post(self.CHAT_STREAM_ENDPOINT, json_data=data):
            line_count += 1
            if line_count <= 5:
                logger.info(f"[ChatAPI] stream line #{line_count}: {line[:200] if len(line) > 200 else line}")

            # Check first line for API-level error (non-SSE JSON response)
            if not first_line_checked:
                first_line_checked = True
                error = self._check_stream_error(line)
                if error:
                    raise error

            chunk = self._parse_sse_line(line)
            if chunk:
                # Check for error in SSE data
                if chunk.event_type == "error":
                    error_msg = chunk.content or chunk.delta or "Stream error occurred"
                    raise SecondMeError(error_msg)

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

        logger.info(f"[ChatAPI] stream completed, total lines: {line_count}")

    def _check_stream_error(self, line: str) -> Optional[SecondMeError]:
        """
        Check if a line contains an API-level error response.

        Some API errors are returned as raw JSON (not SSE format) with structure:
        {"code": 403, "message": "...", "subCode": "..."}
        """
        if not line:
            return None

        # Skip SSE-formatted lines
        if line.startswith("data:") or line.startswith("event:") or line.startswith(":"):
            return None

        try:
            data = json.loads(line)
            # Check for error structure
            if isinstance(data, dict) and "code" in data and data.get("code") != 0:
                error_code = data.get("code")
                error_msg = data.get("message", "Unknown error")
                sub_code = data.get("subCode", "")

                full_msg = f"{error_msg} ({sub_code})" if sub_code else error_msg
                logger.error(f"[ChatAPI] stream error: code={error_code}, message={error_msg}, subCode={sub_code}")

                # Return appropriate exception type based on error code
                if error_code == 403:
                    return PermissionDeniedError(full_msg, error_code, data)
                elif error_code == 401:
                    from ..exceptions import AuthenticationError
                    return AuthenticationError(full_msg, error_code, data)
                else:
                    return SecondMeError(full_msg, error_code, data)
        except json.JSONDecodeError:
            pass

        return None

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

                # Check for error in SSE data payload
                if "code" in data and data.get("code") != 0:
                    error_msg = data.get("message", "Stream error")
                    sub_code = data.get("subCode", "")
                    return ChatChunk(
                        content=f"{error_msg} ({sub_code})" if sub_code else error_msg,
                        done=True,
                        eventType="error",
                    )

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

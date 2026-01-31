"""Tests for Chat API."""

import pytest
import respx
from httpx import Response

from seme import SecondMeClient
from seme.api.chat import ChatAPI
from seme._http import HTTPClient


class TestChatAPI:
    """Test Chat API methods."""

    @respx.mock
    def test_get_session_list(self):
        """Test getting session list."""
        respx.get("https://app.mindos.com/gate/lab/api/secondme/chat/session/list").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "sessionId": "session1",
                            "appId": "app1",
                            "lastMessage": "Hello there",
                            "messageCount": 5,
                        },
                        {
                            "sessionId": "session2",
                            "appId": "app1",
                            "lastMessage": "How are you?",
                            "messageCount": 3,
                        },
                    ]
                },
            )
        )

        client = SecondMeClient(api_key="lba_ak_test123")
        sessions = client.get_session_list()

        assert len(sessions) == 2
        assert sessions[0].session_id == "session1"
        assert sessions[0].last_message == "Hello there"
        assert sessions[0].message_count == 5
        client.close()

    @respx.mock
    def test_get_session_list_with_app_id(self):
        """Test getting session list filtered by app_id."""
        respx.get("https://app.mindos.com/gate/lab/api/secondme/chat/session/list").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "sessionId": "session1",
                            "appId": "specific_app",
                            "lastMessage": "Filtered session",
                            "messageCount": 2,
                        },
                    ]
                },
            )
        )

        client = SecondMeClient(api_key="lba_ak_test123")
        sessions = client.get_session_list(app_id="specific_app")

        assert len(sessions) == 1
        assert sessions[0].app_id == "specific_app"
        client.close()

    @respx.mock
    def test_get_session_messages(self):
        """Test getting session messages."""
        respx.get("https://app.mindos.com/gate/lab/api/secondme/chat/session/messages").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "messageId": "msg1",
                            "role": "user",
                            "content": "Hello!",
                        },
                        {
                            "messageId": "msg2",
                            "role": "assistant",
                            "content": "Hi there! How can I help?",
                        },
                    ]
                },
            )
        )

        client = SecondMeClient(api_key="lba_ak_test123")
        messages = client.get_session_messages(session_id="session1")

        assert len(messages) == 2
        assert messages[0].message_id == "msg1"
        assert messages[0].role == "user"
        assert messages[0].content == "Hello!"
        assert messages[1].role == "assistant"
        client.close()

    def test_get_session_messages_empty_session_id(self):
        """Test that getting messages requires session_id."""
        client = SecondMeClient(api_key="lba_ak_test123")

        with pytest.raises(ValueError, match="cannot be empty"):
            client.get_session_messages(session_id="")

        client.close()


class TestChatAPISSEParsing:
    """Test SSE parsing."""

    def test_parse_sse_data_line(self):
        """Test parsing SSE data line."""
        http = HTTPClient(token_provider=lambda: "test")
        chat_api = ChatAPI(http)

        chunk = chat_api._parse_sse_line('data: {"content": "Hello", "delta": "Hello"}')

        assert chunk is not None
        assert chunk.delta == "Hello"

    def test_parse_sse_done(self):
        """Test parsing SSE done signal."""
        http = HTTPClient(token_provider=lambda: "test")
        chat_api = ChatAPI(http)

        chunk = chat_api._parse_sse_line("data: [DONE]")

        assert chunk is not None
        assert chunk.done is True

    def test_parse_sse_empty_line(self):
        """Test parsing empty line."""
        http = HTTPClient(token_provider=lambda: "test")
        chat_api = ChatAPI(http)

        chunk = chat_api._parse_sse_line("")

        assert chunk is None

    def test_parse_sse_event_line(self):
        """Test parsing event line."""
        http = HTTPClient(token_provider=lambda: "test")
        chat_api = ChatAPI(http)

        chunk = chat_api._parse_sse_line("event: message")

        assert chunk is not None
        assert chunk.event_type == "message"

    def test_chat_stream_empty_message(self):
        """Test that streaming with empty message raises error."""
        client = SecondMeClient(api_key="lba_ak_test123")

        with pytest.raises(ValueError, match="cannot be empty"):
            list(client.chat_stream(message=""))

        client.close()

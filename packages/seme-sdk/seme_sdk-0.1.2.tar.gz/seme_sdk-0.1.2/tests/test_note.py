"""Tests for Note API."""

import pytest
import respx
from httpx import Response

from seme import SecondMeClient


class TestNoteAPI:
    """Test Note API methods."""

    @respx.mock
    def test_add_note_with_content(self):
        """Test adding a note with content."""
        respx.post("https://app.mindos.com/gate/lab/api/secondme/note/add").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "id": "note123",
                    }
                },
            )
        )

        client = SecondMeClient(api_key="lba_ak_test123")
        note_id = client.add_note(content="This is a test note")

        assert note_id == "note123"
        client.close()

    @respx.mock
    def test_add_note_with_title(self):
        """Test adding a note with title."""
        respx.post("https://app.mindos.com/gate/lab/api/secondme/note/add").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "id": "note456",
                    }
                },
            )
        )

        client = SecondMeClient(api_key="lba_ak_test123")
        note_id = client.add_note(
            content="Note content",
            title="My Note Title",
        )

        assert note_id == "note456"
        client.close()

    @respx.mock
    def test_add_note_with_urls(self):
        """Test adding a note with URLs."""
        respx.post("https://app.mindos.com/gate/lab/api/secondme/note/add").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "id": "note789",
                    }
                },
            )
        )

        client = SecondMeClient(api_key="lba_ak_test123")
        note_id = client.add_note(
            urls=["https://example.com/article1", "https://example.com/article2"],
            memory_type="URL",
        )

        assert note_id == "note789"
        client.close()

    def test_add_note_requires_content_or_urls(self):
        """Test that adding a note requires either content or URLs."""
        client = SecondMeClient(api_key="lba_ak_test123")

        with pytest.raises(ValueError, match="Either content or urls"):
            client.add_note()

        client.close()

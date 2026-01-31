"""Tests for User API."""

import pytest
import respx
from httpx import Response

from seme import SecondMeClient


class TestUserAPI:
    """Test User API methods."""

    @respx.mock
    def test_get_user_info(self):
        """Test getting user info."""
        respx.get("https://app.mindos.com/gate/lab/api/secondme/user/info").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "name": "Test User",
                        "email": "test@example.com",
                        "avatar": "https://example.com/avatar.jpg",
                        "bio": "Test bio",
                        "selfIntroduction": "Hello, I am a test user",
                        "voiceId": "voice123",
                        "profileCompleteness": 0.85,
                    }
                },
            )
        )

        client = SecondMeClient(api_key="lba_ak_test123")
        user = client.get_user_info()

        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.avatar == "https://example.com/avatar.jpg"
        assert user.bio == "Test bio"
        assert user.self_introduction == "Hello, I am a test user"
        assert user.voice_id == "voice123"
        assert user.profile_completeness == 0.85
        client.close()

    @respx.mock
    def test_get_user_shades(self):
        """Test getting user shades."""
        respx.get("https://app.mindos.com/gate/lab/api/secondme/user/shades").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "id": "shade1",
                            "shadeName": "Technology",
                            "confidenceLevel": 0.9,
                            "publicContent": "Loves coding",
                            "privateContent": "Secret tech notes",
                        },
                        {
                            "id": "shade2",
                            "shadeName": "Music",
                            "confidenceLevel": 0.7,
                            "publicContent": "Enjoys jazz",
                            "privateContent": None,
                        },
                    ]
                },
            )
        )

        client = SecondMeClient(api_key="lba_ak_test123")
        shades = client.get_user_shades()

        assert len(shades) == 2
        assert shades[0].id == "shade1"
        assert shades[0].shade_name == "Technology"
        assert shades[0].confidence_level == 0.9
        assert shades[1].shade_name == "Music"
        client.close()

    @respx.mock
    def test_get_user_softmemory(self):
        """Test getting user soft memory."""
        respx.get("https://app.mindos.com/gate/lab/api/secondme/user/softmemory").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "items": [
                            {
                                "id": "mem1",
                                "content": "First memory",
                                "createdAt": "2024-01-01T00:00:00Z",
                            },
                            {
                                "id": "mem2",
                                "content": "Second memory",
                                "createdAt": "2024-01-02T00:00:00Z",
                            },
                        ],
                        "total": 2,
                        "pageNo": 1,
                        "pageSize": 20,
                        "hasMore": False,
                    }
                },
            )
        )

        client = SecondMeClient(api_key="lba_ak_test123")
        response = client.get_user_softmemory()

        assert len(response.items) == 2
        assert response.items[0].id == "mem1"
        assert response.items[0].content == "First memory"
        assert response.total == 2
        assert response.has_more is False
        client.close()

    @respx.mock
    def test_get_user_softmemory_with_keyword(self):
        """Test getting user soft memory with keyword filter."""
        respx.get("https://app.mindos.com/gate/lab/api/secondme/user/softmemory").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "items": [
                            {
                                "id": "mem1",
                                "content": "Memory about Python",
                            },
                        ],
                        "total": 1,
                        "pageNo": 1,
                        "pageSize": 20,
                        "hasMore": False,
                    }
                },
            )
        )

        client = SecondMeClient(api_key="lba_ak_test123")
        response = client.get_user_softmemory(keyword="Python", page_no=1, page_size=20)

        assert len(response.items) == 1
        assert "Python" in response.items[0].content
        client.close()

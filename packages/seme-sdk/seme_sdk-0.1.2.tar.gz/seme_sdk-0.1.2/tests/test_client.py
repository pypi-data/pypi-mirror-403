"""Tests for SecondMeClient."""

import pytest

from seme import SecondMeClient
from seme.auth import OAuth2Client


class TestSecondMeClientInit:
    """Test client initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = SecondMeClient(api_key="lba_ak_test123")
        assert client._api_key_auth is not None
        assert client._api_key_auth.api_key == "lba_ak_test123"
        client.close()

    def test_init_with_access_token(self):
        """Test initialization with access token."""
        client = SecondMeClient(access_token="lba_at_test123")
        assert client._static_token == "lba_at_test123"
        client.close()

    def test_init_requires_auth(self):
        """Test that initialization requires either api_key or access_token."""
        with pytest.raises(ValueError, match="Either api_key or access_token"):
            SecondMeClient()

    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        client = SecondMeClient(
            api_key="lba_ak_test123",
            base_url="https://custom.example.com/api",
        )
        assert client._base_url == "https://custom.example.com/api"
        client.close()

    def test_context_manager(self):
        """Test client as context manager."""
        with SecondMeClient(api_key="lba_ak_test123") as client:
            assert client is not None


class TestSecondMeClientFromOAuth:
    """Test client creation from OAuth."""

    def test_from_oauth(self):
        """Test creating client from OAuth token response."""
        from seme.models import TokenResponse

        oauth_client = OAuth2Client(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
        )

        token_response = TokenResponse(
            accessToken="lba_at_test123",
            refreshToken="lba_rt_test123",
            expiresIn=7200,
            tokenType="Bearer",
        )

        client = SecondMeClient.from_oauth(
            oauth_client=oauth_client,
            token_response=token_response,
        )

        assert client._token_manager is not None
        assert client._token_manager.access_token == "lba_at_test123"
        client.close()

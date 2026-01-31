"""Tests for authentication modules."""

import pytest

from seme.auth import APIKeyAuth, OAuth2Client


class TestAPIKeyAuth:
    """Test API Key authentication."""

    def test_init(self):
        """Test initialization."""
        auth = APIKeyAuth("lba_ak_test123")
        assert auth.api_key == "lba_ak_test123"

    def test_init_empty_key(self):
        """Test initialization with empty key raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            APIKeyAuth("")

    def test_get_token(self):
        """Test getting token."""
        auth = APIKeyAuth("lba_ak_test123")
        assert auth.get_token() == "lba_ak_test123"

    def test_is_api_key(self):
        """Test API key detection."""
        assert APIKeyAuth.is_api_key("lba_ak_test123") is True
        assert APIKeyAuth.is_api_key("lba_at_test123") is False
        assert APIKeyAuth.is_api_key("") is False
        assert APIKeyAuth.is_api_key(None) is False


class TestOAuth2Client:
    """Test OAuth2 client."""

    def test_init(self):
        """Test initialization."""
        client = OAuth2Client(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
        )
        assert client.client_id == "test_client"
        assert client.client_secret == "test_secret"
        assert client.redirect_uri == "https://example.com/callback"

    def test_init_empty_client_id(self):
        """Test initialization with empty client_id raises error."""
        with pytest.raises(ValueError, match="client_id cannot be empty"):
            OAuth2Client(
                client_id="",
                client_secret="test_secret",
                redirect_uri="https://example.com/callback",
            )

    def test_init_empty_client_secret(self):
        """Test initialization with empty client_secret raises error."""
        with pytest.raises(ValueError, match="client_secret cannot be empty"):
            OAuth2Client(
                client_id="test_client",
                client_secret="",
                redirect_uri="https://example.com/callback",
            )

    def test_init_empty_redirect_uri(self):
        """Test initialization with empty redirect_uri raises error."""
        with pytest.raises(ValueError, match="redirect_uri cannot be empty"):
            OAuth2Client(
                client_id="test_client",
                client_secret="test_secret",
                redirect_uri="",
            )

    def test_get_authorization_url(self):
        """Test generating authorization URL."""
        client = OAuth2Client(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
        )

        url = client.get_authorization_url(
            scopes=["user.info", "chat"],
            state="random_state",
        )

        assert "/api/oauth/authorize/external" in url
        assert "clientId=test_client" in url
        assert "redirectUri=" in url
        assert "scope=user.info+chat" in url
        assert "state=random_state" in url
        assert "responseType=code" in url

    def test_get_authorization_url_without_state(self):
        """Test generating authorization URL without state."""
        client = OAuth2Client(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
        )

        url = client.get_authorization_url(scopes=["user.info"])

        assert "state=" not in url

    def test_exchange_code_empty(self):
        """Test exchanging empty code raises error."""
        client = OAuth2Client(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
        )

        with pytest.raises(ValueError, match="cannot be empty"):
            client.exchange_code("")

    def test_refresh_token_empty(self):
        """Test refreshing with empty token raises error."""
        client = OAuth2Client(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
        )

        with pytest.raises(ValueError, match="cannot be empty"):
            client.refresh_token("")

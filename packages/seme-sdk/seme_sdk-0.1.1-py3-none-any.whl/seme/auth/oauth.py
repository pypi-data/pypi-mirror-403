"""OAuth2 authentication provider."""

import time
from typing import Callable, List, Optional
from urllib.parse import urlencode

from .._http import DEFAULT_BASE_URL, HTTPClient
from ..exceptions import AuthenticationError, TokenExpiredError
from ..models.auth import TokenResponse


class OAuth2Client:
    """OAuth2 client for authorization and token management."""

    AUTHORIZE_ENDPOINT = "/api/oauth/authorize/external"
    TOKEN_CODE_ENDPOINT = "/api/oauth/token/code"
    TOKEN_REFRESH_ENDPOINT = "/api/oauth/token/refresh"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        base_url: str = DEFAULT_BASE_URL,
    ):
        """
        Initialize OAuth2 client.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            redirect_uri: Redirect URI for authorization callback
            base_url: API base URL
        """
        if not client_id:
            raise ValueError("client_id cannot be empty")
        if not client_secret:
            raise ValueError("client_secret cannot be empty")
        if not redirect_uri:
            raise ValueError("redirect_uri cannot be empty")

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = base_url.rstrip("/")
        self._http = HTTPClient(base_url=base_url)

    def get_authorization_url(
        self,
        scopes: List[str],
        state: Optional[str] = None,
    ) -> str:
        """
        Generate the authorization URL for user consent.

        Args:
            scopes: List of permission scopes to request
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect the user to
        """
        params = {
            "clientId": self.client_id,
            "redirectUri": self.redirect_uri,
            "scope": " ".join(scopes),
            "responseType": "code",
        }
        if state:
            params["state"] = state

        return f"{self.base_url}{self.AUTHORIZE_ENDPOINT}?{urlencode(params)}"

    def exchange_code(self, code: str) -> TokenResponse:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code received from callback

        Returns:
            TokenResponse containing access_token, refresh_token, etc.
        """
        if not code:
            raise ValueError("Authorization code cannot be empty")

        data = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
            "code": code,
            "redirectUri": self.redirect_uri,
            "grantType": "authorization_code",
        }

        response = self._http.post(self.TOKEN_CODE_ENDPOINT, json_data=data)
        return TokenResponse.model_validate(response.get("data", response))

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh the access token using a refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            TokenResponse containing new access_token, refresh_token, etc.
        """
        if not refresh_token:
            raise ValueError("Refresh token cannot be empty")

        data = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
            "refreshToken": refresh_token,
            "grantType": "refresh_token",
        }

        response = self._http.post(self.TOKEN_REFRESH_ENDPOINT, json_data=data)
        return TokenResponse.model_validate(response.get("data", response))


class OAuth2TokenManager:
    """Manages OAuth2 tokens with automatic refresh."""

    # Refresh token 5 minutes before expiry
    REFRESH_BUFFER_SECONDS = 300

    def __init__(
        self,
        oauth_client: OAuth2Client,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        on_token_refresh: Optional[Callable[[TokenResponse], None]] = None,
    ):
        """
        Initialize token manager.

        Args:
            oauth_client: OAuth2Client instance for refreshing tokens
            access_token: Current access token
            refresh_token: Current refresh token
            expires_in: Token expiry time in seconds
            on_token_refresh: Optional callback when tokens are refreshed
        """
        self._oauth_client = oauth_client
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._expires_at = time.time() + expires_in
        self._on_token_refresh = on_token_refresh

    @property
    def access_token(self) -> str:
        """Get current access token."""
        return self._access_token

    @property
    def refresh_token_value(self) -> str:
        """Get current refresh token."""
        return self._refresh_token

    def is_expired(self) -> bool:
        """Check if the access token is expired or about to expire."""
        return time.time() >= (self._expires_at - self.REFRESH_BUFFER_SECONDS)

    def get_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self.is_expired():
            self._do_refresh()
        return self._access_token

    def _do_refresh(self) -> None:
        """Perform token refresh."""
        try:
            token_response = self._oauth_client.refresh_token(self._refresh_token)
            self._access_token = token_response.access_token
            self._refresh_token = token_response.refresh_token
            self._expires_at = time.time() + token_response.expires_in

            if self._on_token_refresh:
                self._on_token_refresh(token_response)
        except Exception as e:
            raise TokenExpiredError(f"Failed to refresh token: {e}") from e

    def force_refresh(self) -> TokenResponse:
        """Force a token refresh regardless of expiry."""
        self._do_refresh()
        return TokenResponse(
            accessToken=self._access_token,
            refreshToken=self._refresh_token,
            expiresIn=int(self._expires_at - time.time()),
            tokenType="Bearer",
        )

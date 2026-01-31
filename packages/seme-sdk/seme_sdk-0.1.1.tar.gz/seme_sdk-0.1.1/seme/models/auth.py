"""Authentication models."""

from typing import List, Optional

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """OAuth2 token response."""

    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    token_type: str = Field(default="Bearer", alias="tokenType")
    expires_in: int = Field(..., alias="expiresIn")
    scope: Optional[str] = None

    model_config = {"populate_by_name": True}

    @property
    def scopes(self) -> List[str]:
        """Get scopes as a list."""
        if self.scope:
            return self.scope.split(" ")
        return []


class AuthorizationRequest(BaseModel):
    """OAuth2 authorization request."""

    client_id: str = Field(..., alias="clientId")
    redirect_uri: str = Field(..., alias="redirectUri")
    scope: str
    state: Optional[str] = None
    response_type: str = Field(default="code", alias="responseType")

    model_config = {"populate_by_name": True}


class TokenRequest(BaseModel):
    """OAuth2 token exchange request."""

    client_id: str = Field(..., alias="clientId")
    client_secret: str = Field(..., alias="clientSecret")
    code: str
    redirect_uri: str = Field(..., alias="redirectUri")
    grant_type: str = Field(default="authorization_code", alias="grantType")

    model_config = {"populate_by_name": True}


class RefreshTokenRequest(BaseModel):
    """OAuth2 refresh token request."""

    client_id: str = Field(..., alias="clientId")
    client_secret: str = Field(..., alias="clientSecret")
    refresh_token: str = Field(..., alias="refreshToken")
    grant_type: str = Field(default="refresh_token", alias="grantType")

    model_config = {"populate_by_name": True}

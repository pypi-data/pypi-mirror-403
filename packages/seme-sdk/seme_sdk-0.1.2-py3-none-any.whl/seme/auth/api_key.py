"""API Key authentication provider."""

from typing import Optional


class APIKeyAuth:
    """API Key authentication handler."""

    def __init__(self, api_key: str):
        """
        Initialize API Key authentication.

        Args:
            api_key: The API key (format: lba_ak_xxxxx...)
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        self._api_key = api_key

    def get_token(self) -> str:
        """Get the API key for authorization header."""
        return self._api_key

    @property
    def api_key(self) -> str:
        """Get the API key."""
        return self._api_key

    @staticmethod
    def is_api_key(token: str) -> bool:
        """Check if a token is an API key (starts with lba_ak_)."""
        return token.startswith("lba_ak_") if token else False

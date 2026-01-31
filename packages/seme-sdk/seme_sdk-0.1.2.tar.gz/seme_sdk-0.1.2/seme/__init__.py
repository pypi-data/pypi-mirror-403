"""
SecondMe Python SDK

A Python SDK for interacting with the SecondMe API.

Example usage:
    from seme import SecondMeClient

    # Using API Key
    client = SecondMeClient(api_key="lba_ak_xxxxx...")
    user = client.get_user_info()
    print(f"Hello, {user.name}!")

    # Streaming chat
    for chunk in client.chat_stream("Hello!"):
        print(chunk.delta, end="", flush=True)
"""

from .auth import APIKeyAuth, OAuth2Client, OAuth2TokenManager
from .client import SecondMeClient
from .exceptions import (
    AuthenticationError,
    InvalidParameterError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    SecondMeError,
    ServerError,
    TokenExpiredError,
)
from .models import (
    ChatChunk,
    ChatMessage,
    Session,
    Shade,
    SoftMemory,
    SoftMemoryResponse,
    TokenResponse,
    UserInfo,
)

__version__ = "0.1.1"

__all__ = [
    # Main client
    "SecondMeClient",
    # Auth
    "OAuth2Client",
    "OAuth2TokenManager",
    "APIKeyAuth",
    # Models
    "UserInfo",
    "Shade",
    "SoftMemory",
    "SoftMemoryResponse",
    "ChatMessage",
    "ChatChunk",
    "Session",
    "TokenResponse",
    # Exceptions
    "SecondMeError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "InvalidParameterError",
    "RateLimitError",
    "ServerError",
    "TokenExpiredError",
]

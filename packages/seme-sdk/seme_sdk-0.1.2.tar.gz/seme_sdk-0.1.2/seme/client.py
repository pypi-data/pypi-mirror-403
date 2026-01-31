"""Main client for SecondMe SDK."""

from typing import Callable, Iterator, List, Optional

from ._http import DEFAULT_BASE_URL, HTTPClient
from .api.chat import ChatAPI
from .api.note import NoteAPI
from .api.user import UserAPI
from .auth.api_key import APIKeyAuth
from .auth.oauth import OAuth2Client, OAuth2TokenManager
from .models.auth import TokenResponse
from .models.chat import ChatChunk, ChatMessage, Session
from .models.user import Shade, SoftMemoryResponse, UserInfo


class SecondMeClient:
    """
    Main client for interacting with SecondMe API.

    This client provides access to all SecondMe API endpoints including
    user information, notes, and chat functionality.

    Example usage with API Key:
        client = SecondMeClient(api_key="lba_ak_xxxxx...")
        user = client.get_user_info()
        print(f"Hello, {user.name}!")

    Example usage with OAuth2 Access Token:
        client = SecondMeClient(access_token="lba_at_xxxxx...")
        user = client.get_user_info()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        # OAuth2 auto-refresh parameters
        oauth_client: Optional[OAuth2Client] = None,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        on_token_refresh: Optional[Callable[[TokenResponse], None]] = None,
    ):
        """
        Initialize SecondMe client.

        Args:
            api_key: API Key for authentication (format: lba_ak_xxxxx...)
            access_token: OAuth2 Access Token (format: lba_at_xxxxx...)
            base_url: API base URL (default: https://app.mindos.com/gate/lab)
            oauth_client: OAuth2Client instance for token refresh
            refresh_token: Refresh token for automatic token refresh
            expires_in: Token expiry time in seconds (default: 7200 = 2 hours)
            on_token_refresh: Callback when tokens are refreshed
        """
        if not api_key and not access_token:
            raise ValueError("Either api_key or access_token must be provided")

        self._base_url = base_url
        self._token_manager: Optional[OAuth2TokenManager] = None
        self._api_key_auth: Optional[APIKeyAuth] = None

        # Set up authentication
        if api_key:
            self._api_key_auth = APIKeyAuth(api_key)
            token_provider = self._api_key_auth.get_token
        else:
            # OAuth2 token authentication
            if oauth_client and refresh_token:
                # Set up auto-refresh
                self._token_manager = OAuth2TokenManager(
                    oauth_client=oauth_client,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=expires_in or 7200,
                    on_token_refresh=on_token_refresh,
                )
                token_provider = self._token_manager.get_token
            else:
                # Static token (no auto-refresh)
                self._static_token = access_token
                token_provider = lambda: self._static_token

        # Initialize HTTP client and APIs
        self._http = HTTPClient(base_url=base_url, token_provider=token_provider)
        self._user_api = UserAPI(self._http)
        self._note_api = NoteAPI(self._http)
        self._chat_api = ChatAPI(self._http)

    @classmethod
    def from_oauth(
        cls,
        oauth_client: OAuth2Client,
        token_response: TokenResponse,
        on_token_refresh: Optional[Callable[[TokenResponse], None]] = None,
    ) -> "SecondMeClient":
        """
        Create a client from OAuth2 token response with automatic refresh.

        Args:
            oauth_client: OAuth2Client instance
            token_response: Token response from code exchange or refresh
            on_token_refresh: Callback when tokens are refreshed

        Returns:
            SecondMeClient instance with auto-refresh enabled
        """
        return cls(
            access_token=token_response.access_token,
            oauth_client=oauth_client,
            refresh_token=token_response.refresh_token,
            expires_in=token_response.expires_in,
            on_token_refresh=on_token_refresh,
            base_url=oauth_client.base_url,
        )

    # ==================== User API ====================

    def get_user_info(self) -> UserInfo:
        """
        Get current user information.

        Returns:
            UserInfo object containing user details

        Raises:
            AuthenticationError: If authentication fails
            PermissionDeniedError: If lacking user.info permission
        """
        return self._user_api.get_info()

    def get_user_shades(self) -> List[Shade]:
        """
        Get user interest shades/tags.

        Returns:
            List of Shade objects representing user interests

        Raises:
            AuthenticationError: If authentication fails
            PermissionDeniedError: If lacking user.info.shades permission
        """
        return self._user_api.get_shades()

    def get_user_softmemory(
        self,
        keyword: Optional[str] = None,
        page_no: int = 1,
        page_size: int = 20,
    ) -> SoftMemoryResponse:
        """
        Get user soft memory items.

        Args:
            keyword: Optional keyword to filter memories
            page_no: Page number (1-indexed, default: 1)
            page_size: Number of items per page (default: 20)

        Returns:
            SoftMemoryResponse containing paginated soft memories

        Raises:
            AuthenticationError: If authentication fails
            PermissionDeniedError: If lacking user.info.softmemory permission
        """
        return self._user_api.get_softmemory(
            keyword=keyword,
            page_no=page_no,
            page_size=page_size,
        )

    # ==================== Note API ====================

    def add_note(
        self,
        content: Optional[str] = None,
        title: Optional[str] = None,
        urls: Optional[List[str]] = None,
        memory_type: str = "TEXT",
    ) -> str:
        """
        Add a new note.

        Args:
            content: Note content text
            title: Optional note title
            urls: Optional list of URLs to attach
            memory_type: Type of memory (default: "TEXT")

        Returns:
            ID of the created note

        Raises:
            AuthenticationError: If authentication fails
            PermissionDeniedError: If lacking note.add permission
            InvalidParameterError: If neither content nor urls is provided
        """
        return self._note_api.add(
            content=content,
            title=title,
            urls=urls,
            memory_type=memory_type,
        )

    # ==================== Chat API ====================

    def chat_stream(
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

        Raises:
            AuthenticationError: If authentication fails
            PermissionDeniedError: If lacking chat permission
            InvalidParameterError: If message is empty

        Example:
            for chunk in client.chat_stream("Hello!"):
                print(chunk.delta, end="", flush=True)
        """
        return self._chat_api.stream(
            message=message,
            session_id=session_id,
            app_id=app_id,
            system_prompt=system_prompt,
        )

    def get_session_list(self, app_id: Optional[str] = None) -> List[Session]:
        """
        Get list of chat sessions.

        Args:
            app_id: Optional app ID to filter sessions

        Returns:
            List of Session objects

        Raises:
            AuthenticationError: If authentication fails
            PermissionDeniedError: If lacking chat permission
        """
        return self._chat_api.get_session_list(app_id=app_id)

    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """
        Get messages for a specific session.

        Args:
            session_id: The session ID

        Returns:
            List of ChatMessage objects in chronological order

        Raises:
            AuthenticationError: If authentication fails
            PermissionDeniedError: If lacking chat permission
            InvalidParameterError: If session_id is empty
            NotFoundError: If session does not exist
        """
        return self._chat_api.get_session_messages(session_id=session_id)

    # ==================== Lifecycle ====================

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()

    def __enter__(self) -> "SecondMeClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

"""User API module."""

from typing import List, Optional

from .._http import HTTPClient
from ..models.user import Shade, SoftMemory, SoftMemoryResponse, UserInfo


class UserAPI:
    """User-related API operations."""

    USER_INFO_ENDPOINT = "/api/secondme/user/info"
    USER_SHADES_ENDPOINT = "/api/secondme/user/shades"
    USER_SOFTMEMORY_ENDPOINT = "/api/secondme/user/softmemory"

    def __init__(self, http_client: HTTPClient):
        """
        Initialize User API.

        Args:
            http_client: HTTP client for making requests
        """
        self._http = http_client

    def get_info(self) -> UserInfo:
        """
        Get user information.

        Returns:
            UserInfo object containing user details
        """
        response = self._http.get(self.USER_INFO_ENDPOINT)
        data = response.get("data", response)
        return UserInfo.model_validate(data)

    def get_shades(self) -> List[Shade]:
        """
        Get user interest shades/tags.

        Returns:
            List of Shade objects
        """
        response = self._http.get(self.USER_SHADES_ENDPOINT)
        data = response.get("data", response)

        if isinstance(data, list):
            return [Shade.model_validate(item) for item in data]
        return []

    def get_softmemory(
        self,
        keyword: Optional[str] = None,
        page_no: int = 1,
        page_size: int = 20,
    ) -> SoftMemoryResponse:
        """
        Get user soft memory items.

        Args:
            keyword: Optional keyword to filter memories
            page_no: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            SoftMemoryResponse containing paginated soft memories
        """
        params = {
            "pageNo": page_no,
            "pageSize": page_size,
        }
        if keyword:
            params["keyword"] = keyword

        response = self._http.get(self.USER_SOFTMEMORY_ENDPOINT, params=params)
        data = response.get("data", response)

        # Handle both list and paginated response formats
        if isinstance(data, list):
            return SoftMemoryResponse(
                items=[SoftMemory.model_validate(item) for item in data],
                total=len(data),
                pageNo=page_no,
                pageSize=page_size,
                hasMore=False,
            )

        items = data.get("items", data.get("list", []))
        return SoftMemoryResponse(
            items=[SoftMemory.model_validate(item) for item in items],
            total=data.get("total", len(items)),
            pageNo=data.get("pageNo", page_no),
            pageSize=data.get("pageSize", page_size),
            hasMore=data.get("hasMore", False),
        )

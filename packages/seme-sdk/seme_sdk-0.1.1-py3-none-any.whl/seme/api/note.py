"""Note API module."""

from typing import List, Optional

from .._http import HTTPClient


class NoteAPI:
    """Note-related API operations."""

    ADD_NOTE_ENDPOINT = "/api/secondme/note/add"

    def __init__(self, http_client: HTTPClient):
        """
        Initialize Note API.

        Args:
            http_client: HTTP client for making requests
        """
        self._http = http_client

    def add(
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
        """
        if not content and not urls:
            raise ValueError("Either content or urls must be provided")

        data = {
            "memoryType": memory_type,
        }
        if content:
            data["content"] = content
        if title:
            data["title"] = title
        if urls:
            data["urls"] = urls

        response = self._http.post(self.ADD_NOTE_ENDPOINT, json_data=data)
        result_data = response.get("data", response)

        # Return the note ID
        if isinstance(result_data, dict):
            return result_data.get("id", result_data.get("noteId", ""))
        return str(result_data)

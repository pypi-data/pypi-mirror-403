"""HTTP client wrapper for SecondMe SDK."""

import json
from typing import Any, Callable, Dict, Iterator, Optional

import httpx

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

DEFAULT_BASE_URL = "https://app.mindos.com/gate/lab"
DEFAULT_TIMEOUT = 30.0
STREAM_TIMEOUT = 120.0


class HTTPClient:
    """HTTP client for making API requests."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        token_provider: Optional[Callable[[], str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._token_provider = token_provider
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    def _get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._token_provider:
            token = self._token_provider()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle HTTP response and raise appropriate exceptions."""
        try:
            data = response.json() if response.content else {}
        except json.JSONDecodeError:
            data = {"raw": response.text}

        if response.is_success:
            return data

        status_code = response.status_code
        message = data.get("message", data.get("error", str(data)))

        if status_code == 400:
            raise InvalidParameterError(message, status_code, data)
        elif status_code == 401:
            if "expired" in message.lower() or "token" in message.lower():
                raise TokenExpiredError(message, status_code, data)
            raise AuthenticationError(message, status_code, data)
        elif status_code == 403:
            raise PermissionDeniedError(message, status_code, data)
        elif status_code == 404:
            raise NotFoundError(message, status_code, data)
        elif status_code == 429:
            raise RateLimitError(message, status_code, data)
        elif status_code >= 500:
            raise ServerError(message, status_code, data)
        else:
            raise SecondMeError(message, status_code, data)

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an HTTP request."""
        url = path if path.startswith("http") else path
        request_headers = self._get_headers(headers)

        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        response = self.client.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=request_headers,
        )
        return self._handle_response(response)

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a GET request."""
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a POST request."""
        return self.request("POST", path, params=params, json_data=json_data, headers=headers)

    def stream_post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Iterator[str]:
        """Make a streaming POST request (SSE)."""
        url = path if path.startswith("http") else path
        request_headers = self._get_headers(headers)
        request_headers["Accept"] = "text/event-stream"

        with httpx.Client(base_url=self.base_url, timeout=STREAM_TIMEOUT) as client:
            with client.stream(
                "POST",
                url,
                json=json_data,
                headers=request_headers,
            ) as response:
                if not response.is_success:
                    # Read full response for error handling
                    response.read()
                    self._handle_response(response)

                for line in response.iter_lines():
                    if line:
                        yield line

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()

    def __enter__(self) -> "HTTPClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

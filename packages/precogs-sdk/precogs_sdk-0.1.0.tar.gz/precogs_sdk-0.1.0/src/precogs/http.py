"""HTTP client with retry logic and error handling."""

from __future__ import annotations

import httpx
from typing import Any

from precogs.exceptions import (
    PrecogsError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    InsufficientTokensError,
    ServerError,
)


class HTTPClient:
    """Low-level HTTP client for Precogs API."""

    DEFAULT_BASE_URL = "https://api.precogs.ai/api/v1"
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout or self.DEFAULT_TIMEOUT

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "precogs-sdk/0.1.0 python",
            },
        )

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse response and raise appropriate exceptions."""
        try:
            data = response.json() if response.content else {}
        except Exception:
            data = {"raw": response.text}

        if response.is_success:
            return data

        message = data.get("message") or data.get("error") or response.reason_phrase
        status = response.status_code

        if status == 401:
            raise AuthenticationError(message, status_code=status, response=data)
        elif status == 402:
            raise InsufficientTokensError(message, status_code=status, response=data)
        elif status == 403:
            raise AuthenticationError(message, status_code=status, response=data)
        elif status == 404:
            raise NotFoundError(message, status_code=status, response=data)
        elif status == 422:
            raise ValidationError(message, status_code=status, response=data)
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                status_code=status,
                response=data,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif status >= 500:
            raise ServerError(message, status_code=status, response=data)
        else:
            raise PrecogsError(message, status_code=status, response=data)

    def get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        """Make GET request."""
        response = self._client.get(path, params=params)
        return self._handle_response(response)

    def post(self, path: str, json: dict | None = None) -> dict[str, Any]:
        """Make POST request."""
        response = self._client.post(path, json=json)
        return self._handle_response(response)

    def put(self, path: str, json: dict | None = None) -> dict[str, Any]:
        """Make PUT request."""
        response = self._client.put(path, json=json)
        return self._handle_response(response)

    def patch(self, path: str, json: dict | None = None) -> dict[str, Any]:
        """Make PATCH request."""
        response = self._client.patch(path, json=json)
        return self._handle_response(response)

    def delete(self, path: str) -> dict[str, Any]:
        """Make DELETE request."""
        response = self._client.delete(path)
        return self._handle_response(response)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "HTTPClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

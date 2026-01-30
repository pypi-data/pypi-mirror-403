"""Base client for Hyphen SDK."""

import os
from typing import Any

import requests


class BaseClient:
    """Base client class for making HTTP requests to Hyphen API."""

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.hyphen.ai"):
        """
        Initialize the base client.

        Args:
            api_key: API key for authentication. If not provided, will check HYPHEN_API_KEY env var.
            base_url: Base URL for the Hyphen API.
        """
        self.api_key = api_key or os.environ.get("HYPHEN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Provide it as a parameter or set "
                "HYPHEN_API_KEY environment variable."
            )
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "x-api-key": self.api_key,
            }
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make an HTTP request to the Hyphen API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Response data as JSON

        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"} if data is not None else {}
        response = self.session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        # Handle empty responses (like 204 No Content)
        if response.status_code == 204 or not response.content:
            return None

        return response.json()

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request."""
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        """Make a POST request with a dict body."""
        return self._request("POST", endpoint, data=data)

    def post_raw(self, endpoint: str, data: Any) -> Any:
        """Make a POST request with raw data (e.g., a list)."""
        return self._request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        """Make a PUT request."""
        return self._request("PUT", endpoint, data=data)

    def patch(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        """Make a PATCH request."""
        return self._request("PATCH", endpoint, data=data)

    def delete(self, endpoint: str) -> Any:
        """Make a DELETE request."""
        return self._request("DELETE", endpoint)

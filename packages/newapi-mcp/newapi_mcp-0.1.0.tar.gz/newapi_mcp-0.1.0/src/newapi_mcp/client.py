"""HTTP client for New API."""

import time
from typing import Any

import requests

from .config import Config


class NewAPIClient:
    """HTTP client for New API."""

    def __init__(self, base_url: str = "", token: str = "", user_id: str = ""):
        self.base_url = base_url or Config.BASE_URL
        self.token = token or Config.TOKEN
        self.user_id = user_id or Config.USER_ID

    def _get_headers(self, auth_required: bool = False) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if auth_required:
            headers.update(
                {
                    "Authorization": f"Bearer {self.token}",
                    "New-Api-User": self.user_id,
                }
            )
        return headers

    def _retry_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> requests.Response:
        """Execute request with retry logic."""
        last_error: requests.RequestException | None = None
        for attempt in range(Config.MAX_RETRIES):
            try:
                response = requests.request(
                    method,
                    url,
                    timeout=Config.get_timeout(),
                    **kwargs,
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_error = e
                if attempt == Config.MAX_RETRIES - 1:
                    raise
                delay = min(
                    Config.BASE_DELAY * (2**attempt),
                    Config.MAX_DELAY,
                )
                time.sleep(delay)
        raise last_error or requests.RequestException("Unknown error")

    def get(
        self,
        endpoint: str,
        auth_required: bool = False,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute GET request."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(auth_required)
        response = self._retry_request("GET", url, headers=headers, params=params)
        return response.json()

    def put(
        self,
        endpoint: str,
        data: dict[str, Any],
        auth_required: bool = True,
    ) -> dict[str, Any]:
        """Execute PUT request."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(auth_required)
        response = self._retry_request(
            "PUT",
            url,
            headers=headers,
            json=data,
        )
        return response.json()

    def post(
        self,
        endpoint: str,
        data: dict[str, Any],
        auth_required: bool = True,
    ) -> dict[str, Any]:
        """Execute POST request."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(auth_required)
        response = self._retry_request(
            "POST",
            url,
            headers=headers,
            json=data,
        )
        return response.json()

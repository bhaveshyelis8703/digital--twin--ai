import os
from typing import Any

import requests


class APIClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

    def _headers(self, token: str | None = None) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _auth_header(self, token: str | None = None) -> dict[str, str]:
        """Return only the Authorization header (no Content-Type, for form posts)."""
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def get(self, path: str, token: str | None = None) -> Any:
        response = requests.get(f"{self.base_url}{path}", headers=self._headers(token), timeout=10)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, payload: dict[str, Any] | None = None, token: str | None = None) -> Any:
        response = requests.post(f"{self.base_url}{path}", json=payload, headers=self._headers(token), timeout=10)
        response.raise_for_status()
        return response.json()

    def post_form(self, path: str, data: dict[str, Any], token: str | None = None) -> Any:
        """Send a form-encoded POST (application/x-www-form-urlencoded).

        Required for OAuth2 password-grant endpoints that use
        OAuth2PasswordRequestForm on the backend.
        """
        response = requests.post(
            f"{self.base_url}{path}",
            data=data,
            headers=self._auth_header(token),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def put(self, path: str, payload: dict[str, Any] | None = None, token: str | None = None) -> Any:
        response = requests.put(f"{self.base_url}{path}", json=payload, headers=self._headers(token), timeout=10)
        response.raise_for_status()
        return response.json()

    def delete(self, path: str, token: str | None = None) -> Any:
        response = requests.delete(f"{self.base_url}{path}", headers=self._headers(token), timeout=10)
        response.raise_for_status()
        return response.text

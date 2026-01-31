"""
Base resource class for API access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from memorer._http import HTTPClient


class BaseResource:
    """Base class for API resources."""

    def __init__(self, http: HTTPClient, owner_id: str | None = None) -> None:
        self._http = http
        self._owner_id = owner_id

    def _get_headers(self) -> dict[str, str]:
        """Get headers for requests."""
        return {}

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request."""
        return self._http.get(path, params=params, headers=self._get_headers())

    def _post(
        self, path: str, json_data: dict[str, Any] | None = None, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a POST request."""
        return self._http.post(path, json_data=json_data, params=params, headers=self._get_headers())

    def _put(self, path: str, json_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a PUT request."""
        return self._http.put(path, json_data=json_data, headers=self._get_headers())

    def _delete(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a DELETE request."""
        return self._http.delete(path, params=params, headers=self._get_headers())

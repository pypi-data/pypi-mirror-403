"""
Memorer SDK HTTP Client

Internal HTTP client wrapper using httpx with retry support.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any, Iterator

import httpx

from memorer.errors import NetworkError, raise_for_status

if TYPE_CHECKING:
    from memorer._config import ClientConfig

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

RETRY_BASE_DELAY = 0.5


def _should_retry(status_code: int, attempt: int, max_retries: int) -> bool:
    """Determine if a request should be retried."""
    return attempt < max_retries and status_code in RETRYABLE_STATUS_CODES


def _get_retry_delay(attempt: int, retry_after: float | None = None) -> float:
    """Calculate delay before next retry with exponential backoff."""
    if retry_after is not None:
        return retry_after
    return RETRY_BASE_DELAY * (2**attempt)


class HTTPClient:
    """Synchronous HTTP client for Memorer API with automatic retry."""

    def __init__(self, config: ClientConfig) -> None:
        self.config = config
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout),
                headers=self._build_headers(),
            )
        return self._client

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _merge_headers(self, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        headers = self._build_headers()
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request with automatic retry."""
        merged_headers = self._merge_headers(headers)
        attempt = 0
        last_error: Exception | None = None

        while True:
            try:
                response = self.client.request(
                    method=method,
                    url=path,
                    json=json_data,
                    params=params,
                    headers=merged_headers,
                )
                if response.status_code == 204:
                    return {}

                try:
                    data = response.json()
                except json.JSONDecodeError:
                    data = {"error": response.text or "Unknown error"}

                if _should_retry(response.status_code, attempt, self.config.max_retries):
                    retry_after = None
                    if response.status_code == 429:
                        retry_after_header = response.headers.get("Retry-After")
                        if retry_after_header:
                            try:
                                retry_after = float(retry_after_header)
                            except ValueError:
                                pass

                    delay = _get_retry_delay(attempt, retry_after)
                    time.sleep(delay)
                    attempt += 1
                    continue

                raise_for_status(response.status_code, data)
                return data

            except httpx.ConnectError as e:
                last_error = NetworkError(
                    f"Failed to connect to {self.config.base_url}", detail=str(e)
                )
                if attempt < self.config.max_retries:
                    delay = _get_retry_delay(attempt)
                    time.sleep(delay)
                    attempt += 1
                    continue
                raise last_error

            except httpx.TimeoutException as e:
                last_error = NetworkError("Request timed out", detail=str(e))
                if attempt < self.config.max_retries:
                    delay = _get_retry_delay(attempt)
                    time.sleep(delay)
                    attempt += 1
                    continue
                raise last_error

            except httpx.RequestError as e:
                raise NetworkError("Request failed", detail=str(e))

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("POST", path, json_data=json_data, params=params, headers=headers)

    def put(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("PUT", path, json_data=json_data, headers=headers)

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("DELETE", path, params=params, headers=headers)

    def stream_post(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Iterator[str]:
        """Make a streaming POST request, yielding raw SSE lines."""
        stream_headers = self._merge_headers(headers)
        stream_headers["Accept"] = "text/event-stream"

        try:
            with self.client.stream(
                "POST",
                path,
                json=json_data,
                headers=stream_headers,
            ) as response:
                if response.status_code >= 400:
                    response.read()
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        data = {"error": response.text or "Unknown error"}
                    raise_for_status(response.status_code, data)

                for line in response.iter_lines():
                    yield line
        except httpx.ConnectError as e:
            raise NetworkError(f"Failed to connect to {self.config.base_url}", detail=str(e))
        except httpx.TimeoutException as e:
            raise NetworkError("Request timed out", detail=str(e))
        except httpx.RequestError as e:
            raise NetworkError("Request failed", detail=str(e))

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

"""
Memorer SDK Configuration
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Internal constants
_API_BASE_URL = "https://api.memorer.ai"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2


@dataclass
class ClientConfig:
    """
    Configuration for the Memorer client.

    Args:
        api_key: API key for authentication (required).
        timeout: Request timeout in seconds. Defaults to 30.
        max_retries: Maximum number of retries for transient failures.
            Defaults to 2. Set to 0 to disable retries.
    """

    api_key: str
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    base_url: str = field(default=_API_BASE_URL, init=False)

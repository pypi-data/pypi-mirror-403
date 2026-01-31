"""
Token Manager

Handles OAuth2 client credentials flow with automatic token caching and refresh.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from dataclasses import dataclass

import httpx

log = logging.getLogger("timeback_common.auth")


@dataclass
class TokenManagerConfig:
    """Configuration for the token manager."""

    token_url: str
    """OAuth2 token endpoint URL."""

    client_id: str
    """OAuth2 client ID."""

    client_secret: str
    """OAuth2 client secret."""

    timeout: float = 30.0
    """Request timeout in seconds."""


class TokenManager:
    """
    OAuth2 token manager with automatic caching and refresh.

    Features:
    - Token caching with expiry tracking
    - Early refresh (60s before expiry) to avoid edge cases
    - Concurrent request de-duplication (one in-flight request at a time)
    - Invalidation support for 401 handling

    Example:
        ```python
        token_manager = TokenManager(TokenManagerConfig(
            token_url="https://auth.example.com/oauth2/token",
            client_id="your-client-id",
            client_secret="your-client-secret",
        ))

        token = await token_manager.get_token()
        ```
    """

    # Refresh tokens 60 seconds before actual expiry
    EARLY_REFRESH_SECONDS = 60

    def __init__(self, config: TokenManagerConfig) -> None:
        """
        Create a new TokenManager.

        Args:
            config: Token manager configuration
        """
        self._config = config
        self._access_token: str | None = None
        self._token_expiry: float = 0.0
        self._pending_request: asyncio.Task[str] | None = None

    async def get_token(self) -> str:
        """
        Get a valid access token.

        Returns a cached token if still valid, otherwise fetches a new one.
        Concurrent calls share a single in-flight request to avoid duplicate fetches.
        Tokens are refreshed 60 seconds before expiry to avoid edge cases.

        Returns:
            A valid access token string

        Raises:
            Exception: If token acquisition fails
        """
        # Check if we have a valid cached token
        if self._access_token and time.time() < self._token_expiry:
            log.debug("Using cached token")
            return self._access_token

        # If there's already a request in flight, wait for it
        if self._pending_request is not None:
            log.debug("Waiting for in-flight token request")
            return await self._pending_request

        # Start a new token fetch
        self._pending_request = asyncio.create_task(self._fetch_token())

        try:
            return await self._pending_request
        finally:
            self._pending_request = None

    async def _fetch_token(self) -> str:
        """Fetch a new access token from the token endpoint."""
        log.debug("Fetching new access token...")

        # Use HTTP Basic auth
        credentials = base64.b64encode(
            f"{self._config.client_id}:{self._config.client_secret}".encode()
        ).decode("ascii")

        start = time.perf_counter()

        async with httpx.AsyncClient(timeout=self._config.timeout) as client:
            response = await client.post(
                self._config.token_url,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                content="grant_type=client_credentials",
            )

        duration_ms = int((time.perf_counter() - start) * 1000)

        if response.status_code != 200:
            log.error(f"Token request failed: {response.status_code} {response.text}")
            raise Exception(
                f"Failed to obtain access token: {response.status_code} {response.text}"
            )

        data = response.json()
        self._access_token = data.get("access_token")

        if not self._access_token:
            raise Exception("No access_token in token response")

        # Refresh early (60s before actual expiry) to avoid edge cases
        expires_in = data.get("expires_in", 3600)
        self._token_expiry = time.time() + expires_in - self.EARLY_REFRESH_SECONDS

        log.debug(f"Token acquired ({duration_ms}ms, expires in {expires_in}s)")

        return self._access_token

    def invalidate(self) -> None:
        """
        Invalidate the cached token.

        Forces the next get_token() call to fetch a fresh token.
        Useful when a request fails with 401 Unauthorized.
        """
        log.debug("Token invalidated")
        self._access_token = None
        self._token_expiry = 0.0


__all__ = ["TokenManager", "TokenManagerConfig"]

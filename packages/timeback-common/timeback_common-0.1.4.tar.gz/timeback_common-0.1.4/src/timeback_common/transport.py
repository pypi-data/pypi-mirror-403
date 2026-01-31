"""
Base Transport Layer

HTTP transport with OAuth2 authentication, retries, and error handling.
"""

from __future__ import annotations

import contextlib
import logging
import os
import re
import time
import uuid
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from .errors import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .token_manager import TokenManager, TokenManagerConfig

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

MAX_RETRIES = 3
"""Maximum number of retry attempts for transient failures."""

RETRY_STATUS_CODES = [429, 503]
"""HTTP status codes that trigger automatic retry."""

INITIAL_RETRY_DELAY_MS = 1000
"""Initial delay before first retry (in milliseconds)."""

log = logging.getLogger("timeback_common.http")


def generate_request_id() -> str:
    """Generate a unique request ID for correlation."""
    return str(uuid.uuid4())[:8]


class BaseTransport:
    """
    Base HTTP transport layer for API communication.

    Handles OAuth2 authentication, request/response lifecycle,
    automatic retries for transient failures, and structured logging.

    Features:
    - Retries on 429/503 with exponential backoff + Retry-After
    - Operation-level timeout spanning all retries/backoff
    - X-Request-ID generation and propagation
    - Absolute URL path rejection (security)
    - Rich JSON parse error context
    - Token caching with expiry + concurrent de-duping
    - 401 token invalidation with single retry

    Subclasses should set service-specific env var names and URL defaults.
    """

    # Override in subclasses
    ENV_VAR_BASE_URL: str = "TIMEBACK_BASE_URL"
    ENV_VAR_AUTH_URL: str = "TIMEBACK_TOKEN_URL"
    ENV_VAR_CLIENT_ID: str = "TIMEBACK_CLIENT_ID"
    ENV_VAR_CLIENT_SECRET: str = "TIMEBACK_CLIENT_SECRET"

    DEFAULT_BASE_URL: str | None = None
    DEFAULT_AUTH_URL: str | None = None

    def __init__(
        self,
        *,
        base_url: str | None = None,
        auth_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 30.0,
        token_manager: TokenManager | None = None,
        http_client: httpx.AsyncClient | None = None,
        no_auth: bool = False,
    ) -> None:
        """
        Initialize transport.

        Args:
            base_url: API base URL
            auth_url: OAuth2 token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            timeout: Request timeout in seconds (applies as operation-level deadline)
            token_manager: Optional shared TokenManager (for provider mode).
                           If provided, auth_url/client_id/client_secret are not required.
            http_client: Optional pre-configured httpx.AsyncClient (for testing).
                         If provided, base_url is still required for URL construction.
            no_auth: If True, skip authentication entirely (for public/no-auth services).
                     No Authorization header will be included in requests.
        """
        # Resolve URLs
        self.base_url = base_url or os.environ.get(self.ENV_VAR_BASE_URL) or self.DEFAULT_BASE_URL
        self.auth_url = auth_url or os.environ.get(self.ENV_VAR_AUTH_URL) or self.DEFAULT_AUTH_URL

        if not self.base_url:
            raise ValueError(
                f"base_url is required. Provide it or set {self.ENV_VAR_BASE_URL} environment variable."
            )

        self.timeout = timeout
        self._client: httpx.AsyncClient | None = http_client
        self._injected_client = http_client is not None
        self._no_auth = no_auth

        # No-auth mode: skip token manager setup entirely
        if no_auth:
            self._token_manager: TokenManager | None = None
            self.client_id = None
            self.client_secret = None
        # Use injected token manager if provided (provider mode)
        elif token_manager is not None:
            self._token_manager = token_manager
            self.client_id = None
            self.client_secret = None
        else:
            # Standalone mode: require auth_url and credentials
            if not self.auth_url:
                raise ValueError(
                    f"auth_url is required. Provide it or set {self.ENV_VAR_AUTH_URL} environment variable."
                )

            # Resolve credentials
            self.client_id = client_id or os.environ.get(self.ENV_VAR_CLIENT_ID)
            self.client_secret = client_secret or os.environ.get(self.ENV_VAR_CLIENT_SECRET)

            if not self.client_id or not self.client_secret:
                raise AuthenticationError(
                    f"Missing credentials. Provide client_id/client_secret or set "
                    f"{self.ENV_VAR_CLIENT_ID}/{self.ENV_VAR_CLIENT_SECRET} environment variables."
                )

            # Token manager with caching and de-duping
            self._token_manager = TokenManager(
                TokenManagerConfig(
                    token_url=self.auth_url,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    timeout=timeout,
                )
            )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            # Don't recreate if this was an injected client that was closed
            if self._injected_client and self._client is not None:
                raise RuntimeError("Injected HTTP client has been closed")
            assert self.base_url is not None, "base_url must be set before making requests"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                # Don't set global timeout here; we handle it per-request
            )
        return self._client

    def _validate_path(self, path: str) -> None:
        """
        Validate that path is relative (security check).

        Rejects absolute URLs to prevent SSRF attacks.

        Args:
            path: The path to validate

        Raises:
            ValueError: If path is an absolute URL
        """
        if re.match(r"^[a-z][a-z0-9+.-]*:", path, re.IGNORECASE):
            raise ValueError(
                f"Absolute URLs are not allowed in path: {path}. Use relative paths only."
            )

    def _parse_retry_after(self, retry_after: str | None, attempt: int) -> float:
        """
        Parse Retry-After header value.

        Handles both formats per RFC 7231:
        - Numeric seconds: "120"
        - HTTP-date: "Wed, 21 Oct 2025 07:28:00 GMT"

        Args:
            retry_after: Retry-After header value
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        if not retry_after:
            # Exponential backoff: 1s, 2s, 4s, ...
            return (INITIAL_RETRY_DELAY_MS / 1000) * (2**attempt)

        # Try parsing as integer seconds
        try:
            seconds = int(retry_after)
            return float(seconds)
        except ValueError:
            pass

        # Try parsing as HTTP-date
        try:
            dt = parsedate_to_datetime(retry_after)
            delay = dt.timestamp() - time.time()
            return max(0.0, delay)
        except (ValueError, TypeError):
            pass

        # Fallback to exponential backoff
        return (INITIAL_RETRY_DELAY_MS / 1000) * (2**attempt)

    async def _sleep(self, seconds: float) -> None:
        """
        Delay execution for retry backoff.

        Override in tests to avoid real delays.
        """
        import asyncio

        await asyncio.sleep(seconds)

    def _extract_error_message(self, body: Any, fallback: str) -> str:
        """
        Extract error message from response body.

        Checks common error formats:
        - `message` (most APIs)
        - `error` (some APIs)
        - `imsx_description` (IMS Global: OneRoster, Caliper, QTI)

        Override in client transports for API-specific error formats.

        Args:
            body: The error response body
            fallback: Fallback message if none found

        Returns:
            Extracted error message
        """
        if isinstance(body, dict):
            if isinstance(body.get("message"), str):
                return body["message"]
            if isinstance(body.get("error"), str):
                return body["error"]
            if isinstance(body.get("imsx_description"), str):
                return body["imsx_description"]
        return fallback

    def _handle_error(
        self,
        status: int,
        body: Any,
        text: str,
        request_id: str,
    ) -> None:
        """
        Parse error response and raise appropriate APIError subclass.

        Args:
            status: HTTP status code
            body: Parsed response body (or None)
            text: Raw response text
            request_id: Request ID for logging

        Raises:
            AuthenticationError: For 401 responses
            ForbiddenError: For 403 responses
            NotFoundError: For 404 responses
            ValidationError: For 400/422 responses
            RateLimitError: For 429 responses
            ServerError: For 5xx responses
            APIError: For all other error status codes
        """
        message = self._extract_error_message(body, text or f"HTTP {status}")

        if status != 404:
            log.error(f"Request failed: {status} {message}", extra={"request_id": request_id})

        if status == 400:
            raise ValidationError(message, body)
        if status == 401:
            raise AuthenticationError(message, body)
        if status == 403:
            raise ForbiddenError(message, body)
        if status == 404:
            raise NotFoundError(message, body)
        if status == 422:
            raise ValidationError(message, body)
        if status == 429:
            raise RateLimitError(message, body)
        if status >= 500:
            raise ServerError(message, status, body)

        raise APIError(message, status, body)

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Make an authenticated HTTP request with retries.

        Automatically retries on transient failures (429, 503).
        Uses operation-level timeout spanning all retry attempts.

        Supports per-request headers.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (appended to base_url)
            json: JSON body for POST/PUT/PATCH
            params: Query parameters
            headers: Optional custom headers (merged with default headers)
            request_id: Optional request ID (generated if not provided)

        Returns:
            Parsed JSON response

        Raises:
            APIError: On HTTP errors or timeout
            AuthenticationError: On auth failures
            ValueError: If path is an absolute URL
        """
        # ─────────────────────────────────────────────────────────────────────
        # STEP 0: Generate request ID and validate path
        # ─────────────────────────────────────────────────────────────────────
        req_id = request_id or generate_request_id()
        self._validate_path(path)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 1: Set up operation-level timeout
        # ─────────────────────────────────────────────────────────────────────
        operation_start = time.time()
        operation_deadline = operation_start + self.timeout

        client = await self._get_client()

        # ─────────────────────────────────────────────────────────────────────
        # STEP 2: Retry loop
        # ─────────────────────────────────────────────────────────────────────
        for attempt in range(MAX_RETRIES):
            remaining_time = operation_deadline - time.time()

            if remaining_time <= 0:
                log.error(
                    "Request timeout before attempt", extra={"request_id": req_id, "path": path}
                )
                raise APIError("Request timeout", 408)

            is_last_attempt = attempt == MAX_RETRIES - 1

            # ─────────────────────────────────────────────────────────────────
            # STEP 3: Build headers (with or without auth)
            # ─────────────────────────────────────────────────────────────────
            default_headers: dict[str, str] = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Request-ID": req_id,
            }

            # Add Authorization header if auth is configured (not no-auth mode)
            if self._token_manager is not None:
                token = await self._token_manager.get_token()
                default_headers["Authorization"] = f"Bearer {token}"

            # Merge with per-request custom headers
            request_headers = {**default_headers, **(headers or {})}

            start = time.perf_counter()

            try:
                response = await client.request(
                    method,
                    path,
                    params=params,
                    headers=request_headers,
                    json=json,
                    timeout=min(remaining_time, self.timeout),
                )
            except httpx.TimeoutException:
                log.error(
                    "Request timeout during HTTP call", extra={"request_id": req_id, "path": path}
                )
                raise APIError("Request timeout", 408)

            duration_ms = int((time.perf_counter() - start) * 1000)
            log.debug(
                f"{'→' if attempt == 0 else '↻'} {method} {response.url} → {response.status_code} ({duration_ms}ms)",
                extra={"request_id": req_id, "attempt": attempt + 1 if attempt > 0 else None},
            )

            # ─────────────────────────────────────────────────────────────────
            # STEP 4: Handle retryable errors (429, 503)
            # ─────────────────────────────────────────────────────────────────
            should_retry = response.status_code in RETRY_STATUS_CODES and not is_last_attempt

            if should_retry:
                retry_after = response.headers.get("Retry-After")
                delay = self._parse_retry_after(retry_after, attempt)

                time_remaining = operation_deadline - time.time()
                if delay >= time_remaining:
                    log.error(
                        "Request timeout during retry backoff",
                        extra={"request_id": req_id, "path": path},
                    )
                    raise APIError("Request timeout", 408)

                log.warning(
                    f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})",
                    extra={"request_id": req_id, "status": response.status_code},
                )

                await self._sleep(delay)
                continue

            # ─────────────────────────────────────────────────────────────────
            # STEP 5: Handle 401 - invalidate token and raise (NO retry)
            # ─────────────────────────────────────────────────────────────────
            # On 401, invalidate token and throw UnauthorizedError.
            # We do NOT auto-retry on 401 - the caller must handle re-auth.
            if response.status_code == 401:
                log.debug("Got 401, invalidating token", extra={"request_id": req_id})
                if self._token_manager is not None:
                    self._token_manager.invalidate()
                # Fall through to error handling below

            # ─────────────────────────────────────────────────────────────────
            # STEP 6: Parse response body
            # ─────────────────────────────────────────────────────────────────
            text = ""
            body: Any = None

            if response.status_code != 204:
                try:
                    text = response.text
                except Exception:
                    text = ""

                if text and text.strip():
                    try:
                        body = response.json()
                    except Exception as e:
                        # Rich JSON parse error context
                        preview = text[:200] + "..." if len(text) > 200 else text
                        parse_error = str(e)

                        log.error(
                            "Failed to parse JSON response",
                            extra={
                                "request_id": req_id,
                                "url": str(response.url),
                                "status": response.status_code,
                                "content_type": response.headers.get("content-type"),
                                "body_preview": preview,
                                "error": parse_error,
                            },
                        )

                        if response.status_code >= 400:
                            # For error responses, include parse context
                            raise APIError(
                                f"Invalid JSON response from {response.url}",
                                response.status_code,
                                {"parse_error": parse_error, "body_preview": preview},
                            )
                        else:
                            # For success responses, this is unexpected
                            raise APIError(
                                f"Invalid JSON response from {response.url}",
                                response.status_code,
                                {"parse_error": parse_error, "body_preview": preview},
                            )

            # ─────────────────────────────────────────────────────────────────
            # STEP 7: Handle non-retryable errors
            # ─────────────────────────────────────────────────────────────────
            if response.status_code >= 400:
                self._handle_error(response.status_code, body, text, req_id)

            # ─────────────────────────────────────────────────────────────────
            # STEP 8: Success!
            # ─────────────────────────────────────────────────────────────────
            return body

        # Exhausted all retries
        log.error("Max retries exceeded", extra={"request_id": req_id, "path": path})
        raise APIError("Max retries exceeded")

    async def request_raw(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        request_id: str | None = None,
    ) -> httpx.Response:
        """
        Make an authenticated HTTP request and return the raw response.

        Like `request()`, but returns the httpx.Response instead of
        parsing it as JSON. Useful for accessing response headers.

        Supports per-request headers.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (appended to base_url)
            json: JSON body for POST/PUT/PATCH
            params: Query parameters
            headers: Optional custom headers (merged with default headers)
            request_id: Optional request ID (generated if not provided)

        Returns:
            Raw httpx.Response object

        Raises:
            APIError: On HTTP errors or timeout
            AuthenticationError: On auth failures
            ValueError: If path is an absolute URL
        """
        req_id = request_id or generate_request_id()
        self._validate_path(path)

        operation_start = time.time()
        operation_deadline = operation_start + self.timeout

        client = await self._get_client()

        for attempt in range(MAX_RETRIES):
            remaining_time = operation_deadline - time.time()

            if remaining_time <= 0:
                log.error(
                    "Request timeout before attempt", extra={"request_id": req_id, "path": path}
                )
                raise APIError("Request timeout", 408)

            is_last_attempt = attempt == MAX_RETRIES - 1

            # Build headers (with or without auth)
            default_headers: dict[str, str] = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Request-ID": req_id,
            }

            # Add Authorization header if auth is configured (not no-auth mode)
            if self._token_manager is not None:
                token = await self._token_manager.get_token()
                default_headers["Authorization"] = f"Bearer {token}"

            # Merge with per-request custom headers
            request_headers = {**default_headers, **(headers or {})}

            start = time.perf_counter()

            try:
                response = await client.request(
                    method,
                    path,
                    params=params,
                    headers=request_headers,
                    json=json,
                    timeout=min(remaining_time, self.timeout),
                )
            except httpx.TimeoutException:
                log.error(
                    "Request timeout during HTTP call", extra={"request_id": req_id, "path": path}
                )
                raise APIError("Request timeout", 408)

            duration_ms = int((time.perf_counter() - start) * 1000)
            log.debug(
                f"{'→' if attempt == 0 else '↻'} {method} {response.url} → {response.status_code} ({duration_ms}ms)",
                extra={"request_id": req_id, "attempt": attempt + 1 if attempt > 0 else None},
            )

            # Handle retryable errors (429, 503)
            should_retry = response.status_code in RETRY_STATUS_CODES and not is_last_attempt

            if should_retry:
                retry_after = response.headers.get("Retry-After")
                delay = self._parse_retry_after(retry_after, attempt)

                time_remaining = operation_deadline - time.time()
                if delay >= time_remaining:
                    log.error(
                        "Request timeout during retry backoff",
                        extra={"request_id": req_id, "path": path},
                    )
                    raise APIError("Request timeout", 408)

                log.warning(
                    f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})",
                    extra={"request_id": req_id, "status": response.status_code},
                )

                await self._sleep(delay)
                continue

            # Handle 401 - invalidate token and raise (NO retry)
            if response.status_code == 401:
                log.debug("Got 401, invalidating token", extra={"request_id": req_id})
                if self._token_manager is not None:
                    self._token_manager.invalidate()
                # Fall through to error handling below

            # Handle non-retryable errors
            if response.status_code >= 400:
                text = ""
                body: Any = None

                try:
                    text = response.text
                except Exception:
                    text = ""

                if text and text.strip():
                    with contextlib.suppress(Exception):
                        body = response.json()

                self._handle_error(response.status_code, body, text, req_id)

            # Success!
            return response

        # Exhausted all retries
        log.error("Max retries exceeded", extra={"request_id": req_id, "path": path})
        raise APIError("Max retries exceeded")

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        return await self.request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        return await self.request("POST", path, json=data, headers=headers)

    async def put(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return await self.request("PUT", path, json=data, headers=headers)

    async def patch(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a PATCH request."""
        return await self.request("PATCH", path, json=data, headers=headers)

    async def delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self.request("DELETE", path, headers=headers)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def invalidate_token(self) -> None:
        """Clear the cached access token. No-op if no auth is configured."""
        if self._token_manager is not None:
            self._token_manager.invalidate()


__all__ = ["BaseTransport"]

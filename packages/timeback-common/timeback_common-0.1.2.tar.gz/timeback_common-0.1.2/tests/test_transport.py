"""Tests for BaseTransport."""

import time
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from timeback_common import APIError, AuthenticationError, BaseTransport
from timeback_common.token_manager import TokenManager, TokenManagerConfig


class MockableTransport(BaseTransport):
    """Transport subclass for testing with mocked sleep and token."""

    def __init__(
        self,
        *,
        base_url: str = "https://api.example.com",
        auth_url: str = "https://auth.example.com/token",
        client_id: str = "test-id",
        client_secret: str = "test-secret",
        timeout: float = 30.0,
        mock_transport: httpx.MockTransport | None = None,
    ) -> None:
        # Skip parent __init__ to avoid token manager setup
        self.base_url = base_url
        self.auth_url = auth_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._mock_transport = mock_transport
        self._sleep_calls: list[float] = []

        # Mock token manager that always returns a token
        self._token_manager = AsyncMock()
        self._token_manager.get_token = AsyncMock(return_value="mock-token")
        self._token_manager.invalidate = lambda: None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                transport=self._mock_transport,
            )
        return self._client

    async def _sleep(self, seconds: float) -> None:
        """Record sleep calls instead of actually sleeping."""
        self._sleep_calls.append(seconds)


def create_mock_handler(responses: list[tuple[int, dict[str, Any] | str, dict[str, str] | None]]):
    """
    Create a mock transport handler that returns responses in order.

    Args:
        responses: List of (status_code, body, headers) tuples.
                   body can be a dict (JSON) or str (raw text).
    """
    call_count = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        if call_count >= len(responses):
            return httpx.Response(500, json={"error": "Unexpected request"})

        status, body, headers = responses[call_count]
        call_count += 1

        if isinstance(body, dict):
            return httpx.Response(status, json=body, headers=headers or {})
        else:
            return httpx.Response(status, text=body, headers=headers or {})

    return handler, lambda: call_count


class TestRetryBehavior:
    """Tests for retry logic on 429/503."""

    @pytest.mark.asyncio
    async def test_retries_on_503(self):
        """Should retry on 503 and succeed on second attempt."""
        handler, get_count = create_mock_handler(
            [
                (503, {"error": "Service Unavailable"}, None),
                (200, {"data": "success"}, None),
            ]
        )

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))
        result = await transport.get("/test")

        assert result == {"data": "success"}
        assert get_count() == 2
        assert len(transport._sleep_calls) == 1

    @pytest.mark.asyncio
    async def test_retries_on_429(self):
        """Should retry on 429 and succeed on second attempt."""
        handler, get_count = create_mock_handler(
            [
                (429, {"error": "Too Many Requests"}, None),
                (200, {"data": "success"}, None),
            ]
        )

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))
        result = await transport.get("/test")

        assert result == {"data": "success"}
        assert get_count() == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Should raise the final error after max retries exceeded."""
        handler, get_count = create_mock_handler(
            [
                (503, {"error": "fail"}, None),
                (503, {"error": "fail"}, None),
                (503, {"error": "fail"}, None),
            ]
        )

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))

        # On the last attempt, the error is raised (not retried)
        with pytest.raises(APIError) as exc_info:
            await transport.get("/test")

        # The final 503 error is raised
        assert exc_info.value.status_code == 503
        assert get_count() == 3


class TestRetryAfterParsing:
    """Tests for Retry-After header parsing."""

    @pytest.mark.asyncio
    async def test_retry_after_seconds(self):
        """Should respect Retry-After header in seconds."""
        handler, _ = create_mock_handler(
            [
                (429, {"error": "rate limited"}, {"Retry-After": "5"}),
                (200, {"data": "success"}, None),
            ]
        )

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))
        await transport.get("/test")

        assert transport._sleep_calls[0] == 5.0

    @pytest.mark.asyncio
    async def test_exponential_backoff_without_header(self):
        """Should use exponential backoff when no Retry-After header."""
        handler, _ = create_mock_handler(
            [
                (503, {"error": "fail"}, None),
                (503, {"error": "fail"}, None),
                (200, {"data": "success"}, None),
            ]
        )

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))
        await transport.get("/test")

        # First retry: 1s, second retry: 2s
        assert transport._sleep_calls[0] == 1.0
        assert transport._sleep_calls[1] == 2.0


class TestOperationLevelTimeout:
    """Tests for operation-level deadline."""

    @pytest.mark.asyncio
    async def test_timeout_before_retry(self):
        """Should fail if retry would exceed operation deadline."""
        handler, _ = create_mock_handler(
            [
                (503, {"error": "fail"}, {"Retry-After": "60"}),  # 60s delay
            ]
        )

        # Only 10s timeout, so 60s Retry-After should exceed it
        transport = MockableTransport(
            mock_transport=httpx.MockTransport(handler),
            timeout=10.0,
        )

        with pytest.raises(APIError) as exc_info:
            await transport.get("/test")

        assert exc_info.value.status_code == 408
        assert "timeout" in str(exc_info.value).lower()


class TestRequestIdPropagation:
    """Tests for X-Request-ID header."""

    @pytest.mark.asyncio
    async def test_request_id_header_present(self):
        """Should include X-Request-ID header in requests."""
        captured_headers: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_headers.update(dict(request.headers))
            return httpx.Response(200, json={"ok": True})

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))
        await transport.get("/test")

        assert "x-request-id" in captured_headers
        assert len(captured_headers["x-request-id"]) == 8  # UUID prefix

    @pytest.mark.asyncio
    async def test_request_id_stable_across_retries(self):
        """Should use same request ID across retry attempts."""
        request_ids: list[str] = []

        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            request_ids.append(request.headers.get("x-request-id", ""))
            call_count += 1
            if call_count < 2:
                return httpx.Response(503, json={"error": "fail"})
            return httpx.Response(200, json={"ok": True})

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))
        await transport.get("/test")

        assert len(request_ids) == 2
        assert request_ids[0] == request_ids[1]  # Same ID across retries


class TestAbsoluteUrlGuard:
    """Tests for absolute URL rejection."""

    @pytest.mark.asyncio
    async def test_rejects_absolute_url(self):
        """Should reject absolute URLs in path."""
        transport = MockableTransport(
            mock_transport=httpx.MockTransport(lambda _: httpx.Response(200))
        )

        with pytest.raises(ValueError) as exc_info:
            await transport.get("https://evil.example.com/steal-data")

        assert "Absolute URLs are not allowed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_allows_relative_paths(self):
        """Should allow relative paths."""
        transport = MockableTransport(
            mock_transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"ok": True}))
        )

        # These should all work
        await transport.get("/api/users")
        await transport.get("api/users")


class TestTokenInvalidationOn401:
    """Tests for 401 token invalidation behavior.

    On 401, invalidate token and raise immediately (NO retry).
    """

    @pytest.mark.asyncio
    async def test_401_invalidates_token_and_raises(self):
        """Should invalidate token and raise on 401 (no retry)."""
        call_count = 0
        invalidate_called = False

        def handler(_request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(401, json={"error": "Unauthorized"})

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))

        # Track invalidate calls
        assert transport._token_manager is not None
        original_invalidate = transport._token_manager.invalidate

        def track_invalidate():
            nonlocal invalidate_called
            invalidate_called = True
            original_invalidate()

        transport._token_manager.invalidate = track_invalidate

        with pytest.raises(AuthenticationError):
            await transport.get("/test")

        # Only 1 request, no retry on 401
        assert call_count == 1
        assert invalidate_called

    @pytest.mark.asyncio
    async def test_401_does_not_retry(self):
        """Should NOT retry on 401 (raise immediately)."""
        call_count = 0

        def handler(_request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(401, json={"error": "Unauthorized"})

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))

        with pytest.raises(AuthenticationError):
            await transport.get("/test")

        # no retry on 401
        assert call_count == 1


class TestJsonParseErrorContext:
    """Tests for JSON parse error handling."""

    @pytest.mark.asyncio
    async def test_includes_body_preview_on_parse_error(self):
        """Should include body preview when JSON parsing fails."""

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                text="<html>Not JSON!</html>",
                headers={"content-type": "text/html"},
            )

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))

        with pytest.raises(APIError) as exc_info:
            await transport.get("/test")

        error = exc_info.value
        assert error.response is not None
        assert "parse_error" in error.response
        assert "body_preview" in error.response
        assert "<html>" in error.response["body_preview"]


class TestNoAuthMode:
    """Tests for no-auth mode."""

    @pytest.mark.asyncio
    async def test_no_auth_mode_skips_authorization_header(self):
        """Should not include Authorization header in no-auth mode."""
        captured_headers: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_headers.update(dict(request.headers))
            return httpx.Response(200, json={"ok": True})

        # Create transport with no_auth=True
        transport = BaseTransport(
            base_url="https://api.example.com",
            no_auth=True,
            http_client=httpx.AsyncClient(
                base_url="https://api.example.com",
                transport=httpx.MockTransport(handler),
            ),
        )

        await transport.get("/test")

        # No Authorization header should be present
        assert "authorization" not in captured_headers

    @pytest.mark.asyncio
    async def test_no_auth_mode_includes_other_headers(self):
        """Should include standard headers even in no-auth mode."""
        captured_headers: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_headers.update(dict(request.headers))
            return httpx.Response(200, json={"ok": True})

        transport = BaseTransport(
            base_url="https://api.example.com",
            no_auth=True,
            http_client=httpx.AsyncClient(
                base_url="https://api.example.com",
                transport=httpx.MockTransport(handler),
            ),
        )

        await transport.get("/test")

        # Standard headers should be present
        assert "content-type" in captured_headers
        assert "accept" in captured_headers
        assert "x-request-id" in captured_headers

    def test_no_auth_mode_no_token_manager(self):
        """Should not create token manager in no-auth mode."""
        transport = BaseTransport(
            base_url="https://api.example.com",
            no_auth=True,
        )

        assert transport._token_manager is None
        assert transport._no_auth is True

    def test_invalidate_token_is_noop_in_no_auth_mode(self):
        """invalidate_token() should be a no-op in no-auth mode."""
        transport = BaseTransport(
            base_url="https://api.example.com",
            no_auth=True,
        )

        # Should not raise
        transport.invalidate_token()

    @pytest.mark.asyncio
    async def test_401_does_not_crash_in_no_auth_mode(self):
        """Should handle 401 gracefully in no-auth mode (no token to invalidate)."""

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "Unauthorized"})

        transport = BaseTransport(
            base_url="https://api.example.com",
            no_auth=True,
            http_client=httpx.AsyncClient(
                base_url="https://api.example.com",
                transport=httpx.MockTransport(handler),
            ),
        )

        with pytest.raises(AuthenticationError):
            await transport.get("/test")


class TestQueryParams:
    """Tests for query parameter handling - Bug #1 from 2026-01-19.

    The bug was that params weren't being passed to httpx.client.request(),
    causing API filters to be silently ignored.
    """

    @pytest.mark.asyncio
    async def test_params_are_passed_to_request(self):
        """Query params should appear in the actual HTTP request URL."""
        captured_request: httpx.Request | None = None

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_request
            captured_request = request
            return httpx.Response(200, json={"data": "success"})

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))
        await transport.get("/users", params={"filter": "email='test@example.com'"})

        assert captured_request is not None
        # The params should be in the URL as query string
        assert "filter=" in str(captured_request.url)
        assert "email" in str(captured_request.url)

    @pytest.mark.asyncio
    async def test_multiple_params(self):
        """Multiple query params should all be included."""
        captured_request: httpx.Request | None = None

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_request
            captured_request = request
            return httpx.Response(200, json={"users": []})

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))
        await transport.get(
            "/users", params={"limit": 10, "offset": 20, "filter": "role='teacher'"}
        )

        assert captured_request is not None
        url_str = str(captured_request.url)
        assert "limit=10" in url_str
        assert "offset=20" in url_str
        assert "filter=" in url_str

    @pytest.mark.asyncio
    async def test_empty_params_ok(self):
        """Empty params dict should work without query string."""
        captured_request: httpx.Request | None = None

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_request
            captured_request = request
            return httpx.Response(200, json={"data": "success"})

        transport = MockableTransport(mock_transport=httpx.MockTransport(handler))
        await transport.get("/users", params={})

        assert captured_request is not None
        # No query string when params is empty
        assert "?" not in str(captured_request.url) or str(captured_request.url).endswith("?")


class TestTokenManager:
    """Tests for TokenManager."""

    @pytest.mark.asyncio
    async def test_caches_token_after_set(self):
        """Should return cached token when set directly."""
        manager = TokenManager(
            TokenManagerConfig(
                token_url="https://auth.example.com/token",
                client_id="test-id",
                client_secret="test-secret",
            )
        )

        # Manually set token (simulating a successful fetch)
        manager._access_token = "test-token"
        manager._token_expiry = time.time() + 3600

        # Token should be returned from cache without fetching
        token = await manager.get_token()
        assert token == "test-token"

    def test_invalidate_clears_cache(self):
        """Invalidate should clear cached token."""
        manager = TokenManager(
            TokenManagerConfig(
                token_url="https://auth.example.com/token",
                client_id="test-id",
                client_secret="test-secret",
            )
        )
        manager._access_token = "cached-token"
        manager._token_expiry = time.time() + 3600

        manager.invalidate()

        assert manager._access_token is None
        assert manager._token_expiry == 0.0

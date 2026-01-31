"""
Tests for pagination utilities.

Covers header-based and body-based pagination parsing strategies,
plus Paginator class tests.
"""

from __future__ import annotations

import pytest
from httpx import Headers

from timeback_common.pagination import DEFAULT_MAX_ITEMS, PageResult, Paginator
from timeback_common.pagination_strategies import (
    parse_body_pagination,
    parse_body_pagination_raw,
    parse_header_has_more,
    parse_header_total,
)

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER PAGINATION PARSING
# ═══════════════════════════════════════════════════════════════════════════════


class TestHeaderPagination:
    """Tests for header-based pagination parsing."""

    def test_returns_data_array(self):
        """Returns data array."""
        headers = Headers()
        data = [{"id": 1}, {"id": 2}]

        assert parse_header_has_more(headers) is False
        assert parse_header_total(headers) is None
        assert data == [{"id": 1}, {"id": 2}]

    def test_parses_x_total_count_header(self):
        """Parses X-Total-Count header."""
        headers = Headers({"x-total-count": "100"})

        assert parse_header_total(headers) == 100

    def test_sets_has_more_true_when_link_contains_next(self):
        """Sets hasMore true when Link header contains rel="next"."""
        headers = Headers({"link": '<https://api.example.com/users?page=2>; rel="next"'})

        assert parse_header_has_more(headers) is True

    def test_sets_has_more_false_when_no_next_link(self):
        """Sets hasMore false when no next link."""
        headers = Headers({"link": '<https://api.example.com/users?page=1>; rel="prev"'})

        assert parse_header_has_more(headers) is False

    def test_handles_missing_x_total_count_header(self):
        """Handles missing X-Total-Count header."""
        headers = Headers()

        assert parse_header_total(headers) is None

    def test_handles_invalid_x_total_count_header(self):
        """Handles invalid X-Total-Count header."""
        headers = Headers({"x-total-count": "invalid"})

        assert parse_header_total(headers) is None

    def test_detects_has_more_with_single_quoted_rel(self):
        """Detects hasMore with single-quoted rel."""
        headers = Headers({"link": "<https://api.example.com/users?page=2>; rel='next'"})

        assert parse_header_has_more(headers) is True

    def test_detects_has_more_with_unquoted_rel(self):
        """Detects hasMore with unquoted rel."""
        headers = Headers({"link": "<https://api.example.com/users?page=2>; rel=next"})

        assert parse_header_has_more(headers) is True


class TestBodyPagination:
    """Tests for body-based pagination parsing."""

    def test_extracts_data_from_specified_key(self):
        """Extracts data from specified key."""
        body = {
            "users": [{"id": 1}, {"id": 2}],
            "totalCount": 10,
            "pageCount": 2,
            "pageNumber": 1,
        }

        result = parse_body_pagination(body, "users")

        assert result["data"] == [{"id": 1}, {"id": 2}]

    def test_returns_total_from_total_count(self):
        """Returns total from totalCount."""
        body = {
            "users": [{"id": 1}],
            "totalCount": 100,
            "pageCount": 10,
            "pageNumber": 1,
        }

        result = parse_body_pagination(body, "users")

        assert result["total"] == 100

    def test_sets_has_more_true_when_page_number_less_than_page_count(self):
        """Sets hasMore true when pageNumber < pageCount."""
        body = {
            "users": [{"id": 1}],
            "totalCount": 50,
            "pageCount": 5,
            "pageNumber": 1,
        }

        result = parse_body_pagination(body, "users")

        assert result["hasMore"] is True

    def test_sets_has_more_false_when_page_number_equals_page_count(self):
        """Sets hasMore false when pageNumber equals pageCount."""
        body = {
            "users": [{"id": 1}],
            "totalCount": 50,
            "pageCount": 5,
            "pageNumber": 5,
        }

        result = parse_body_pagination(body, "users")

        assert result["hasMore"] is False

    def test_handles_missing_data_key_as_empty_array(self):
        """Handles missing data key as empty array."""
        body = {
            "totalCount": 0,
            "pageCount": 0,
            "pageNumber": 1,
        }

        result = parse_body_pagination(body, "users")

        assert result["data"] == []


class TestBodyPaginationRaw:
    """Tests for raw body pagination parsing."""

    def test_returns_full_body_as_data(self):
        """Returns full body as data for Paginator unwrapKey."""
        body = {
            "users": [{"id": 1}, {"id": 2}],
            "totalCount": 10,
            "pageCount": 2,
            "pageNumber": 1,
        }

        result = parse_body_pagination_raw(body)

        assert result["data"] is body

    def test_returns_total_from_total_count(self):
        """Returns total from totalCount."""
        body = {
            "users": [{"id": 1}],
            "totalCount": 100,
            "pageCount": 10,
            "pageNumber": 1,
        }

        result = parse_body_pagination_raw(body)

        assert result["total"] == 100

    def test_sets_has_more_correctly(self):
        """Sets hasMore correctly."""
        body_with_more = {
            "users": [],
            "totalCount": 50,
            "pageCount": 5,
            "pageNumber": 2,
        }

        body_no_more = {
            "users": [],
            "totalCount": 50,
            "pageCount": 5,
            "pageNumber": 5,
        }

        assert parse_body_pagination_raw(body_with_more)["hasMore"] is True
        assert parse_body_pagination_raw(body_no_more)["hasMore"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# PAGINATOR CLASS TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class MockTransport:
    """Mock transport for testing paginator."""

    def __init__(self, pages: list[list[dict]], unwrap_key: str = "items"):
        """
        Initialize with a list of pages to return.

        Args:
            pages: List of pages, each page is a list of items
            unwrap_key: Key to wrap items under in response
        """
        self._pages = pages
        self._unwrap_key = unwrap_key
        self._call_count = 0
        self._last_params: dict | None = None

    async def get(self, path: str, *, params: dict | None = None) -> dict:  # noqa: ARG002
        """Return the next page."""
        self._last_params = params
        if self._call_count >= len(self._pages):
            return {self._unwrap_key: []}
        page = self._pages[self._call_count]
        self._call_count += 1
        return {self._unwrap_key: page}


class MockTransportMalformed:
    """Mock transport that returns malformed responses for validation testing."""

    def __init__(self, response: dict):
        """Initialize with the response to return."""
        self._response = response

    async def get(self, path: str, *, params: dict | None = None) -> dict:  # noqa: ARG002
        """Return the malformed response."""
        return self._response


class TestPaginatorFirstPage:
    """Tests for Paginator.first_page() method."""

    @pytest.mark.asyncio
    async def test_returns_page_result(self):
        """first_page() returns PageResult with data and metadata."""
        transport = MockTransport([[{"id": 1}, {"id": 2}]])
        paginator = Paginator(transport, "/test", unwrap_key="items", limit=10)

        result = await paginator.first_page()

        assert isinstance(result, PageResult)
        assert result.data == [{"id": 1}, {"id": 2}]
        assert result.has_more is False  # 2 items < limit of 10
        assert result.next_offset is None

    @pytest.mark.asyncio
    async def test_has_more_when_page_full(self):
        """first_page() sets has_more=True when page is full."""
        transport = MockTransport([[{"id": i} for i in range(5)]])
        paginator = Paginator(transport, "/test", unwrap_key="items", limit=5)

        result = await paginator.first_page()

        assert result.has_more is True
        assert result.next_offset == 5


class TestPaginatorToArray:
    """Tests for Paginator.to_array() method with safety guard."""

    @pytest.mark.asyncio
    async def test_collects_all_items(self):
        """to_array() collects all items from all pages."""
        transport = MockTransport(
            [
                [{"id": 1}, {"id": 2}],
                [{"id": 3}, {"id": 4}],
            ]
        )
        paginator = Paginator(transport, "/test", unwrap_key="items", limit=2)

        result = await paginator.to_array()

        assert result == [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]

    @pytest.mark.asyncio
    async def test_raises_on_max_items_exceeded(self):
        """to_array() raises RuntimeError when max_items exceeded."""
        transport = MockTransport([[{"id": i} for i in range(100)]])
        paginator = Paginator(transport, "/test", unwrap_key="items", limit=100)

        with pytest.raises(RuntimeError, match="exceeded max_items limit of 5"):
            await paginator.to_array(max_items=5)

    @pytest.mark.asyncio
    async def test_default_max_items(self):
        """to_array() has default max_items of 10,000."""
        assert DEFAULT_MAX_ITEMS == 10_000

    @pytest.mark.asyncio
    async def test_none_max_items_disables_guard(self):
        """to_array(max_items=None) disables safety guard."""
        transport = MockTransport([[{"id": i} for i in range(50)]])
        paginator = Paginator(transport, "/test", unwrap_key="items", limit=50)

        # Should not raise even though we'd normally hit a limit
        result = await paginator.to_array(max_items=None)

        assert len(result) == 50


# ═══════════════════════════════════════════════════════════════════════════════
# PAGINATOR PAGINATION STYLE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestPaginatorPaginationStyle:
    """Tests for Paginator pagination_style option."""

    @pytest.mark.asyncio
    async def test_offset_style_uses_limit_offset(self):
        """Offset pagination style uses limit/offset params."""
        transport = MockTransport([[{"id": 1}], [{"id": 2}]])
        paginator = Paginator(
            transport,
            "/test",
            unwrap_key="items",
            limit=1,
            pagination_style="offset",
        )

        await paginator.to_array()

        # First call should have offset=0, second offset=1
        assert transport._call_count == 2

    @pytest.mark.asyncio
    async def test_page_style_uses_limit_page(self):
        """Page pagination style uses limit/page params."""
        transport = MockTransport([[{"id": 1}], [{"id": 2}]])
        paginator = Paginator(
            transport,
            "/test",
            unwrap_key="items",
            limit=1,
            pagination_style="page",
        )

        await paginator.to_array()

        # Should use page parameter (1-indexed)
        assert transport._call_count == 2
        # Last params should have page, not offset
        assert "page" in transport._last_params
        assert "offset" not in transport._last_params

    @pytest.mark.asyncio
    async def test_first_page_uses_correct_style(self):
        """first_page() respects pagination_style."""
        transport = MockTransport([[{"id": 1}]])
        paginator = Paginator(
            transport,
            "/test",
            unwrap_key="items",
            limit=10,
            pagination_style="page",
        )

        await paginator.first_page()

        assert "page" in transport._last_params
        assert transport._last_params["page"] == 1

    @pytest.mark.asyncio
    async def test_first_uses_correct_style(self):
        """first() respects pagination_style."""
        transport = MockTransport([[{"id": 1}]])
        paginator = Paginator(
            transport,
            "/test",
            unwrap_key="items",
            pagination_style="page",
        )

        await paginator.first()

        assert "page" in transport._last_params


# ═══════════════════════════════════════════════════════════════════════════════
# PAGINATOR TRANSFORM TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestPaginatorTransform:
    """Tests for Paginator transform option."""

    @pytest.mark.asyncio
    async def test_transform_applied_to_items(self):
        """Transform function is applied to each item."""
        transport = MockTransport([[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]])
        paginator = Paginator(
            transport,
            "/test",
            unwrap_key="items",
            transform=lambda x: x["name"].upper(),
        )

        result = await paginator.to_array()

        assert result == ["ALICE", "BOB"]

    @pytest.mark.asyncio
    async def test_transform_applied_to_first_page(self):
        """Transform is applied to first_page() results."""
        transport = MockTransport([[{"id": 1, "name": "Alice"}]])
        paginator = Paginator(
            transport,
            "/test",
            unwrap_key="items",
            limit=10,
            transform=lambda x: {"id": x["id"], "upper_name": x["name"].upper()},
        )

        result = await paginator.first_page()

        assert result.data == [{"id": 1, "upper_name": "ALICE"}]

    @pytest.mark.asyncio
    async def test_transform_applied_to_first(self):
        """Transform is applied to first() result."""
        transport = MockTransport([[{"id": 1, "name": "Alice"}]])
        paginator = Paginator(
            transport,
            "/test",
            unwrap_key="items",
            transform=lambda x: x["name"],
        )

        result = await paginator.first()

        assert result == "Alice"

    @pytest.mark.asyncio
    async def test_no_transform_when_none(self):
        """Items are not transformed when transform is None."""
        transport = MockTransport([[{"id": 1}]])
        paginator = Paginator(transport, "/test", unwrap_key="items", transform=None)

        result = await paginator.to_array()

        assert result == [{"id": 1}]


# ═══════════════════════════════════════════════════════════════════════════════
# PAGINATOR VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestPaginatorValidation:
    """Tests for Paginator response validation to prevent infinite loops."""

    @pytest.mark.asyncio
    async def test_raises_on_non_list_response(self):
        """Raises RuntimeError when unwrap_key returns non-list."""
        transport = MockTransportMalformed({"items": "not a list"})
        paginator = Paginator(transport, "/test", unwrap_key="items")

        with pytest.raises(RuntimeError, match="expected list"):
            await paginator.to_array()

    @pytest.mark.asyncio
    async def test_raises_on_dict_response(self):
        """Raises RuntimeError when unwrap_key returns dict."""
        transport = MockTransportMalformed({"items": {"nested": "dict"}})
        paginator = Paginator(transport, "/test", unwrap_key="items")

        with pytest.raises(RuntimeError, match="expected list"):
            await paginator.to_array()

    @pytest.mark.asyncio
    async def test_handles_none_as_empty(self):
        """Treats None as empty list (with warning)."""
        transport = MockTransportMalformed({"items": None})
        paginator = Paginator(transport, "/test", unwrap_key="items")

        result = await paginator.to_array()

        assert result == []

    @pytest.mark.asyncio
    async def test_handles_missing_key_as_empty(self):
        """Treats missing unwrap_key as empty list."""
        transport = MockTransportMalformed({"other_key": []})
        paginator = Paginator(transport, "/test", unwrap_key="items")

        result = await paginator.to_array()

        assert result == []

    @pytest.mark.asyncio
    async def test_first_page_validates(self):
        """first_page() validates response."""
        transport = MockTransportMalformed({"items": "invalid"})
        paginator = Paginator(transport, "/test", unwrap_key="items", limit=10)

        with pytest.raises(RuntimeError, match="expected list"):
            await paginator.first_page()

    @pytest.mark.asyncio
    async def test_first_validates(self):
        """first() validates response."""
        transport = MockTransportMalformed({"items": 123})
        paginator = Paginator(transport, "/test", unwrap_key="items")

        with pytest.raises(RuntimeError, match="expected list"):
            await paginator.first()

"""
Shared Pagination Support

Async iterator for paginated API responses.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypeVar

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

T = TypeVar("T")

log = logging.getLogger("timeback_common.pagination")

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_LIMIT = 100
"""Default page size for paginated requests."""

DEFAULT_MAX_ITEMS = 10_000
"""Default maximum items for to_array() to prevent OOM."""

# Pagination style types
PaginationStyle = Literal["offset", "page"]
"""Pagination style: 'offset' (limit/offset) or 'page' (limit/page, 1-indexed)."""


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE RESULT
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class PageResult[T]:
    """
    Result of fetching a single page of resources.

    Provides pagination metadata for building custom pagination UIs.
    """

    data: list[T]
    """Array of items in this page."""

    has_more: bool
    """Whether more pages are available."""

    total: int | None = None
    """Total count of items (if provided by server)."""

    next_offset: int | None = None
    """Offset to use for fetching the next page."""


class TransportProtocol(Protocol):
    """Protocol for transport classes that support pagination."""

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]: ...


class Paginator[T]:
    """
    Async paginator for list endpoints.

    Lazily fetches pages as you iterate, handling offset-based pagination.
    Automatically fetches subsequent pages as you iterate, making it easy
    to process large datasets without manual pagination handling.

    Example:
        ```python
        # Iterate over all items
        async for user in paginator:
            print(user["name"])

        # Collect all items into an array (with safety guard)
        all_users = await paginator.to_array()

        # Get just the first page with metadata
        page = await paginator.first_page()
        print(f"Got {len(page.data)} of {page.total} users")

        # Get just the first item
        first = await paginator.first()
        ```
    """

    def __init__(
        self,
        transport: TransportProtocol,
        path: str,
        *,
        unwrap_key: str,
        params: dict[str, Any] | None = None,
        limit: int = DEFAULT_LIMIT,
        max_items: int | None = None,
        pagination_style: PaginationStyle = "offset",
        transform: Callable[[Any], T] | None = None,
    ) -> None:
        """
        Initialize paginator.

        Args:
            transport: Transport instance with get() method
            path: API endpoint path
            unwrap_key: Key to unwrap from response (e.g., "users", "events")
            params: Additional query parameters
            limit: Items per page
            max_items: Maximum total items to fetch (None for unlimited)
            pagination_style: 'offset' (limit/offset) or 'page' (limit/page, 1-indexed)
            transform: Optional function to transform each item before yielding
        """
        self._transport = transport
        self._path = path
        self._unwrap_key = unwrap_key
        self._params = params or {}
        self._limit = limit
        self._max_items = max_items
        self._pagination_style = pagination_style
        self._transform = transform
        # Internal state
        self._offset = 0
        self._page = 1  # For page-style pagination (1-indexed)
        self._total_fetched = 0
        self._exhausted = False
        self._buffer: list[T] = []
        self._buffer_index = 0

    def _validate_items(self, items: Any, source: str) -> list[Any]:
        """
        Validate unwrapped items to prevent infinite loops on malformed responses.

        Args:
            items: The items to validate
            source: Description of where items came from (for error message)

        Returns:
            Validated list of items

        Raises:
            RuntimeError: If items is not a list
        """
        if items is None:
            log.warning(
                "Paginator received None for unwrap_key='%s' from %s, treating as empty",
                self._unwrap_key,
                source,
            )
            return []

        if not isinstance(items, list):
            msg = (
                f"Paginator expected list for unwrap_key='{self._unwrap_key}' from {source}, "
                f"got {type(items).__name__}. Check API response structure."
            )
            raise RuntimeError(msg)

        return items

    async def _fetch_page(self) -> list[T]:
        """Fetch the next page of results."""
        # Build pagination params based on style
        if self._pagination_style == "page":
            params = {
                **self._params,
                "limit": self._limit,
                "page": self._page,
            }
        else:
            params = {
                **self._params,
                "limit": self._limit,
                "offset": self._offset,
            }

        response = await self._transport.get(self._path, params=params)
        raw_items = response.get(self._unwrap_key)

        # Validate to prevent infinite loops on malformed responses
        items = self._validate_items(raw_items, f"GET {self._path}")

        # Apply transform if provided
        if self._transform is not None:
            items = [self._transform(item) for item in items]

        # Update state based on pagination style
        if self._pagination_style == "page":
            self._page += 1
        else:
            self._offset += len(items)

        # Check if exhausted
        if len(items) < self._limit:
            self._exhausted = True

        return items

    def __aiter__(self) -> AsyncIterator[T]:
        """Return async iterator."""
        return self

    async def __anext__(self) -> T:
        """Get next item, fetching pages as needed."""
        # Check max items limit
        if self._max_items is not None and self._total_fetched >= self._max_items:
            raise StopAsyncIteration

        # If buffer is exhausted, fetch more
        while self._buffer_index >= len(self._buffer):
            if self._exhausted:
                raise StopAsyncIteration

            self._buffer = await self._fetch_page()
            self._buffer_index = 0

            if not self._buffer:
                raise StopAsyncIteration

        # Return next item from buffer
        item = self._buffer[self._buffer_index]
        self._buffer_index += 1
        self._total_fetched += 1
        return item

    async def to_list(self) -> list[T]:
        """
        Fetch all pages and return as a single list.

        Alias for `to_array()` without safety guard.

        Returns:
            List of all items across all pages
        """
        all_items: list[T] = []

        async for item in self:
            all_items.append(item)

        return all_items

    async def to_array(self, *, max_items: int | None = DEFAULT_MAX_ITEMS) -> list[T]:
        """
        Collect all items into an array.

        **Warning**: Use with caution on large datasets as this loads
        all items into memory. Consider iterating with `async for` for
        better memory efficiency.

        Args:
            max_items: Maximum items to collect (default: 10,000).
                Raises error if limit is exceeded. Set to None to disable.

        Returns:
            List of all items across all pages

        Raises:
            RuntimeError: If max_items limit is exceeded
        """
        all_items: list[T] = []

        async for item in self:
            if max_items is not None and len(all_items) >= max_items:
                raise RuntimeError(
                    f"to_array() exceeded max_items limit of {max_items}. "
                    "Use 'async for' to stream large datasets, or increase max_items."
                )
            all_items.append(item)

        return all_items

    async def first(self) -> T | None:
        """
        Fetch just the first item.

        Returns:
            First item or None if empty
        """
        # Build params for first item based on pagination style
        if self._pagination_style == "page":
            params = {**self._params, "limit": 1, "page": 1}
        else:
            params = {**self._params, "limit": 1, "offset": 0}

        response = await self._transport.get(self._path, params=params)
        raw_items = response.get(self._unwrap_key)
        items = self._validate_items(raw_items, f"first() GET {self._path}")

        if not items:
            return None

        item = items[0]
        if self._transform is not None:
            return self._transform(item)
        return item

    async def first_page(self) -> PageResult[T]:
        """
        Fetch only the first page of results.

        Useful when you need pagination metadata (total count, has_more)
        or want to implement custom pagination UI.

        Returns:
            PageResult with data, has_more, total, and next_offset
        """
        # Build params based on pagination style
        if self._pagination_style == "page":
            page = self._params.get("page", 1) or 1
            params = {
                **self._params,
                "limit": self._limit,
                "page": page,
            }
        else:
            offset = self._params.get("offset", 0) or 0
            params = {
                **self._params,
                "limit": self._limit,
                "offset": offset,
            }

        response = await self._transport.get(self._path, params=params)
        raw_items = response.get(self._unwrap_key)
        items = self._validate_items(raw_items, f"first_page() GET {self._path}")

        # Apply transform if provided
        if self._transform is not None:
            items = [self._transform(item) for item in items]

        # Determine if more pages exist
        has_more = len(items) >= self._limit

        # Compute next_offset for offset-style pagination
        if self._pagination_style == "page":
            next_offset = None  # Page-style doesn't use offset
        else:
            offset = self._params.get("offset", 0) or 0
            next_offset = offset + len(items) if has_more else None

        return PageResult(
            data=items,
            has_more=has_more,
            total=None,  # Not available from simple GET
            next_offset=next_offset,
        )

    def reset(self) -> None:
        """Reset the paginator to start from the beginning."""
        self._offset = 0
        self._total_fetched = 0
        self._exhausted = False
        self._buffer = []
        self._buffer_index = 0


__all__ = [
    "DEFAULT_LIMIT",
    "DEFAULT_MAX_ITEMS",
    "PageResult",
    "PaginationStyle",
    "Paginator",
    "TransportProtocol",
]

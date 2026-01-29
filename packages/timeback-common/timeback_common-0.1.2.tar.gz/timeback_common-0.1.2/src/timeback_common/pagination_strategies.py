"""
Pagination Strategy Helpers

It provides small, focused helpers for parsing pagination metadata from:
- HTTP headers (Link, X-Total-Count)
- Response bodies (totalCount, pageCount, pageNumber)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from httpx import Headers


def parse_header_has_more(headers: Headers) -> bool:
    """Return True if Link header contains rel=next."""
    link = headers.get("link", "")
    if not link:
        return False
    return bool(re.search(r'rel=["\']?next["\']?(?:\s|;|,|$)', link, re.IGNORECASE))


def parse_header_total(headers: Headers) -> int | None:
    """Parse X-Total-Count header as integer if present."""
    total = headers.get("x-total-count")
    if not total:
        return None
    try:
        return int(total)
    except ValueError:
        return None


def parse_body_pagination(body: dict[str, Any], data_key: str) -> dict[str, Any]:
    """
    Parse body-based pagination returning extracted `data` array.

    Returns dict with keys:
    - data
    - total
    - hasMore
    """
    data = body.get(data_key, [])
    total_count = body.get("totalCount", 0)
    page_count = body.get("pageCount", 0)
    page_number = body.get("pageNumber", 0)

    has_more = page_number < page_count

    return {
        "data": data,
        "total": total_count,
        "hasMore": has_more,
    }


def parse_body_pagination_raw(body: dict[str, Any]) -> dict[str, Any]:
    """
    Parse body pagination returning full body as `data`.

    This is used when a paginator will apply `unwrap_key` itself.
    """
    total_count = body.get("totalCount", 0)
    page_count = body.get("pageCount", 0)
    page_number = body.get("pageNumber", 0)

    has_more = page_number < page_count

    return {
        "data": body,
        "total": total_count,
        "hasMore": has_more,
    }


def parse_offset_pagination(data: list[Any], limit: int) -> dict[str, Any]:
    """
    Parse pagination for APIs without pagination metadata.

    Uses a heuristic: if we received a full page (len(data) >= limit),
    there might be more pages. If fewer items than limit, we've reached the end.

    """
    return {
        "data": data,
        "total": None,
        "hasMore": len(data) >= limit,
    }


__all__ = [
    "parse_body_pagination",
    "parse_body_pagination_raw",
    "parse_header_has_more",
    "parse_header_total",
    "parse_offset_pagination",
]

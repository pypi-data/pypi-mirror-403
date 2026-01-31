"""
Type Normalization Utilities

Helpers for normalizing API response values to consistent Python types.
"""

from __future__ import annotations

import re
from datetime import datetime

from .datetime import ensure_z_suffix

# Regex for date-only format: YYYY-MM-DD
_DATE_ONLY_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalize_boolean(value: bool | str) -> bool:
    """
    Normalize a boolean-like value to a boolean.

    The Beyond-AI API sometimes returns boolean fields as strings (`"true"`/`"false"`).
    This normalizes them to actual booleans for a stable, predictable API.

    Args:
        value: Boolean-like value from the API

    Returns:
        Normalized boolean

    Example:
        >>> normalize_boolean("true")
        True
        >>> normalize_boolean("false")
        False
        >>> normalize_boolean(True)
        True
    """
    if isinstance(value, bool):
        return value
    return value == "true"


def normalize_date(date: str | datetime | None) -> str | None:
    """
    Normalize a date string to full ISO 8601 format.

    Some APIs require full ISO 8601 datetime format (e.g., `2025-12-25T00:00:00.000Z`).
    This function accepts multiple input formats for developer convenience:
    - Date-only: `2025-12-25` → `2025-12-25T00:00:00.000Z`
    - Full ISO: `2025-12-25T10:30:00.000Z` → passed through unchanged
    - Date object: `datetime()` → `.isoformat()` + 'Z'

    Args:
        date: Date string or datetime object

    Returns:
        Full ISO 8601 datetime string, or None if input is None

    Example:
        >>> normalize_date("2025-12-25")
        '2025-12-25T00:00:00.000Z'
        >>> normalize_date("2025-12-25T10:30:00.000Z")
        '2025-12-25T10:30:00.000Z'
        >>> normalize_date(None)
        None
    """
    if date is None:
        return None

    if isinstance(date, datetime):
        # Format datetime to ISO 8601 with milliseconds and Z suffix
        return date.strftime("%Y-%m-%dT%H:%M:%S.") + f"{date.microsecond // 1000:03d}Z"

    # If the date string is already in full ISO 8601 format
    # (i.e., contains a 'T' character), normalize the timezone suffix.
    # Python's isoformat() produces "+00:00" but API expects "Z".
    if "T" in date:
        return ensure_z_suffix(date)

    # Handles date-only format (YYYY-MM-DD) by appending time at midnight UTC.
    # Converts '2025-12-25' → '2025-12-25T00:00:00.000Z'
    if _DATE_ONLY_PATTERN.match(date):
        return f"{date}T00:00:00.000Z"

    # If the date string is not in a valid format, return it as-is;
    # this will be caught by the API validation error.
    return date


def normalize_date_only(date: str) -> str:
    """
    Normalize a date string to `YYYY-MM-DD`.

    Some APIs return ISO timestamps (e.g., `2024-01-01T00:00:00.000Z`)
    for fields that are conceptually dates. This function normalizes these to date-only
    strings for a stable, predictable API.

    Args:
        date: Date string from the API

    Returns:
        Normalized date string in `YYYY-MM-DD` format

    Example:
        >>> normalize_date_only("2024-01-15T00:00:00.000Z")
        '2024-01-15'
        >>> normalize_date_only("2024-01-15")
        '2024-01-15'
    """
    return date[:10]


__all__ = [
    "normalize_boolean",
    "normalize_date",
    "normalize_date_only",
]

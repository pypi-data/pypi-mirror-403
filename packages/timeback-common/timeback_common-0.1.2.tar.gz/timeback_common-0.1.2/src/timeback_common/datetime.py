"""
DateTime Utilities

Shared datetime utilities for Timeback Python clients.
"""

from datetime import UTC, datetime


def utc_iso_timestamp() -> str:
    """
    Return current UTC time in ISO 8601 format with Z suffix.

    Most APIs expect the 'Z' suffix for UTC times, but Python's
    `datetime.isoformat()` produces '+00:00'. This function ensures
    consistent formatting across all SDK packages.

    Returns:
        ISO 8601 timestamp with Z suffix (e.g., "2024-01-15T10:30:00.123456Z")
    """
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def ensure_z_suffix(iso_string: str) -> str:
    """
    Ensure an ISO datetime string uses Z suffix instead of +00:00.

    Args:
        iso_string: ISO 8601 datetime string

    Returns:
        The same string with +00:00 replaced by Z if present
    """
    if iso_string.endswith("+00:00"):
        return iso_string[:-6] + "Z"
    return iso_string

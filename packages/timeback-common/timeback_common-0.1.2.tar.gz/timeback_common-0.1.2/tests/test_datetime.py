"""
Tests for datetime utilities.
"""

import re
from datetime import UTC, datetime

from timeback_common import ensure_z_suffix, utc_iso_timestamp


class TestUtcIsoTimestamp:
    """Tests for utc_iso_timestamp()."""

    def test_returns_string(self):
        """Returns a string."""
        result = utc_iso_timestamp()
        assert isinstance(result, str)

    def test_ends_with_z(self):
        """Timestamp ends with Z suffix, not +00:00."""
        result = utc_iso_timestamp()
        assert result.endswith("Z")
        assert "+00:00" not in result

    def test_valid_iso_format(self):
        """Timestamp is valid ISO 8601 format."""
        result = utc_iso_timestamp()
        # Should match: 2024-01-15T10:30:00.123456Z
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"
        assert re.match(pattern, result), f"'{result}' doesn't match ISO format"

    def test_is_recent(self):
        """Timestamp is close to current time."""
        before = datetime.now(UTC)
        result = utc_iso_timestamp()
        after = datetime.now(UTC)

        # Parse the result (replace Z with +00:00 for fromisoformat)
        parsed = datetime.fromisoformat(result.replace("Z", "+00:00"))

        # Should be between before and after
        assert before <= parsed <= after


class TestEnsureZSuffix:
    """Tests for ensure_z_suffix()."""

    def test_converts_plus_zero_to_z(self):
        """Converts +00:00 suffix to Z."""
        result = ensure_z_suffix("2024-01-15T10:30:00+00:00")
        assert result == "2024-01-15T10:30:00Z"

    def test_converts_with_microseconds(self):
        """Converts +00:00 suffix with microseconds."""
        result = ensure_z_suffix("2024-01-15T10:30:00.123456+00:00")
        assert result == "2024-01-15T10:30:00.123456Z"

    def test_preserves_z_suffix(self):
        """Preserves existing Z suffix."""
        result = ensure_z_suffix("2024-01-15T10:30:00Z")
        assert result == "2024-01-15T10:30:00Z"

    def test_preserves_other_timezones(self):
        """Preserves non-UTC timezone offsets."""
        result = ensure_z_suffix("2024-01-15T10:30:00+05:00")
        assert result == "2024-01-15T10:30:00+05:00"

    def test_preserves_negative_timezone(self):
        """Preserves negative timezone offsets."""
        result = ensure_z_suffix("2024-01-15T10:30:00-08:00")
        assert result == "2024-01-15T10:30:00-08:00"

    def test_preserves_date_only(self):
        """Preserves date-only strings."""
        result = ensure_z_suffix("2024-01-15")
        assert result == "2024-01-15"

    def test_preserves_naive_datetime(self):
        """Preserves naive datetime strings (no timezone)."""
        result = ensure_z_suffix("2024-01-15T10:30:00")
        assert result == "2024-01-15T10:30:00"

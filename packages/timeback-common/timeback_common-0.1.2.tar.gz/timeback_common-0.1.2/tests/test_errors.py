"""
Tests for error classes and formatting.

Covers IMS error parsing and format_api_error.
"""

from __future__ import annotations

from timeback_common import (
    APIError,
    AuthenticationError,
    FormattedError,
    format_api_error,
)


class TestAPIErrorProperties:
    """Tests for APIError IMS parsing properties."""

    def test_minor_codes_extracts_from_ims_response(self):
        """minor_codes extracts codes from IMS Global response format."""
        response = {
            "imsx_CodeMinor": {
                "imsx_codeMinorField": [
                    {
                        "imsx_codeMinorFieldName": "sourcedId",
                        "imsx_codeMinorFieldValue": "unknownobject",
                    }
                ]
            }
        }
        error = APIError("Not Found", 404, response)

        assert len(error.minor_codes) == 1
        assert error.minor_codes[0]["field"] == "sourcedId"
        assert error.minor_codes[0]["value"] == "unknownobject"

    def test_minor_codes_returns_empty_for_non_ims_response(self):
        """minor_codes returns empty list for non-IMS response."""
        error = APIError("Error", 500, {"message": "Internal error"})
        assert error.minor_codes == []

    def test_details_extracts_from_ims_response(self):
        """details extracts from IMS Global response format."""
        response = {"imsx_error_details": [{"field": "email", "reason": "invalid format"}]}
        error = APIError("Validation Error", 422, response)

        assert len(error.details) == 1
        assert error.details[0]["field"] == "email"

    def test_authentication_error_has_correct_status(self):
        """AuthenticationError has status code 401."""
        error = AuthenticationError("Invalid credentials")
        assert error.status_code == 401
        assert str(error) == "[401] Invalid credentials"


class TestFormatApiError:
    """Tests for format_api_error helper."""

    def test_formats_simple_error(self):
        """format_api_error uses message as header (no status code)."""
        error = APIError("Not Found", 404)
        formatted = format_api_error(error)

        assert isinstance(formatted, FormattedError)
        # Header is just the message, not including status code
        assert formatted.header == "Not Found"
        assert formatted.details == []

    def test_formats_error_with_path_and_message_details(self):
        """format_api_error combines path + message from details."""
        response = {"imsx_error_details": [{"path": "sourcedId", "message": "Required"}]}
        error = APIError("Validation Error", 422, response)
        formatted = format_api_error(error)

        # Details are "path: message" format
        assert formatted.details == ["sourcedId: Required"]

    def test_formats_error_with_field_and_reason_details(self):
        """format_api_error handles field/reason fallback."""
        response = {"imsx_error_details": [{"field": "email", "reason": "invalid format"}]}
        error = APIError("Validation Error", 422, response)
        formatted = format_api_error(error)

        # Falls back to field/reason if path/message not present
        assert formatted.details == ["email: invalid format"]

    def test_formats_error_with_message_only_detail(self):
        """format_api_error handles detail with only message."""
        response = {"imsx_error_details": [{"message": "Something went wrong"}]}
        error = APIError("Error", 500, response)
        formatted = format_api_error(error)

        # If only message, just include the message
        assert formatted.details == ["Something went wrong"]

    def test_does_not_include_minor_codes(self):
        """format_api_error does not include minor codes."""
        response = {
            "imsx_CodeMinor": {
                "imsx_codeMinorField": [
                    {
                        "imsx_codeMinorFieldName": "sourcedId",
                        "imsx_codeMinorFieldValue": "unknownobject",
                    }
                ]
            }
        }
        error = APIError("Not Found", 404, response)
        formatted = format_api_error(error)

        # Minor codes are NOT included in formatted output
        assert formatted.details == []

    def test_formatted_error_repr(self):
        """FormattedError has readable repr."""
        formatted = FormattedError(header="Not Found", details=["sourcedId: Required"])
        repr_str = repr(formatted)

        assert "FormattedError" in repr_str
        assert "Not Found" in repr_str

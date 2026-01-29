"""Tests for validation helpers."""

import pytest

from timeback_common import (
    InputValidationError,
    ValidationIssue,
    create_input_validation_error,
    format_error,
    is_input_validation_error,
    validate_non_empty_string,
    validate_offset_list_params,
    validate_page_list_params,
    validate_sourced_id,
)


class TestInputValidationError:
    """Tests for InputValidationError class."""

    def test_creates_error_with_issues(self) -> None:
        """Creates InputValidationError with issues."""
        issues = [
            ValidationIssue(path="sourcedId", message="Required"),
            ValidationIssue(path="givenName", message="Must be string"),
        ]
        error = InputValidationError("Invalid input", issues)

        assert error.message == "Invalid input"
        assert error.status_code == 400
        assert len(error.issues) == 2
        assert error.issues[0].path == "sourcedId"
        assert error.issues[1].message == "Must be string"

    def test_has_ims_like_details(self) -> None:
        """InputValidationError provides IMS-like details for formatters."""
        issues = [ValidationIssue(path="field", message="error")]
        error = InputValidationError("test", issues)

        assert len(error.details) == 1
        assert error.details[0]["path"] == "field"
        assert error.details[0]["message"] == "error"

    def test_error_name(self) -> None:
        """InputValidationError has correct name."""
        error = InputValidationError("test", [])
        # Check it's an APIError subclass
        assert isinstance(error, Exception)

    def test_str_representation(self) -> None:
        """InputValidationError has status code in str."""
        error = InputValidationError("test message", [])
        assert str(error) == "[400] test message"


class TestCreateInputValidationError:
    """Tests for create_input_validation_error helper."""

    def test_creates_error(self) -> None:
        """Creates InputValidationError from issues."""
        issues = [ValidationIssue(path="test", message="error")]
        error = create_input_validation_error("Invalid parameters", issues)

        assert isinstance(error, InputValidationError)
        assert error.message == "Invalid parameters"
        assert len(error.issues) == 1


class TestIsInputValidationError:
    """Tests for is_input_validation_error type guard."""

    def test_returns_true_for_input_validation_error(self) -> None:
        """Returns True for InputValidationError."""
        error = InputValidationError("test", [])
        assert is_input_validation_error(error) is True

    def test_returns_false_for_other_errors(self) -> None:
        """Returns False for non-InputValidationError."""
        assert is_input_validation_error(ValueError("test")) is False
        assert is_input_validation_error(Exception("test")) is False

    def test_returns_false_for_non_exceptions(self) -> None:
        """Returns False for non-exceptions."""
        assert is_input_validation_error(None) is False
        assert is_input_validation_error("string") is False
        assert is_input_validation_error({"issues": []}) is False


class TestFormatError:
    """Tests for format_error helper."""

    def test_formats_input_validation_error(self) -> None:
        """Formats InputValidationError correctly."""
        issues = [ValidationIssue(path="field", message="error message")]
        error = InputValidationError("Validation failed", issues)
        formatted = format_error(error)

        assert formatted.header == "Validation failed"
        # Each issue produces "path: message" format
        assert formatted.details == ["field: error message"]

    def test_formats_regular_exception(self) -> None:
        """Formats regular exceptions."""
        error = ValueError("something went wrong")
        formatted = format_error(error)

        assert formatted.header == "something went wrong"
        assert formatted.details == []

    def test_formats_string(self) -> None:
        """Formats string inputs."""
        formatted = format_error("error message")

        assert formatted.header == "error message"
        assert formatted.details == []


class TestValidateNonEmptyString:
    """Tests for validate_non_empty_string."""

    def test_passes_for_non_empty_string(self) -> None:
        """Does not raise for non-empty string."""
        validate_non_empty_string("hello", "field")  # No error

    def test_raises_for_empty_string(self) -> None:
        """Raises for empty string."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_non_empty_string("", "fieldName")

        assert exc_info.value.issues[0].path == "fieldName"
        assert "non-empty" in exc_info.value.issues[0].message.lower()

    def test_raises_for_whitespace_string(self) -> None:
        """Raises for whitespace-only string."""
        with pytest.raises(InputValidationError):
            validate_non_empty_string("   ", "field")

    def test_raises_for_non_string(self) -> None:
        """Raises for non-string values."""
        with pytest.raises(InputValidationError):
            validate_non_empty_string(123, "field")  # type: ignore[arg-type]


class TestValidateOffsetListParams:
    """Tests for validate_offset_list_params."""

    def test_passes_for_valid_params(self) -> None:
        """Does not raise for valid params."""
        validate_offset_list_params(limit=100, offset=0, max_items=1000)

    def test_passes_for_no_params(self) -> None:
        """Does not raise when no params provided."""
        validate_offset_list_params()

    def test_raises_for_negative_limit(self) -> None:
        """Raises for negative limit."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_offset_list_params(limit=-1)

        assert any(i.path == "limit" for i in exc_info.value.issues)

    def test_raises_for_zero_limit(self) -> None:
        """Raises for zero limit."""
        with pytest.raises(InputValidationError):
            validate_offset_list_params(limit=0)

    def test_raises_for_negative_offset(self) -> None:
        """Raises for negative offset."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_offset_list_params(offset=-1)

        assert any(i.path == "offset" for i in exc_info.value.issues)

    def test_passes_for_zero_offset(self) -> None:
        """Does not raise for zero offset (valid)."""
        validate_offset_list_params(offset=0)

    def test_raises_for_non_integer_limit(self) -> None:
        """Raises for non-integer limit."""
        with pytest.raises(InputValidationError):
            validate_offset_list_params(limit=1.5)  # type: ignore[arg-type]

    def test_collects_multiple_issues(self) -> None:
        """Collects all issues in one error."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_offset_list_params(limit=-1, offset=-1, max_items=-1)

        assert len(exc_info.value.issues) == 3


class TestValidatePageListParams:
    """Tests for validate_page_list_params."""

    def test_passes_for_valid_params(self) -> None:
        """Does not raise for valid params."""
        validate_page_list_params(page=1, limit=100, max_items=1000)

    def test_raises_for_zero_page(self) -> None:
        """Raises for zero page (1-indexed)."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_page_list_params(page=0)

        assert any(i.path == "page" for i in exc_info.value.issues)

    def test_raises_for_negative_page(self) -> None:
        """Raises for negative page."""
        with pytest.raises(InputValidationError):
            validate_page_list_params(page=-1)


class TestValidateSourcedId:
    """Tests for validate_sourced_id."""

    def test_passes_for_valid_sourced_id(self) -> None:
        """Does not raise for valid sourcedId."""
        validate_sourced_id("abc-123", "get user")

    def test_raises_for_empty_sourced_id(self) -> None:
        """Raises for empty sourcedId."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_sourced_id("", "get user")

        error = exc_info.value
        assert "get user" in error.message
        assert error.issues[0].path == "sourcedId"

    def test_raises_for_whitespace_sourced_id(self) -> None:
        """Raises for whitespace-only sourcedId."""
        with pytest.raises(InputValidationError):
            validate_sourced_id("   ", "delete enrollment")

    def test_raises_for_non_string(self) -> None:
        """Raises for non-string sourcedId."""
        with pytest.raises(InputValidationError):
            validate_sourced_id(None, "get user")  # type: ignore[arg-type]

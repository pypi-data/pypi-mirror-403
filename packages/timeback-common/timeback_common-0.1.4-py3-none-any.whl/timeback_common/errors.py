"""
API Error Classes

Base error classes for HTTP API failures.
Includes IMS Global error response parsing (OneRoster, QTI, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION ISSUE
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ValidationIssue:
    """
    A single validation issue with a field path and message.
    """

    path: str
    """Field path (e.g., 'sourcedId', 'givenName')."""

    message: str
    """Human-readable error message."""


# ═══════════════════════════════════════════════════════════════════════════════
# BASE ERRORS
# ═══════════════════════════════════════════════════════════════════════════════


class TimebackError(Exception):
    """Base exception for all Timeback errors."""

    pass


class APIError(TimebackError):
    """
    Base error class for all API errors.

    Provides access to the HTTP status code and raw response body.
    Includes IMS Global error parsing (minor_codes, details) for
    IMS-standard APIs like OneRoster and QTI.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: Any | None = None,
    ) -> None:
        """
        Creates a new APIError.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            response: Raw response body (if available)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message

    @property
    def minor_codes(self) -> list[dict[str, str]]:
        """
        Minor error codes from IMS Global error response.

        For IMS-standard APIs (OneRoster, QTI), provides specific error codes
        like "unknownobject" or "invaliddata".

        Returns:
            List of field/value dicts, or empty list if not IMS format
        """
        if not isinstance(self.response, dict):
            return []

        code_minor = self.response.get("imsx_CodeMinor", {})
        fields = code_minor.get("imsx_codeMinorField", [])

        return [
            {
                "field": f.get("imsx_codeMinorFieldName", ""),
                "value": f.get("imsx_codeMinorFieldValue", ""),
            }
            for f in fields
            if isinstance(f, dict)
        ]

    @property
    def details(self) -> list[dict[str, str]]:
        """
        Additional error details from IMS Global response.

        Returns:
            List of key-value dicts, or empty list if not present
        """
        if not isinstance(self.response, dict):
            return []
        return self.response.get("imsx_error_details", [])


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP ERRORS
# ═══════════════════════════════════════════════════════════════════════════════


class AuthenticationError(APIError):
    """
    Error thrown when authentication fails (HTTP 401).

    Typically indicates invalid or expired credentials.
    """

    def __init__(self, message: str = "Unauthorized", response: Any | None = None) -> None:
        super().__init__(message, 401, response)


class ForbiddenError(APIError):
    """
    Error thrown when the client lacks permission for the operation (HTTP 403).

    The credentials are valid, but the client is not authorized for this action.
    """

    def __init__(self, message: str = "Forbidden", response: Any | None = None) -> None:
        super().__init__(message, 403, response)


class NotFoundError(APIError):
    """
    Error thrown when a requested resource is not found (HTTP 404).
    """

    def __init__(self, message: str = "Not Found", response: Any | None = None) -> None:
        super().__init__(message, 404, response)


class ValidationError(APIError):
    """
    Error thrown when request data is invalid (HTTP 422).

    Check the `details` property for field-level validation errors.
    """

    def __init__(self, message: str = "Validation Error", response: Any | None = None) -> None:
        super().__init__(message, 422, response)


class RateLimitError(APIError):
    """
    Rate limit exceeded (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying (if provided by API)
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        response: Any | None = None,
        *,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message, 429, response)
        self.retry_after = retry_after


class ServerError(APIError):
    """
    Server error (HTTP 5xx).

    The API encountered an internal error.
    """

    def __init__(
        self,
        message: str = "Server error",
        status_code: int = 500,
        response: Any | None = None,
    ) -> None:
        super().__init__(message, status_code, response)


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT-SIDE VALIDATION ERROR
# ═══════════════════════════════════════════════════════════════════════════════


class InputValidationError(APIError):
    """
    Error thrown when client-side input validation fails.

    This is thrown **before** making a network request, providing fast feedback
    with actionable, path-based error messages.

    Uses status_code 400 (Bad Request) to distinguish from server-side 422 errors.
    Formats like IMS errors via `imsx_error_details` so existing error formatters work.

    Example:
        ```python
        try:
            await client.users.create({})  # missing required fields
        except InputValidationError as e:
            print("Invalid input:", e.issues)
            # [ValidationIssue(path='sourcedId', message='Required')]
        ```
    """

    def __init__(self, message: str, issues: list[ValidationIssue]) -> None:
        """
        Creates a new InputValidationError.

        Args:
            message: Overall error message
            issues: List of validation issues with path and message
        """
        # Build IMS-like response so APIError.details works
        response = {
            "imsx_codeMajor": "failure",
            "imsx_severity": "error",
            "imsx_description": message,
            "imsx_error_details": [
                {"path": issue.path, "message": issue.message} for issue in issues
            ],
        }
        super().__init__(message, 400, response)
        self.issues = issues


def create_input_validation_error(
    message: str, issues: list[ValidationIssue]
) -> InputValidationError:
    """
    Create an InputValidationError from validation issues.

    Args:
        message: Overall error message
        issues: Array of validation issues with path and message

    Returns:
        InputValidationError ready to raise

    Example:
        ```python
        raise create_input_validation_error("Invalid input", [
            ValidationIssue(path="sourcedId", message="sourcedId is required"),
            ValidationIssue(path="givenName", message="givenName must be a string"),
        ])
        ```
    """
    return InputValidationError(message, issues)


def is_input_validation_error(error: object) -> bool:
    """
    Type guard to check if an error is an InputValidationError.

    Uses duck typing to work across module boundaries where `isinstance`
    may fail due to multiple package copies.

    Args:
        error: The error to check

    Returns:
        True if error looks like an InputValidationError (has issues attribute)
    """
    if not isinstance(error, Exception):
        return False
    # Duck typing: InputValidationError has name='InputValidationError' and 'issues' attribute
    return getattr(error, "__class__", type(error)).__name__ == "InputValidationError" and hasattr(
        error, "issues"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE GUARDS
# ═══════════════════════════════════════════════════════════════════════════════


def is_api_error(error: object) -> bool:
    """
    Type guard to check if an error is an APIError.

    Uses duck typing to work across module boundaries where `isinstance`
    may fail due to multiple package copies.

    Args:
        error: The error to check

    Returns:
        True if error looks like an APIError (has status_code and response attributes)
    """
    if not isinstance(error, Exception):
        return False
    return hasattr(error, "status_code") and hasattr(error, "response")


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR FORMATTING
# ═══════════════════════════════════════════════════════════════════════════════


class FormattedError:
    """
    Formatted error with header and details.

    Attributes:
        header: Main error message with status code
        details: List of specific error details
    """

    def __init__(self, header: str, details: list[str]) -> None:
        self.header = header
        self.details = details

    def __repr__(self) -> str:
        return f"FormattedError(header={self.header!r}, details={self.details!r})"


def format_api_error(error: APIError) -> FormattedError:
    """
    Format an APIError for display.

    Extracts IMS Global error details into a structured format
    suitable for logging or user display.

    Args:
        error: The API error to format

    Returns:
        FormattedError with header and details list

    Example:
        ```python
        try:
            await client.users.get("nonexistent")
        except APIError as e:
            formatted = format_api_error(e)
            print(formatted.header)  # "Not Found"
            for detail in formatted.details:
                print(f"  - {detail}")  # "sourcedId: Required"
        ```
    """
    # Header is just the message, not including status code
    header = error.message
    details: list[str] = []

    # Extract path/field + message/reason from each detail
    for detail in error.details:
        if isinstance(detail, dict):
            # TS: detail.path ?? detail.field
            path = detail.get("path") or detail.get("field") or ""
            # TS: detail.message ?? detail.reason
            message = detail.get("message") or detail.get("reason") or ""

            if path and message:
                details.append(f"{path}: {message}")
            elif message:
                details.append(message)
        elif isinstance(detail, str):
            details.append(detail)

    return FormattedError(header=header, details=details)


def format_error(error: object) -> FormattedError:
    """
    Format any error for display.

    Safely handles both APIError and non-APIError inputs.
    Returns an object with header and detail lines for flexible rendering.

    Args:
        error: The error to format (any type)

    Returns:
        FormattedError with header and details list

    Example:
        ```python
        try:
            await some_operation()
        except Exception as e:
            formatted = format_error(e)
            print(formatted.header)
            for detail in formatted.details:
                print(f"  - {detail}")
        ```
    """
    if is_api_error(error):  # type: ignore[arg-type]
        return format_api_error(error)  # type: ignore[arg-type]

    # Handle non-APIError inputs
    if isinstance(error, Exception):
        return FormattedError(header=str(error), details=[])

    return FormattedError(header=str(error), details=[])


__all__ = [
    "APIError",
    "AuthenticationError",
    "ForbiddenError",
    "FormattedError",
    "InputValidationError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TimebackError",
    "ValidationError",
    "ValidationIssue",
    "create_input_validation_error",
    "format_api_error",
    "format_error",
    "is_api_error",
    "is_input_validation_error",
]

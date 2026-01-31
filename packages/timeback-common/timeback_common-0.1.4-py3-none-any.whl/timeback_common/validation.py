"""
Shared runtime validation helpers for client SDKs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .errors import ValidationIssue, create_input_validation_error

if TYPE_CHECKING:
    from pydantic import BaseModel

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def _issue(path: str, message: str) -> ValidationIssue:
    """Create a ValidationIssue for consistent error formatting."""
    return ValidationIssue(path=path, message=message)


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


def validate_with_schema(
    model: type[BaseModel],
    data: Any,
    context: str,
) -> None:
    """
    Validate data with a Pydantic model and throw InputValidationError on failure.

    Args:
        model: Pydantic model class to validate against
        data: Input data to validate (dict or model instance)
        context: Context label used in the error message

    Raises:
        InputValidationError: If validation fails

    Example:
        ```python
        from pydantic import BaseModel

        class UserInput(BaseModel):
            name: str
            email: str

        validate_with_schema(UserInput, {"name": "", "email": "invalid"}, "user")
        # Raises InputValidationError with structured issues
        ```
    """
    from pydantic import ValidationError

    try:
        if isinstance(data, model):
            # Already a model instance, re-validate
            model.model_validate(data.model_dump())
        elif isinstance(data, dict):
            model.model_validate(data)
        else:
            raise create_input_validation_error(
                f"Invalid {context} data",
                [_issue("(root)", f"Expected dict or {model.__name__}, got {type(data).__name__}")],
            )
    except ValidationError as e:
        issues = [
            _issue(
                ".".join(str(loc) for loc in err["loc"]) or "(root)",
                err["msg"],
            )
            for err in e.errors()
        ]
        raise create_input_validation_error(f"Invalid {context} data", issues) from None


# ═══════════════════════════════════════════════════════════════════════════════
# STRING VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


def validate_non_empty_string(value: str, name: str) -> None:
    """
    Validate that a string value is non-empty.

    Args:
        value: String value to validate
        name: Name of the field (used for error path/message)

    Raises:
        InputValidationError: If value is empty or not a string
    """
    if not isinstance(value, str) or value.strip() == "":
        raise create_input_validation_error(
            f"Invalid {name}",
            [_issue(name, "Must be a non-empty string")],
        )


# ═══════════════════════════════════════════════════════════════════════════════
# LIST PARAMS VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


def validate_offset_list_params(
    *,
    limit: int | None = None,
    offset: int | None = None,
    max_items: int | None = None,
) -> None:
    """
    Validate list params for offset-based pagination (offset/limit/max).

    Args:
        limit: Maximum items per page (must be positive integer)
        offset: Number of items to skip (must be non-negative integer)
        max_items: Maximum total items to fetch (must be positive integer)

    Raises:
        InputValidationError: If any parameter is invalid
    """
    issues: list[ValidationIssue] = []

    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        issues.append(_issue("limit", "Must be a positive integer"))

    if offset is not None and (not isinstance(offset, int) or offset < 0):
        issues.append(_issue("offset", "Must be a non-negative integer"))

    if max_items is not None and (not isinstance(max_items, int) or max_items <= 0):
        issues.append(_issue("max", "Must be a positive integer"))

    if issues:
        raise create_input_validation_error("Invalid list parameters", issues)


def validate_page_list_params(
    *,
    page: int | None = None,
    limit: int | None = None,
    max_items: int | None = None,
) -> None:
    """
    Validate list params for page-based pagination (page/limit/max).

    Args:
        page: Page number (must be positive integer, 1-indexed)
        limit: Maximum items per page (must be positive integer)
        max_items: Maximum total items to fetch (must be positive integer)

    Raises:
        InputValidationError: If any parameter is invalid
    """
    issues: list[ValidationIssue] = []

    if page is not None and (not isinstance(page, int) or page <= 0):
        issues.append(_issue("page", "Must be a positive integer"))

    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        issues.append(_issue("limit", "Must be a positive integer"))

    if max_items is not None and (not isinstance(max_items, int) or max_items <= 0):
        issues.append(_issue("max", "Must be a positive integer"))

    if issues:
        raise create_input_validation_error("Invalid list parameters", issues)


# ═══════════════════════════════════════════════════════════════════════════════
# SOURCED ID VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


def validate_sourced_id(sourced_id: str, context: str) -> None:
    """
    Validate a sourcedId before using it in a URL path.

    Rejects empty strings to avoid malformed URLs and unnecessary server round-trips.

    Args:
        sourced_id: The sourcedId to validate
        context: Context for error message (e.g., "get user", "delete enrollment")

    Raises:
        InputValidationError: If sourcedId is empty or not a string
    """
    if not isinstance(sourced_id, str) or sourced_id.strip() == "":
        raise create_input_validation_error(
            f"Invalid {context} request",
            [_issue("sourcedId", "Must be a non-empty string")],
        )


# ═══════════════════════════════════════════════════════════════════════════════
# FIELDS VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


def validate_fields(fields: list[str] | None) -> None:
    """
    Validate the fields parameter for list operations.

    Args:
        fields: List of field names to include in the response

    Raises:
        InputValidationError: If any field name is empty
    """
    if fields is None:
        return

    issues: list[ValidationIssue] = []

    if not isinstance(fields, list):
        issues.append(_issue("fields", "Must be a list of strings"))
    else:
        for i, field in enumerate(fields):
            if not isinstance(field, str) or field.strip() == "":
                issues.append(_issue(f"fields[{i}]", "Must be a non-empty string"))

    if issues:
        raise create_input_validation_error("Invalid list parameters", issues)


__all__ = [
    "validate_fields",
    "validate_non_empty_string",
    "validate_offset_list_params",
    "validate_page_list_params",
    "validate_sourced_id",
    "validate_with_schema",
]

"""
Where Clause Filter Support

Type-safe object syntax for building filter expressions.

Example:
    ```python
    from timeback_common import where_to_filter

    # Simple equality
    where_to_filter({"status": "active"})
    # → "status='active'"

    # Multiple fields (AND)
    where_to_filter({"status": "active", "role": "teacher"})
    # → "status='active' AND role='teacher'"

    # With operators
    where_to_filter({"score": {"gte": 90}})
    # → "score>=90"

    # OR condition
    where_to_filter({"role": {"in_": ["teacher", "aide"]}})
    # → "(role='teacher' OR role='aide')"
    ```
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, TypedDict

# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

# Primitive value types that can be used in filters
FilterValue = str | int | float | bool | datetime | date


class FieldOperators(TypedDict, total=False):
    """
    Operators for a single field.

    Example:
        ```python
        {"status": {"ne": "deleted"}}
        {"score": {"gte": 90, "lte": 100}}
        {"email": {"contains": "@school.edu"}}
        {"role": {"in_": ["teacher", "aide"]}}
        ```
    """

    ne: FilterValue
    """Not equal."""

    gt: FilterValue
    """Greater than."""

    gte: FilterValue
    """Greater than or equal."""

    lt: FilterValue
    """Less than."""

    lte: FilterValue
    """Less than or equal."""

    contains: str
    """Contains substring (strings only)."""

    in_: list[FilterValue]
    """Match any of the values. Named `in_` to avoid Python keyword."""

    not_in: list[FilterValue]
    """Match none of the values."""


# Field condition: direct value (equality) or operator object
FieldCondition = FilterValue | FieldOperators

# Where clause: dict of field conditions, or OR condition
WhereClause = dict[str, FieldCondition | Any]
"""
Type-safe where clause for filtering.

Multiple fields are combined with AND. Use 'OR' key for OR logic.

Examples:
    ```python
    # Simple equality
    {"status": "active"}

    # Multiple fields (AND)
    {"status": "active", "role": "teacher"}

    # With operators
    {"score": {"gte": 90}}

    # OR condition
    {"OR": [{"role": "teacher"}, {"role": "aide"}]}

    # in operator (any of values)
    {"role": {"in_": ["teacher", "aide"]}}
    ```
"""


# ═══════════════════════════════════════════════════════════════════════════════
# VALUE FORMATTING
# ═══════════════════════════════════════════════════════════════════════════════


def _escape_value(value: FilterValue) -> str:
    """
    Escape a primitive value for safe inclusion in a filter expression.

    - datetime/date → ISO 8601 string
    - bool → 'true' | 'false'
    - numbers → string representation
    - strings → single quotes escaped by doubling (O'Brien → O''Brien)
    """
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    # String - escape single quotes
    return str(value).replace("'", "''")


def _format_value(value: FilterValue) -> str:
    """
    Format a value for the filter string with appropriate quoting.

    - Strings and dates are wrapped in single quotes
    - Numbers and booleans are unquoted
    """
    escaped = _escape_value(value)
    needs_quotes = isinstance(value, str | datetime | date)
    return f"'{escaped}'" if needs_quotes else escaped


# ═══════════════════════════════════════════════════════════════════════════════
# CONDITION CONVERSION
# ═══════════════════════════════════════════════════════════════════════════════


def _is_primitive(value: Any) -> bool:
    """Check if value is a primitive filter value."""
    return isinstance(value, str | int | float | bool | datetime | date)


def _field_to_conditions(field: str, condition: Any) -> list[str]:
    """
    Convert a single field's condition(s) to filter expression strings.

    Handles both direct values (equality) and operator objects.
    """
    # Direct value - equality
    if _is_primitive(condition):
        return [f"{field}={_format_value(condition)}"]

    # Object with operators
    if isinstance(condition, dict):
        conditions: list[str] = []

        if "ne" in condition:
            conditions.append(f"{field}!={_format_value(condition['ne'])}")
        if "gt" in condition:
            conditions.append(f"{field}>{_format_value(condition['gt'])}")
        if "gte" in condition:
            conditions.append(f"{field}>={_format_value(condition['gte'])}")
        if "lt" in condition:
            conditions.append(f"{field}<{_format_value(condition['lt'])}")
        if "lte" in condition:
            conditions.append(f"{field}<={_format_value(condition['lte'])}")
        if "contains" in condition:
            conditions.append(f"{field}~{_format_value(condition['contains'])}")

        # Handle 'in' operator (Python keyword, so we accept both 'in' and 'in_')
        in_values = condition.get("in_") or condition.get("in")
        if in_values and len(in_values) > 0:
            in_conditions = [f"{field}={_format_value(v)}" for v in in_values]
            joined = " OR ".join(in_conditions)
            conditions.append(f"({joined})" if len(in_conditions) > 1 else joined)

        # Handle 'notIn' / 'not_in'
        not_in_values = condition.get("not_in") or condition.get("notIn")
        if not_in_values and len(not_in_values) > 0:
            not_in_conditions = [f"{field}!={_format_value(v)}" for v in not_in_values]
            conditions.append(" AND ".join(not_in_conditions))

        return conditions

    return []


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONVERSION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════


def where_to_filter(where: WhereClause) -> str | None:
    """
    Convert a type-safe where clause to a filter string.

    Args:
        where: The where clause object

    Returns:
        The filter string, or None if the clause is empty

    Example:
        ```python
        # Simple equality
        where_to_filter({"status": "active"})
        # → "status='active'"

        # Multiple fields (implicit AND)
        where_to_filter({"status": "active", "role": "teacher"})
        # → "status='active' AND role='teacher'"

        # Comparison operators
        where_to_filter({"score": {"gte": 90, "lte": 100}})
        # → "score>=90 AND score<=100"

        # Not equal
        where_to_filter({"status": {"ne": "deleted"}})
        # → "status!='deleted'"

        # Contains (substring match)
        where_to_filter({"email": {"contains": "@school.edu"}})
        # → "email~'@school.edu'"

        # Match any value
        where_to_filter({"role": {"in_": ["teacher", "aide"]}})
        # → "(role='teacher' OR role='aide')"

        # Explicit OR across fields
        where_to_filter({"OR": [{"role": "teacher"}, {"status": "active"}]})
        # → "role='teacher' OR status='active'"
        ```
    """
    # Handle OR condition
    if "OR" in where and isinstance(where["OR"], list):
        or_clauses = where["OR"]
        or_parts = [where_to_filter(clause) for clause in or_clauses]
        or_parts = [p for p in or_parts if p is not None]
        return " OR ".join(or_parts) if or_parts else None

    # Regular field conditions - combined with AND
    conditions: list[str] = []

    for field, condition in where.items():
        if condition is not None:
            conditions.extend(_field_to_conditions(field, condition))

    return " AND ".join(conditions) if conditions else None


__all__ = [
    "FieldCondition",
    "FieldOperators",
    "FilterValue",
    "WhereClause",
    "where_to_filter",
]

"""
Timeback Common

Shared infrastructure for Timeback Python clients.

Provides:
- Base transport with OAuth2 client credentials flow
- Shared error classes
- Pagination support
- Where clause filtering
- Platform configuration (endpoints and paths)
- TimebackProvider for unified connection management
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("timeback-common")
except PackageNotFoundError:
    __version__ = "0.0.0"

from .config import (
    BEYONDAI_API_URLS,
    BEYONDAI_CALIPER_PATHS,
    BEYONDAI_ONEROSTER_PATHS,
    BEYONDAI_TOKEN_URLS,
    DEFAULT_PLATFORM,
    PLATFORM_CALIPER_PATHS,
    PLATFORM_ENDPOINTS,
    CaliperPaths,
    EdubridgePaths,
    Environment,
    OneRosterPaths,
    Platform,
    PlatformPaths,
)
from .create_response import BulkCreateResponse, CreateResponse, SourcedIdPair
from .datetime import ensure_z_suffix, utc_iso_timestamp
from .errors import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    FormattedError,
    InputValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimebackError,
    ValidationError,
    ValidationIssue,
    create_input_validation_error,
    format_api_error,
    format_error,
    is_api_error,
    is_input_validation_error,
)
from .filter import (
    FieldCondition,
    FieldOperators,
    FilterValue,
    WhereClause,
    where_to_filter,
)
from .normalization import normalize_boolean, normalize_date, normalize_date_only
from .pagination import (
    DEFAULT_LIMIT,
    DEFAULT_MAX_ITEMS,
    PageResult,
    PaginationStyle,
    Paginator,
    TransportProtocol,
)
from .pagination_strategies import (
    parse_body_pagination,
    parse_body_pagination_raw,
    parse_header_has_more,
    parse_header_total,
    parse_offset_pagination,
)
from .provider import (
    AuthCheckChecks,
    AuthCheckResult,
    CustomPaths,
    PathProfileName,
    ResolvedEndpoint,
    ServiceName,
    TimebackProvider,
)
from .resolve import (
    EnvVarNames,
    ResolvedProvider,
    ResolvedTransport,
    ResolverConfig,
    ResolveResult,
    build_provider_env,
    build_provider_explicit,
    resolve_to_provider,
)
from .token_manager import TokenManager, TokenManagerConfig
from .transport import BaseTransport
from .validation import (
    validate_fields,
    validate_non_empty_string,
    validate_offset_list_params,
    validate_page_list_params,
    validate_sourced_id,
    validate_with_schema,
)

__all__ = [
    "BEYONDAI_API_URLS",
    "BEYONDAI_CALIPER_PATHS",
    "BEYONDAI_ONEROSTER_PATHS",
    "BEYONDAI_TOKEN_URLS",
    "DEFAULT_LIMIT",
    "DEFAULT_MAX_ITEMS",
    "DEFAULT_PLATFORM",
    "PLATFORM_CALIPER_PATHS",
    "PLATFORM_ENDPOINTS",
    "APIError",
    "AuthCheckChecks",
    "AuthCheckResult",
    "AuthenticationError",
    "BaseTransport",
    "BulkCreateResponse",
    "CaliperPaths",
    "CreateResponse",
    "CustomPaths",
    "EdubridgePaths",
    "EnvVarNames",
    "Environment",
    "FieldCondition",
    "FieldOperators",
    "FilterValue",
    "ForbiddenError",
    "FormattedError",
    "InputValidationError",
    "NotFoundError",
    "OneRosterPaths",
    "PageResult",
    "PaginationStyle",
    "Paginator",
    "PathProfileName",
    "Platform",
    "PlatformPaths",
    "RateLimitError",
    "ResolveResult",
    "ResolvedEndpoint",
    "ResolvedProvider",
    "ResolvedTransport",
    "ResolverConfig",
    "ServerError",
    "ServiceName",
    "SourcedIdPair",
    "TimebackError",
    "TimebackProvider",
    "TokenManager",
    "TokenManagerConfig",
    "TransportProtocol",
    "ValidationError",
    "ValidationIssue",
    "WhereClause",
    "__version__",
    "build_provider_env",
    "build_provider_explicit",
    "create_input_validation_error",
    "ensure_z_suffix",
    "format_api_error",
    "format_error",
    "is_api_error",
    "is_input_validation_error",
    "normalize_boolean",
    "normalize_date",
    "normalize_date_only",
    "parse_body_pagination",
    "parse_body_pagination_raw",
    "parse_header_has_more",
    "parse_header_total",
    "parse_offset_pagination",
    "resolve_to_provider",
    "utc_iso_timestamp",
    "validate_fields",
    "validate_non_empty_string",
    "validate_offset_list_params",
    "validate_page_list_params",
    "validate_sourced_id",
    "validate_with_schema",
    "where_to_filter",
]

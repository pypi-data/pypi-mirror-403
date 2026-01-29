# timeback-common

Shared infrastructure for Timeback Python clients.

## Installation

```bash
# pip
pip install timeback-common

# uv (add to a project)
uv add timeback-common

# uv (install into current environment)
uv pip install timeback-common
```

```python
from timeback_common import BaseTransport, APIError, Paginator, where_to_filter

class MyTransport(BaseTransport):
    ENV_VAR_BASE_URL = "MY_SERVICE_BASE_URL"
    ENV_VAR_AUTH_URL = "MY_SERVICE_TOKEN_URL"
    ENV_VAR_CLIENT_ID = "MY_SERVICE_CLIENT_ID"
    ENV_VAR_CLIENT_SECRET = "MY_SERVICE_CLIENT_SECRET"
```

## Components

| Module | Description |
|--------|-------------|
| `transport` | Base HTTP transport with OAuth2 client credentials |
| `errors` | Shared exception hierarchy (APIError, NotFoundError, etc.) |
| `pagination` | Async Paginator for list endpoints |
| `filter` | `where_to_filter()` for type-safe filtering |

## Usage

This package is used internally by:
- `timeback-oneroster`
- `timeback-caliper`
- `timeback-edubridge`
- `timeback-core`

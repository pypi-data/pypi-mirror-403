"""
Resolver utilities.

This module provides shared resolver helpers so service clients can:
- build a `TimebackProvider` from env/platform + credentials
- build a `TimebackProvider` from explicit URLs + credentials
- fall back to service-specific environment variables
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypedDict

from .config import DEFAULT_PLATFORM, Environment, Platform
from .provider import TimebackProvider

if TYPE_CHECKING:
    from .provider import CustomPaths, PathProfileName


@dataclass(frozen=True)
class EnvVarNames:
    """Environment variable names for fallback config."""

    base_url: str
    auth_url: str
    client_id: str
    client_secret: str


def _missing_env_error(names: list[str]) -> str:
    vars_list = "\n".join(f"  - {name}" for name in names)
    return (
        f"Missing required environment variable(s):\n{vars_list}\n\n"
        "Either:\n"
        "  1. Set these variables in your environment, or\n"
        "  2. Pass the values directly to the client constructor"
    )


def resolve_credentials(
    *,
    client_id: str | None,
    client_secret: str | None,
    env_vars: EnvVarNames,
) -> tuple[str, str]:
    """Resolve credentials from args or env vars."""
    resolved_id = client_id or os.environ.get(env_vars.client_id)
    resolved_secret = client_secret or os.environ.get(env_vars.client_secret)

    missing: list[str] = []
    if not resolved_id:
        missing.append(env_vars.client_id)
    if not resolved_secret:
        missing.append(env_vars.client_secret)
    if missing:
        raise ValueError(_missing_env_error(missing))

    # After validation, both values are guaranteed to be non-None strings
    assert resolved_id is not None
    assert resolved_secret is not None

    return resolved_id, resolved_secret


def resolve_explicit_urls(
    *,
    base_url: str | None,
    auth_url: str | None,
    env_vars: EnvVarNames,
) -> tuple[str, str]:
    """Resolve base/auth URLs from args or env vars."""
    resolved_base = base_url or os.environ.get(env_vars.base_url)
    resolved_auth = auth_url or os.environ.get(env_vars.auth_url)

    missing: list[str] = []
    if not resolved_base:
        missing.append(env_vars.base_url)
    if not resolved_auth:
        missing.append(env_vars.auth_url)
    if missing:
        raise ValueError(_missing_env_error(missing))

    # After validation, both values are guaranteed to be non-None strings
    assert resolved_base is not None
    assert resolved_auth is not None

    return resolved_base, resolved_auth


def build_provider_env(
    *,
    platform: Platform | None,
    env: Environment,
    client_id: str | None,
    client_secret: str | None,
    timeout: float,
    env_vars: EnvVarNames,
) -> TimebackProvider:
    """Build provider for env/platform mode."""
    resolved_id, resolved_secret = resolve_credentials(
        client_id=client_id,
        client_secret=client_secret,
        env_vars=env_vars,
    )
    return TimebackProvider(
        platform=platform or DEFAULT_PLATFORM,
        env=env,
        client_id=resolved_id,
        client_secret=resolved_secret,
        timeout=timeout,
    )


def build_provider_explicit(
    *,
    base_url: str | None,
    auth_url: str | None,
    client_id: str | None,
    client_secret: str | None,
    timeout: float,
    env_vars: EnvVarNames,
    path_profile: PathProfileName | None = None,
    paths: CustomPaths | None = None,
) -> TimebackProvider:
    """Build provider for explicit URL mode."""
    resolved_base, resolved_auth = resolve_explicit_urls(
        base_url=base_url,
        auth_url=auth_url,
        env_vars=env_vars,
    )
    resolved_id, resolved_secret = resolve_credentials(
        client_id=client_id,
        client_secret=client_secret,
        env_vars=env_vars,
    )
    return TimebackProvider(
        base_url=resolved_base,
        auth_url=resolved_auth,
        client_id=resolved_id,
        client_secret=resolved_secret,
        timeout=timeout,
        path_profile=path_profile,
        paths=paths,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED RESOLVER
# ═══════════════════════════════════════════════════════════════════════════════


class ResolvedProvider(TypedDict):
    """Result of resolve_to_provider when mode is 'provider'."""

    mode: Literal["provider"]
    provider: TimebackProvider


class ResolvedTransport(TypedDict):
    """Result of resolve_to_provider when mode is 'transport'."""

    mode: Literal["transport"]
    transport: object  # The injected transport


ResolveResult = ResolvedProvider | ResolvedTransport


@dataclass
class ResolverConfig:
    """
    Configuration for resolve_to_provider.
    """

    # Pre-built provider (highest precedence)
    provider: TimebackProvider | None = None

    # Pre-built transport (for testing/injection)
    transport: object | None = None

    # Env mode
    platform: Platform | None = None
    env: Environment | None = None

    # Explicit mode
    base_url: str | None = None
    auth_url: str | None = None

    # Services mode
    services: dict[str, str] | None = None

    # Auth
    client_id: str | None = None
    client_secret: str | None = None

    # Options
    timeout: float = 30.0
    path_profile: PathProfileName | None = None
    paths: CustomPaths | None = None


def resolve_to_provider(
    config: ResolverConfig,
    env_vars: EnvVarNames,
) -> ResolveResult:
    """
    Resolve client configuration to a provider or transport.

    This is the unified entry point for resolving any client configuration mode
    into a usable provider/transport. The precedence order is:

    1. transport - If provided, return immediately (for testing/injection)
    2. provider - If provided, return immediately (pre-built provider)
    3. env config - If env is set, use platform endpoints
    4. explicit config - If base_url is set, use explicit URLs
    5. services config - If services is set, use per-service URLs
    6. env-var fallback - Try to build from environment variables

    Args:
        config: Resolver configuration with various config options
        env_vars: Environment variable names for fallback resolution

    Returns:
        ResolveResult with mode='provider' or mode='transport'

    Raises:
        ValueError: If no valid configuration is found
    """
    # 1. Transport mode (for testing/injection)
    if config.transport is not None:
        return ResolvedTransport(mode="transport", transport=config.transport)

    # 2. Provider mode (pre-built provider)
    if config.provider is not None:
        return ResolvedProvider(mode="provider", provider=config.provider)

    # 3. Env config mode (platform + env)
    if config.env is not None:
        resolved_id, resolved_secret = resolve_credentials(
            client_id=config.client_id,
            client_secret=config.client_secret,
            env_vars=env_vars,
        )
        provider = TimebackProvider(
            platform=config.platform or DEFAULT_PLATFORM,
            env=config.env,
            client_id=resolved_id,
            client_secret=resolved_secret,
            timeout=config.timeout,
            path_profile=config.path_profile,
            paths=config.paths,
        )
        return ResolvedProvider(mode="provider", provider=provider)

    # 4. Explicit config mode (base_url provided)
    if config.base_url is not None:
        auth_url = config.auth_url
        require_auth = auth_url is not None

        # Only resolve credentials if auth is required
        resolved_id: str | None = None
        resolved_secret: str | None = None
        if require_auth:
            resolved_id, resolved_secret = resolve_credentials(
                client_id=config.client_id,
                client_secret=config.client_secret,
                env_vars=env_vars,
            )

        provider = TimebackProvider(
            base_url=config.base_url,
            auth_url=auth_url,
            client_id=resolved_id,
            client_secret=resolved_secret,
            timeout=config.timeout,
            path_profile=config.path_profile,
            paths=config.paths,
        )
        return ResolvedProvider(mode="provider", provider=provider)

    # 5. Services config mode (per-service URLs)
    if config.services is not None:
        auth_url = config.auth_url
        require_auth = auth_url is not None

        # Only resolve credentials if auth is required
        resolved_id = None
        resolved_secret = None
        if require_auth:
            resolved_id, resolved_secret = resolve_credentials(
                client_id=config.client_id,
                client_secret=config.client_secret,
                env_vars=env_vars,
            )

        provider = TimebackProvider(
            services=config.services,
            auth_url=auth_url,
            client_id=resolved_id,
            client_secret=resolved_secret,
            timeout=config.timeout,
            path_profile=config.path_profile,
            paths=config.paths,
        )
        return ResolvedProvider(mode="provider", provider=provider)

    # 6. Env-var fallback mode (try to get URLs from environment)
    env_base_url = os.environ.get(env_vars.base_url)
    env_auth_url = os.environ.get(env_vars.auth_url)

    if env_base_url:
        # Got base_url from env, try to build explicit provider
        resolved_id, resolved_secret = resolve_credentials(
            client_id=config.client_id,
            client_secret=config.client_secret,
            env_vars=env_vars,
        )
        provider = TimebackProvider(
            base_url=env_base_url,
            auth_url=env_auth_url,
            client_id=resolved_id,
            client_secret=resolved_secret,
            timeout=config.timeout,
            path_profile=config.path_profile,
            paths=config.paths,
        )
        return ResolvedProvider(mode="provider", provider=provider)

    # No valid configuration found
    raise ValueError(
        "No valid configuration found. Provide one of:\n"
        "  - provider: Pre-built TimebackProvider\n"
        "  - transport: Pre-built transport (for testing)\n"
        f"  - env: Environment name (staging/production) with platform\n"
        f"  - base_url: Explicit base URL\n"
        f"  - services: Per-service URL map\n"
        f"  - Environment variables: {env_vars.base_url}, {env_vars.auth_url}"
    )


__all__ = [
    "EnvVarNames",
    "ResolveResult",
    "ResolvedProvider",
    "ResolvedTransport",
    "ResolverConfig",
    "build_provider_env",
    "build_provider_explicit",
    "resolve_credentials",
    "resolve_explicit_urls",
    "resolve_to_provider",
]

"""
Timeback Provider

Encapsulates platform connection configuration including endpoints and auth.
Providers are complete "connection" objects that clients consume.


"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from .config import (
    DEFAULT_PLATFORM,
    PLATFORM_ENDPOINTS,
    PLATFORM_PATHS,
    CaliperPaths,
    EdubridgePaths,
    OneRosterPaths,
    PlatformPaths,
)
from .token_manager import TokenManager, TokenManagerConfig

if TYPE_CHECKING:
    from .config import Environment, Platform

# ═══════════════════════════════════════════════════════════════════════════════
# PATH PROFILE TYPES
# ═══════════════════════════════════════════════════════════════════════════════

# Path profile names correspond to platform keys
PathProfileName = Literal["BEYOND_AI", "LEARNWITH_AI"]

# Custom paths dict for per-service path overrides
CustomPaths = dict[str, Any]  # e.g., {"oneroster": OneRosterPaths(...), "caliper": {...}}

# ═══════════════════════════════════════════════════════════════════════════════
# RESOLVED ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ResolvedEndpoint:
    """Resolved endpoint for a service."""

    base_url: str
    auth_url: str | None


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH CHECK RESULT
# ═══════════════════════════════════════════════════════════════════════════════


class AuthCheckChecks(TypedDict):
    """Detailed check results for auth verification."""

    token_acquisition: bool  # camelCase in TS: tokenAcquisition


class AuthCheckResult(TypedDict, total=False):
    """
    Result of an authentication check.
    """

    ok: bool
    latency_ms: int  # camelCase in TS: latencyMs
    error: str | None
    checks: AuthCheckChecks


# ═══════════════════════════════════════════════════════════════════════════════
# PROVIDER
# ═══════════════════════════════════════════════════════════════════════════════

ServiceName = Literal["oneroster", "caliper", "edubridge"]


class TimebackProvider:
    """
    Timeback Provider - encapsulates a complete platform connection.

    A provider contains everything needed to connect to Timeback APIs:
    - Service endpoints (URLs)
    - Authentication credentials
    - Configuration options
    - Shared token managers (cached by auth URL)

    Providers can be created from:
    - Platform + environment (uses known Timeback endpoints)
    - Explicit base URL (single URL for all services)
    - Per-service URLs (different URLs for each service)

    Example (environment mode):
        ```python
        provider = TimebackProvider(
            platform="BEYOND_AI",
            env="staging",
            client_id="...",
            client_secret="...",
        )
        ```

    Example (explicit URL mode):
        ```python
        provider = TimebackProvider(
            base_url="https://api.myschool.edu",
            auth_url="https://auth.myschool.edu/oauth/token",
            client_id="...",
            client_secret="...",
        )
        ```

    Example (per-service URLs):
        ```python
        provider = TimebackProvider(
            services={
                "oneroster": "https://roster.myschool.edu",
                "caliper": "https://analytics.myschool.edu",
            },
            auth_url="https://auth.myschool.edu/oauth/token",
            client_id="...",
            client_secret="...",
        )
        ```
    """

    def __init__(
        self,
        *,
        # Env mode
        platform: Platform | None = None,
        env: Environment | None = None,
        # Explicit mode
        base_url: str | None = None,
        # Services mode
        services: dict[str, str] | None = None,
        # Auth
        auth_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        # Options
        timeout: float = 30.0,
        # Path configuration
        path_profile: PathProfileName | None = None,
        paths: CustomPaths | None = None,
    ) -> None:
        """
        Create a new TimebackProvider.

        Args:
            platform: Platform identifier (BEYOND_AI or LEARNWITH_AI)
            env: Environment (staging or production)
            base_url: Single base URL for all services (explicit mode)
            services: Per-service URLs (services mode)
            auth_url: OAuth2 token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            timeout: Request timeout in seconds
            path_profile: Named path profile to use (BEYOND_AI or LEARNWITH_AI).
                         If not specified, uses platform's default paths.
            paths: Custom path overrides per service. Merged over profile paths.
                   Example: {"oneroster": OneRosterPaths(rostering="/custom/path")}
        """
        self.platform = platform
        self.env = env
        self.timeout = timeout
        self.path_profile = path_profile

        # Store credentials
        self._client_id = client_id
        self._client_secret = client_secret

        # Shared token managers by auth URL
        self._token_managers: dict[str, TokenManager] = {}

        # Resolve endpoints based on config mode
        if env is not None and platform is None:
            platform = DEFAULT_PLATFORM

        if env is not None:
            # Env mode
            self.platform = platform
            self.env = env
            platform_key = platform or DEFAULT_PLATFORM
            endpoints = PLATFORM_ENDPOINTS.get(platform_key)
            if not endpoints:
                raise ValueError(f"Unknown platform: {platform}")

            self._auth_url = endpoints["token"].get(env)
            # Use canonical per-platform path profiles, or use path_profile if specified
            profile_key = path_profile or platform_key
            base_paths = PLATFORM_PATHS.get(profile_key, PLATFORM_PATHS[platform_key])
            self._paths = self._apply_path_overrides(base_paths, paths)

            # Endpoints are always present for oneroster + caliper.
            # Edubridge is platform-dependent (LearnWith.AI does not support it).
            self._endpoints = {
                "oneroster": ResolvedEndpoint(
                    base_url=endpoints["api"][env],
                    auth_url=self._auth_url,
                ),
                "caliper": ResolvedEndpoint(
                    base_url=endpoints["caliper"][env],
                    auth_url=self._auth_url,
                ),
            }
            if self._paths.edubridge is not None:
                self._endpoints["edubridge"] = ResolvedEndpoint(
                    base_url=endpoints["api"][env],
                    auth_url=self._auth_url,
                )
        elif base_url is not None:
            # Explicit mode
            self._auth_url = auth_url
            self._endpoints = {
                "oneroster": ResolvedEndpoint(base_url=base_url, auth_url=auth_url),
                "edubridge": ResolvedEndpoint(base_url=base_url, auth_url=auth_url),
                "caliper": ResolvedEndpoint(base_url=base_url, auth_url=auth_url),
            }
            # Use path profile if specified, otherwise default to BEYOND_AI
            profile_key = path_profile or DEFAULT_PLATFORM
            base_paths = PLATFORM_PATHS.get(profile_key, PLATFORM_PATHS[DEFAULT_PLATFORM])
            self._paths = self._apply_path_overrides(base_paths, paths)
        elif services is not None:
            # Services mode
            self._auth_url = auth_url
            self._endpoints = {}
            for service, url in services.items():
                self._endpoints[service] = ResolvedEndpoint(base_url=url, auth_url=auth_url)
            # Use path profile if specified, otherwise default to BEYOND_AI
            profile_key = path_profile or DEFAULT_PLATFORM
            base_paths = PLATFORM_PATHS.get(profile_key, PLATFORM_PATHS[DEFAULT_PLATFORM])
            self._paths = self._apply_path_overrides(base_paths, paths)
        else:
            raise ValueError("Provider configuration required. Provide env, base_url, or services.")

    def _apply_path_overrides(
        self, base_paths: PlatformPaths, custom_paths: CustomPaths | None
    ) -> PlatformPaths:
        """
        Apply custom path overrides to base path profiles.

        Args:
            base_paths: Base platform paths
            custom_paths: Custom overrides per service

        Returns:
            New PlatformPaths with overrides applied
        """
        if not custom_paths:
            return base_paths

        oneroster = base_paths.oneroster
        edubridge = base_paths.edubridge
        caliper = base_paths.caliper

        # Apply oneroster overrides
        if "oneroster" in custom_paths:
            override = custom_paths["oneroster"]
            if isinstance(override, OneRosterPaths):
                oneroster = override
            elif isinstance(override, dict):
                oneroster = replace(oneroster, **override)

        # Apply edubridge overrides
        if "edubridge" in custom_paths:
            override = custom_paths["edubridge"]
            if override is None:
                edubridge = None
            elif isinstance(override, EdubridgePaths):
                edubridge = override
            elif isinstance(override, dict) and edubridge is not None:
                edubridge = replace(edubridge, **override)

        # Apply caliper overrides
        if "caliper" in custom_paths:
            override = custom_paths["caliper"]
            if isinstance(override, CaliperPaths):
                caliper = override
            elif isinstance(override, dict):
                caliper = replace(caliper, **override)

        return PlatformPaths(oneroster=oneroster, edubridge=edubridge, caliper=caliper)

    def get_endpoint(self, service: ServiceName) -> ResolvedEndpoint:
        """
        Get the resolved endpoint for a specific service.

        Args:
            service: Service name (oneroster, caliper, edubridge)

        Returns:
            Resolved endpoint with base_url and auth_url

        Raises:
            ValueError: If the service is not configured
        """
        endpoint = self._endpoints.get(service)
        if not endpoint:
            raise ValueError(f'Service "{service}" is not configured in this provider')
        return endpoint

    def has_service(self, service: ServiceName) -> bool:
        """
        Check if a service is available in this provider.

        Args:
            service: Service name to check

        Returns:
            True if the service is configured
        """
        return service in self._endpoints

    def get_available_services(self) -> list[ServiceName]:
        """
        Get all configured service names.

        Returns:
            List of service names available in this provider
        """
        return list(self._endpoints.keys())  # type: ignore[return-value]

    def get_paths(self, service: ServiceName) -> Any:
        """
        Get path profiles for a service.

        Args:
            service: Service name

        Returns:
            Path configuration for the service
        """
        if service == "oneroster":
            return self._paths.oneroster
        elif service == "edubridge":
            if self._paths.edubridge is None:
                raise ValueError(f'Service "{service}" is not supported on this platform')
            return self._paths.edubridge
        elif service == "caliper":
            return self._paths.caliper
        else:
            raise ValueError(f"Unknown service: {service}")

    def get_service_paths(self, service: ServiceName) -> Any:
        """Alias for get_paths()."""
        return self.get_paths(service)

    def get_all_paths(self) -> PlatformPaths:
        """
        Get all path profiles for all services.

        Returns:
            PlatformPaths with all service path configurations
        """
        return self._paths

    def has_service_support(self, service: ServiceName) -> bool:
        """
        Check if a service is fully supported (endpoint + paths).

        Args:
            service: Service name to check

        Returns:
            True if the service has both endpoint and path configuration
        """
        # Check endpoint exists
        if service not in self._endpoints:
            return False

        # Check paths exist
        paths_by_service = {
            "oneroster": self._paths.oneroster,
            "edubridge": self._paths.edubridge,
            "caliper": self._paths.caliper,
        }
        return paths_by_service.get(service) is not None

    def get_endpoint_with_paths(self, service: ServiceName) -> tuple[ResolvedEndpoint, Any]:
        """
        Get both endpoint and paths for a service in a single call.

        Args:
            service: Service name

        Returns:
            Tuple of (ResolvedEndpoint, service paths)

        Raises:
            ValueError: If service is not configured or not supported
        """
        endpoint = self.get_endpoint(service)
        paths = self.get_paths(service)
        return endpoint, paths

    def get_token_manager(self, service: ServiceName) -> TokenManager | None:
        """
        Get a TokenManager for a specific service.

        TokenManagers are cached by auth_url, so services sharing the same
        token endpoint will share the same cached OAuth tokens.

        Args:
            service: Service name

        Returns:
            Cached TokenManager for the service's token endpoint, or None if no auth

        Raises:
            ValueError: If credentials are missing
        """
        endpoint = self.get_endpoint(service)
        auth_url = endpoint.auth_url

        if not auth_url:
            return None

        if not self._client_id or not self._client_secret:
            raise ValueError(
                f'Service "{service}" requires authentication but no credentials were provided'
            )

        if auth_url not in self._token_managers:
            self._token_managers[auth_url] = TokenManager(
                TokenManagerConfig(
                    token_url=auth_url,
                    client_id=self._client_id,
                    client_secret=self._client_secret,
                    timeout=self.timeout,
                )
            )

        return self._token_managers[auth_url]

    async def check_auth(self) -> AuthCheckResult:
        """
        Verify that OAuth authentication is working.

        Attempts to acquire a token using the provider's credentials.
        Returns a health check result with success/failure and latency info.

        Returns:
            Auth check result with ok, latency_ms, and optional error
        """
        if not self._auth_url or not self._client_id or not self._client_secret:
            raise ValueError("No auth configured on this provider")

        start_time = time.time()

        # Get or create token manager for the primary auth URL
        if self._auth_url not in self._token_managers:
            self._token_managers[self._auth_url] = TokenManager(
                TokenManagerConfig(
                    token_url=self._auth_url,
                    client_id=self._client_id,
                    client_secret=self._client_secret,
                    timeout=self.timeout,
                )
            )

        manager = self._token_managers[self._auth_url]

        try:
            await manager.get_token()
            return AuthCheckResult(
                ok=True,
                latency_ms=int((time.time() - start_time) * 1000),
                checks=AuthCheckChecks(token_acquisition=True),
            )
        except Exception as e:
            return AuthCheckResult(
                ok=False,
                latency_ms=int((time.time() - start_time) * 1000),
                error=str(e),
                checks=AuthCheckChecks(token_acquisition=False),
            )

    def invalidate_tokens(self) -> None:
        """
        Invalidate all cached OAuth tokens.

        Call this when closing the client or when tokens need to be refreshed.
        New tokens will be acquired on the next API call.
        """
        for manager in self._token_managers.values():
            manager.invalidate()
        self._token_managers.clear()


__all__ = [
    "AuthCheckChecks",
    "AuthCheckResult",
    "CustomPaths",
    "PathProfileName",
    "ResolvedEndpoint",
    "ServiceName",
    "TimebackProvider",
]

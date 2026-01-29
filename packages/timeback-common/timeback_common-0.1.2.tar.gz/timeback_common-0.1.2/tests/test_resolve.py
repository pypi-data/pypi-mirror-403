"""Tests for resolver utilities."""

import os
from unittest import mock

import pytest

from timeback_common import (
    EnvVarNames,
    ResolverConfig,
    TimebackProvider,
    resolve_to_provider,
)

# Test env var names
TEST_ENV_VARS = EnvVarNames(
    base_url="TEST_BASE_URL",
    auth_url="TEST_AUTH_URL",
    client_id="TEST_CLIENT_ID",
    client_secret="TEST_CLIENT_SECRET",
)


class TestResolveToProviderTransportMode:
    """Tests for resolve_to_provider with transport mode."""

    def test_returns_transport_mode_when_transport_provided(self) -> None:
        """Returns transport mode when transport is provided."""
        mock_transport = object()
        config = ResolverConfig(transport=mock_transport)

        result = resolve_to_provider(config, TEST_ENV_VARS)

        assert result["mode"] == "transport"
        assert result["transport"] is mock_transport

    def test_transport_mode_has_highest_precedence(self) -> None:
        """Transport mode has highest precedence over other options."""
        mock_transport = object()
        provider = TimebackProvider(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        config = ResolverConfig(
            transport=mock_transport,
            provider=provider,  # Should be ignored
            env="staging",  # Should be ignored
        )

        result = resolve_to_provider(config, TEST_ENV_VARS)

        assert result["mode"] == "transport"


class TestResolveToProviderProviderMode:
    """Tests for resolve_to_provider with pre-built provider."""

    def test_returns_provider_mode_when_provider_provided(self) -> None:
        """Returns provider mode when provider is provided."""
        provider = TimebackProvider(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        config = ResolverConfig(provider=provider)

        result = resolve_to_provider(config, TEST_ENV_VARS)

        assert result["mode"] == "provider"
        assert result["provider"] is provider


class TestResolveToProviderEnvMode:
    """Tests for resolve_to_provider with env config."""

    def test_builds_provider_from_env_config(self) -> None:
        """Builds provider from env config."""
        config = ResolverConfig(
            env="staging",
            platform="BEYOND_AI",
            client_id="test-id",
            client_secret="test-secret",
        )

        result = resolve_to_provider(config, TEST_ENV_VARS)

        assert result["mode"] == "provider"
        assert result["provider"].env == "staging"
        assert result["provider"].platform == "BEYOND_AI"

    def test_resolves_credentials_from_env_vars(self) -> None:
        """Resolves credentials from environment variables."""
        with mock.patch.dict(
            os.environ,
            {
                "TEST_CLIENT_ID": "env-id",
                "TEST_CLIENT_SECRET": "env-secret",
            },
        ):
            config = ResolverConfig(env="staging")

            result = resolve_to_provider(config, TEST_ENV_VARS)

            assert result["mode"] == "provider"


class TestResolveToProviderExplicitMode:
    """Tests for resolve_to_provider with explicit URLs."""

    def test_builds_provider_from_explicit_urls(self) -> None:
        """Builds provider from explicit URLs."""
        config = ResolverConfig(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth/token",
            client_id="test-id",
            client_secret="test-secret",
        )

        result = resolve_to_provider(config, TEST_ENV_VARS)

        assert result["mode"] == "provider"
        endpoint = result["provider"].get_endpoint("oneroster")
        assert endpoint.base_url == "https://api.example.com"

    def test_supports_path_profile_in_explicit_mode(self) -> None:
        """Supports path_profile in explicit mode."""
        config = ResolverConfig(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth/token",
            client_id="test-id",
            client_secret="test-secret",
            path_profile="LEARNWITH_AI",
        )

        result = resolve_to_provider(config, TEST_ENV_VARS)

        assert result["mode"] == "provider"
        paths = result["provider"].get_paths("oneroster")
        assert paths.rostering == "/rostering/1.0"


class TestResolveToProviderServicesMode:
    """Tests for resolve_to_provider with per-service URLs."""

    def test_builds_provider_from_services(self) -> None:
        """Builds provider from per-service URLs."""
        config = ResolverConfig(
            services={
                "oneroster": "https://roster.example.com",
                "caliper": "https://caliper.example.com",
            },
            auth_url="https://auth.example.com/oauth/token",
            client_id="test-id",
            client_secret="test-secret",
        )

        result = resolve_to_provider(config, TEST_ENV_VARS)

        assert result["mode"] == "provider"
        assert result["provider"].has_service("oneroster")
        assert result["provider"].has_service("caliper")


class TestResolveToProviderEnvVarFallback:
    """Tests for resolve_to_provider with env var fallback."""

    def test_falls_back_to_env_vars(self) -> None:
        """Falls back to environment variables when no config provided."""
        with mock.patch.dict(
            os.environ,
            {
                "TEST_BASE_URL": "https://api.example.com",
                "TEST_AUTH_URL": "https://auth.example.com/oauth/token",
                "TEST_CLIENT_ID": "env-id",
                "TEST_CLIENT_SECRET": "env-secret",
            },
        ):
            config = ResolverConfig()

            result = resolve_to_provider(config, TEST_ENV_VARS)

            assert result["mode"] == "provider"
            endpoint = result["provider"].get_endpoint("oneroster")
            assert endpoint.base_url == "https://api.example.com"

    def test_raises_when_no_config_and_no_env_vars(self) -> None:
        """Raises ValueError when no config and no env vars."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = ResolverConfig()

            with pytest.raises(ValueError, match="No valid configuration found"):
                resolve_to_provider(config, TEST_ENV_VARS)


class TestResolveToProviderPrecedence:
    """Tests for resolve_to_provider config precedence."""

    def test_precedence_order(self) -> None:
        """Config options follow correct precedence order."""
        # The precedence is: transport > provider > env > explicit > services > env-var

        provider = TimebackProvider(
            base_url="https://provider.example.com",
            auth_url="https://auth.example.com/oauth/token",
            client_id="test-id",
            client_secret="test-secret",
        )

        # provider should win over env
        config = ResolverConfig(
            provider=provider,
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

        result = resolve_to_provider(config, TEST_ENV_VARS)

        assert result["mode"] == "provider"
        endpoint = result["provider"].get_endpoint("oneroster")
        assert endpoint.base_url == "https://provider.example.com"

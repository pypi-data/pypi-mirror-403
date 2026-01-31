"""Tests for TimebackProvider."""

import pytest

from timeback_common import (
    OneRosterPaths,
    TimebackProvider,
)


class TestTimebackProviderEnvMode:
    """Tests for TimebackProvider in env mode."""

    def test_creates_provider_with_platform_and_env(self) -> None:
        """Creates provider with platform and env."""
        provider = TimebackProvider(
            platform="BEYOND_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

        assert provider.platform == "BEYOND_AI"
        assert provider.env == "staging"
        assert provider.has_service("oneroster")
        assert provider.has_service("caliper")

    def test_defaults_to_beyond_ai_platform(self) -> None:
        """Defaults to BEYOND_AI platform when only env is provided."""
        provider = TimebackProvider(
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

        assert provider.platform == "BEYOND_AI"

    def test_learnwithai_does_not_support_edubridge(self) -> None:
        """LearnWith.AI platform does not support Edubridge."""
        provider = TimebackProvider(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

        assert provider.has_service("oneroster")
        assert provider.has_service("caliper")
        assert not provider.has_service("edubridge")


class TestTimebackProviderExplicitMode:
    """Tests for TimebackProvider in explicit URL mode."""

    def test_creates_provider_with_explicit_urls(self) -> None:
        """Creates provider with explicit URLs."""
        provider = TimebackProvider(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth/token",
            client_id="test-id",
            client_secret="test-secret",
        )

        endpoint = provider.get_endpoint("oneroster")
        assert endpoint.base_url == "https://api.example.com"
        assert endpoint.auth_url == "https://auth.example.com/oauth/token"


class TestTimebackProviderServicesMode:
    """Tests for TimebackProvider in services mode."""

    def test_creates_provider_with_per_service_urls(self) -> None:
        """Creates provider with per-service URLs."""
        provider = TimebackProvider(
            services={
                "oneroster": "https://roster.example.com",
                "caliper": "https://caliper.example.com",
            },
            auth_url="https://auth.example.com/oauth/token",
            client_id="test-id",
            client_secret="test-secret",
        )

        oneroster = provider.get_endpoint("oneroster")
        caliper = provider.get_endpoint("caliper")

        assert oneroster.base_url == "https://roster.example.com"
        assert caliper.base_url == "https://caliper.example.com"


class TestTimebackProviderPathProfile:
    """Tests for TimebackProvider path profile feature."""

    def test_uses_default_paths_for_platform(self) -> None:
        """Uses default paths for the platform."""
        provider = TimebackProvider(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

        paths = provider.get_paths("oneroster")
        # LearnWith.AI uses different paths
        assert paths.rostering == "/rostering/1.0"

    def test_path_profile_overrides_platform_paths(self) -> None:
        """path_profile parameter overrides platform default paths."""
        provider = TimebackProvider(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
            path_profile="BEYOND_AI",  # Use BEYOND_AI paths instead
        )

        paths = provider.get_paths("oneroster")
        # Should use BEYOND_AI paths (the default IMS paths)
        assert paths.rostering == "/ims/oneroster/rostering/v1p2"

    def test_custom_paths_override_profile(self) -> None:
        """Custom paths parameter overrides path profile."""
        provider = TimebackProvider(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth/token",
            client_id="test-id",
            client_secret="test-secret",
            paths={
                "oneroster": {"rostering": "/custom/rostering/path"},
            },
        )

        paths = provider.get_paths("oneroster")
        assert paths.rostering == "/custom/rostering/path"
        # Other paths should remain default
        assert paths.gradebook == "/ims/oneroster/gradebook/v1p2"

    def test_custom_paths_with_dataclass(self) -> None:
        """Custom paths can be provided as dataclass instances."""
        custom_oneroster = OneRosterPaths(
            rostering="/v2/rostering",
            gradebook="/v2/gradebook",
            resources="/v2/resources",
        )
        provider = TimebackProvider(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth/token",
            client_id="test-id",
            client_secret="test-secret",
            paths={"oneroster": custom_oneroster},
        )

        paths = provider.get_paths("oneroster")
        assert paths.rostering == "/v2/rostering"
        assert paths.gradebook == "/v2/gradebook"


class TestTimebackProviderMethods:
    """Tests for TimebackProvider helper methods."""

    def test_get_all_paths(self) -> None:
        """get_all_paths() returns PlatformPaths."""
        provider = TimebackProvider(
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

        paths = provider.get_all_paths()

        assert paths.oneroster is not None
        assert paths.caliper is not None

    def test_get_service_paths_alias(self) -> None:
        """get_service_paths() is an alias for get_paths()."""
        provider = TimebackProvider(
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

        paths1 = provider.get_paths("oneroster")
        paths2 = provider.get_service_paths("oneroster")

        assert paths1 == paths2

    def test_has_service_support(self) -> None:
        """has_service_support() checks both endpoint and paths."""
        provider = TimebackProvider(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

        assert provider.has_service_support("oneroster") is True
        assert provider.has_service_support("caliper") is True
        # Edubridge not supported on LearnWith.AI
        assert provider.has_service_support("edubridge") is False

    def test_get_endpoint_with_paths(self) -> None:
        """get_endpoint_with_paths() returns tuple of endpoint and paths."""
        provider = TimebackProvider(
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

        endpoint, paths = provider.get_endpoint_with_paths("oneroster")

        assert endpoint.base_url is not None
        assert paths.rostering is not None

    def test_raises_for_unsupported_service(self) -> None:
        """Raises ValueError for unsupported service."""
        provider = TimebackProvider(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )

        with pytest.raises(ValueError, match="not supported"):
            provider.get_paths("edubridge")


class TestTimebackProviderErrors:
    """Tests for TimebackProvider error cases."""

    def test_raises_without_config(self) -> None:
        """Raises ValueError when no config is provided."""
        with pytest.raises(ValueError, match="Provider configuration required"):
            TimebackProvider(client_id="test-id", client_secret="test-secret")

    def test_raises_for_unknown_platform(self) -> None:
        """Raises ValueError for unknown platform."""
        with pytest.raises(ValueError, match="Unknown platform"):
            TimebackProvider(
                platform="UNKNOWN",  # type: ignore[arg-type]
                env="staging",
                client_id="test-id",
                client_secret="test-secret",
            )

"""
Tests for TimebackProvider

Covers provider configuration modes, shared token management, and check_auth.
"""

from __future__ import annotations

import pytest

from timeback_common import TimebackProvider


class TestProviderConfiguration:
    """Tests for provider configuration modes."""

    def test_env_mode_creates_provider(self):
        """Provider can be created with env mode."""
        provider = TimebackProvider(
            env="staging",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert provider.env == "staging"
        assert provider.has_service("oneroster")
        assert provider.has_service("caliper")
        assert provider.has_service("edubridge")

    def test_env_mode_resolves_endpoints(self):
        """Env mode resolves correct endpoints for services."""
        provider = TimebackProvider(
            platform="BEYOND_AI",
            env="staging",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        oneroster_endpoint = provider.get_endpoint("oneroster")
        caliper_endpoint = provider.get_endpoint("caliper")

        # BeyondAI staging endpoints
        assert "staging" in oneroster_endpoint.base_url
        assert "staging" in caliper_endpoint.base_url
        assert oneroster_endpoint.auth_url is not None

    def test_learnwithai_does_not_support_edubridge(self):
        """LearnWith.AI platform should not advertise edubridge support."""
        provider = TimebackProvider(
            platform="LEARNWITH_AI",
            env="staging",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert provider.has_service("oneroster") is True
        assert provider.has_service("caliper") is True
        assert provider.has_service("edubridge") is False

        with pytest.raises(ValueError, match="not supported"):
            provider.get_paths("edubridge")

        with pytest.raises(ValueError, match="not configured"):
            provider.get_endpoint("edubridge")

    def test_explicit_url_mode(self):
        """Provider can be created with explicit base_url mode."""
        provider = TimebackProvider(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/token",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        oneroster_endpoint = provider.get_endpoint("oneroster")
        assert oneroster_endpoint.base_url == "https://api.example.com"
        assert oneroster_endpoint.auth_url == "https://auth.example.com/token"

    def test_services_mode(self):
        """Provider can be created with per-service URLs."""
        provider = TimebackProvider(
            services={
                "oneroster": "https://roster.example.com",
                "caliper": "https://analytics.example.com",
            },
            auth_url="https://auth.example.com/token",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert provider.get_endpoint("oneroster").base_url == "https://roster.example.com"
        assert provider.get_endpoint("caliper").base_url == "https://analytics.example.com"

    def test_missing_config_raises(self):
        """Provider without config raises ValueError."""
        with pytest.raises(ValueError, match="Provider configuration required"):
            TimebackProvider(
                client_id="test-client-id",
                client_secret="test-client-secret",
            )

    def test_get_paths_returns_service_paths(self):
        """get_paths returns appropriate path profiles for each service."""
        provider = TimebackProvider(
            env="staging",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        oneroster_paths = provider.get_paths("oneroster")
        caliper_paths = provider.get_paths("caliper")
        edubridge_paths = provider.get_paths("edubridge")

        assert hasattr(oneroster_paths, "rostering")
        assert hasattr(oneroster_paths, "gradebook")
        assert hasattr(caliper_paths, "send")
        assert hasattr(edubridge_paths, "base")


class TestSharedTokenManager:
    """Tests for shared token management."""

    def test_same_auth_url_shares_token_manager(self):
        """Services with the same auth_url share a token manager."""
        provider = TimebackProvider(
            env="staging",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        # Get token managers for different services
        oneroster_tm = provider.get_token_manager("oneroster")
        edubridge_tm = provider.get_token_manager("edubridge")

        # They should be the same instance (same auth URL)
        assert oneroster_tm is edubridge_tm

    def test_invalidate_tokens_clears_cache(self):
        """invalidate_tokens clears all cached token managers."""
        provider = TimebackProvider(
            env="staging",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        # Trigger token manager creation
        provider.get_token_manager("oneroster")
        assert len(provider._token_managers) > 0

        # Invalidate
        provider.invalidate_tokens()
        assert len(provider._token_managers) == 0


class TestCheckAuth:
    """Tests for check_auth functionality."""

    @pytest.mark.asyncio
    async def test_check_auth_without_credentials_raises(self):
        """check_auth without credentials raises ValueError."""
        provider = TimebackProvider(
            base_url="https://api.example.com",
            auth_url=None,  # No auth configured
            client_id=None,
            client_secret=None,
        )

        with pytest.raises(ValueError, match="No auth configured"):
            await provider.check_auth()

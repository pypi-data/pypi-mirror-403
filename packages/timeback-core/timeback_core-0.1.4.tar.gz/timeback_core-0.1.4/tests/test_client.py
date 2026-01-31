"""Tests for TimebackClient."""

import pytest

from timeback_core import BroadcastResults, TimebackClient, TimebackManager


class TestTimebackClientInit:
    """Tests for client initialization."""

    def test_env_staging(self) -> None:
        """Test staging environment configuration."""
        client = TimebackClient(
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert (
            client._provider.get_endpoint("oneroster").base_url
            == "https://api.staging.alpha-1edtech.ai"
        )
        assert (
            client._provider.get_endpoint("caliper").base_url
            == "https://caliper.staging.alpha-1edtech.ai"
        )
        assert not client.closed

    def test_env_production(self) -> None:
        """Test production environment configuration."""
        client = TimebackClient(
            env="production",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert client._provider.get_endpoint("oneroster").base_url == "https://api.alpha-1edtech.ai"
        assert (
            client._provider.get_endpoint("caliper").base_url == "https://caliper.alpha-1edtech.ai"
        )

    def test_base_url_mode(self) -> None:
        """Test base URL configuration."""
        client = TimebackClient(
            base_url="https://custom.example.com",
            auth_url="https://auth.example.com/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert client._provider.get_endpoint("oneroster").base_url == "https://custom.example.com"
        assert client._provider.get_endpoint("caliper").base_url == "https://custom.example.com"
        assert client._provider.get_endpoint("edubridge").base_url == "https://custom.example.com"

    def test_services_mode(self) -> None:
        """Test explicit services configuration."""
        client = TimebackClient(
            services={
                "oneroster": "https://roster.example.com",
                "caliper": "https://analytics.example.com",
            },
            auth_url="https://auth.example.com/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert client._provider.get_endpoint("oneroster").base_url == "https://roster.example.com"
        assert client._provider.get_endpoint("caliper").base_url == "https://analytics.example.com"

    def test_missing_credentials_raises(self) -> None:
        """Test that missing credentials raise an error."""
        with pytest.raises(ValueError, match="client_id is required"):
            TimebackClient(env="staging", client_secret="secret")

        with pytest.raises(ValueError, match="client_secret is required"):
            TimebackClient(env="staging", client_id="id")

    def test_missing_config_raises(self) -> None:
        """Test that missing configuration raises an error."""
        with pytest.raises(ValueError, match="Configuration required"):
            TimebackClient(client_id="id", client_secret="secret")

    def test_invalid_env_raises(self) -> None:
        """Test that invalid environment raises an error."""
        with pytest.raises(ValueError, match="Invalid environment"):
            TimebackClient(env="invalid", client_id="id", client_secret="secret")

    def test_base_url_no_auth_mode(self) -> None:
        """Test that base_url mode works without auth."""
        # This is useful for local development against unauthenticated services
        client = TimebackClient(
            base_url="http://localhost:3000",
        )
        assert client._provider.get_endpoint("oneroster").base_url == "http://localhost:3000"
        # No auth_url means no token manager
        assert client._provider.get_token_manager("oneroster") is None

    def test_base_url_with_auth_requires_credentials(self) -> None:
        """Test that base_url with auth_url requires credentials."""
        with pytest.raises(ValueError, match="credentials are required"):
            TimebackClient(
                base_url="https://example.com",
                auth_url="https://auth.example.com/token",
                # Missing client_id and client_secret
            )


class TestTimebackClientServices:
    """Tests for sub-client access."""

    def test_oneroster_lazy_init(self) -> None:
        """Test that OneRoster client is lazily initialized."""
        client = TimebackClient(
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert client._oneroster is None
        _ = client.oneroster
        assert client._oneroster is not None

    def test_edubridge_lazy_init(self) -> None:
        """Test that Edubridge client is lazily initialized."""
        client = TimebackClient(
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert client._edubridge is None
        _ = client.edubridge
        assert client._edubridge is not None

    def test_caliper_lazy_init(self) -> None:
        """Test that Caliper client is lazily initialized."""
        client = TimebackClient(
            env="staging",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert client._caliper is None
        _ = client.caliper
        assert client._caliper is not None

    def test_service_not_configured_raises(self) -> None:
        """Test that accessing unconfigured service raises."""
        client = TimebackClient(
            services={"oneroster": "https://example.com"},
            auth_url="https://auth.example.com/token",
            client_id="id",
            client_secret="secret",
        )
        # oneroster should work
        _ = client.oneroster
        # caliper should fail
        with pytest.raises(RuntimeError, match="not configured"):
            _ = client.caliper


class TestTimebackManager:
    """Tests for TimebackManager."""

    def test_register_and_get(self) -> None:
        """Test registering and retrieving clients."""
        manager = TimebackManager()
        manager.register("alpha", env="staging", client_id="id", client_secret="secret")

        assert manager.has("alpha")
        assert not manager.has("beta")
        assert manager.size == 1
        assert "alpha" in manager.names

        client = manager.get("alpha")
        assert isinstance(client, TimebackClient)

    def test_get_unregistered_raises(self) -> None:
        """Test that getting unregistered client raises."""
        manager = TimebackManager()
        with pytest.raises(KeyError, match="not registered"):
            manager.get("nonexistent")

    def test_duplicate_register_raises(self) -> None:
        """Test that duplicate registration raises."""
        manager = TimebackManager()
        manager.register("alpha", env="staging", client_id="id", client_secret="secret")
        with pytest.raises(ValueError, match="already registered"):
            manager.register("alpha", env="staging", client_id="id", client_secret="secret")

    @pytest.mark.asyncio
    async def test_unregister(self) -> None:
        """Test unregistering clients."""
        manager = TimebackManager()
        manager.register("alpha", env="staging", client_id="id", client_secret="secret")

        assert await manager.unregister("alpha") is True
        assert await manager.unregister("alpha") is False
        assert manager.size == 0

    def test_method_chaining(self) -> None:
        """Test that register returns self for chaining."""
        manager = (
            TimebackManager()
            .register("alpha", env="staging", client_id="id", client_secret="secret")
            .register("beta", env="production", client_id="id", client_secret="secret")
        )
        assert manager.size == 2


class TestBroadcastResults:
    """Tests for BroadcastResults."""

    def test_access_by_name(self) -> None:
        """Test accessing results by name."""
        results = BroadcastResults(
            _results={
                "alpha": {"ok": True, "value": [1, 2, 3]},
                "beta": {"ok": False, "error": ValueError("test")},
            }
        )

        assert results["alpha"]["ok"] is True
        assert results["alpha"]["value"] == [1, 2, 3]
        assert results["beta"]["ok"] is False
        assert isinstance(results["beta"]["error"], ValueError)

    def test_succeeded_and_failed(self) -> None:
        """Test succeeded and failed properties."""
        results = BroadcastResults(
            _results={
                "alpha": {"ok": True, "value": "success1"},
                "beta": {"ok": True, "value": "success2"},
                "gamma": {"ok": False, "error": ValueError("fail")},
            }
        )

        assert len(results.succeeded) == 2
        assert len(results.failed) == 1
        assert ("alpha", "success1") in results.succeeded
        assert results.failed[0][0] == "gamma"

    def test_all_succeeded(self) -> None:
        """Test all_succeeded property."""
        all_ok = BroadcastResults(
            _results={
                "alpha": {"ok": True, "value": 1},
                "beta": {"ok": True, "value": 2},
            }
        )
        assert all_ok.all_succeeded is True
        assert all_ok.any_failed is False

        some_failed = BroadcastResults(
            _results={
                "alpha": {"ok": True, "value": 1},
                "beta": {"ok": False, "error": ValueError()},
            }
        )
        assert some_failed.all_succeeded is False
        assert some_failed.any_failed is True

    def test_values(self) -> None:
        """Test values() method."""
        all_ok = BroadcastResults(
            _results={
                "alpha": {"ok": True, "value": 1},
                "beta": {"ok": True, "value": 2},
            }
        )
        assert all_ok.values() == [1, 2]

        some_failed = BroadcastResults(
            _results={
                "alpha": {"ok": True, "value": 1},
                "beta": {"ok": False, "error": ValueError()},
            }
        )
        with pytest.raises(RuntimeError, match="operations failed"):
            some_failed.values()

    def test_contains_and_len(self) -> None:
        """Test __contains__ and __len__."""
        results = BroadcastResults(
            _results={
                "alpha": {"ok": True, "value": 1},
            }
        )
        assert "alpha" in results
        assert "beta" not in results
        assert len(results) == 1

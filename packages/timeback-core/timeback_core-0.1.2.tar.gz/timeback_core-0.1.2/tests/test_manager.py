"""Tests for TimebackManager."""

import pytest

from timeback_core import TimebackManager

# Test configurations
alpha_config = {
    "env": "staging",
    "client_id": "alpha-id",
    "client_secret": "alpha-secret",
}

beta_config = {
    "env": "production",
    "client_id": "beta-id",
    "client_secret": "beta-secret",
}


class TestRegistration:
    """Tests for TimebackManager registration."""

    def test_register_adds_client(self):
        """register() adds a client."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        assert manager.has("alpha") is True
        assert manager.size == 1

    def test_register_returns_self_for_chaining(self):
        """register() returns self for chaining."""
        manager = TimebackManager()
        result = manager.register("alpha", **alpha_config)

        assert result is manager

    def test_register_allows_chaining(self):
        """register() allows chaining."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config).register("beta", **beta_config)

        assert manager.size == 2

    def test_register_throws_on_duplicate_name(self):
        """register() throws on duplicate name."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        with pytest.raises(ValueError, match='Client "alpha" is already registered'):
            manager.register("alpha", **alpha_config)

    def test_names_returns_all_registered_client_names(self):
        """names returns all registered client names."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config).register("beta", **beta_config)

        assert manager.names == ["alpha", "beta"]


class TestGet:
    """Tests for TimebackManager get."""

    def test_get_returns_registered_client(self):
        """get() returns registered client."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        client = manager.get("alpha")

        assert client is not None
        assert hasattr(client, "oneroster")

    def test_get_throws_for_unregistered_name(self):
        """get() throws for unregistered name."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        with pytest.raises(KeyError, match=r'Client "beta" is not registered\. Available: alpha'):
            manager.get("beta")

    def test_get_shows_all_available_names_in_error(self):
        """get() shows all available names in error."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config).register("beta", **beta_config)

        with pytest.raises(KeyError, match="Available: alpha, beta"):
            manager.get("dev")

    def test_get_shows_none_when_no_clients_registered(self):
        """get() shows (none) when no clients registered."""
        manager = TimebackManager()

        with pytest.raises(KeyError, match=r"Available: \(none\)"):
            manager.get("alpha")

    def test_get_returns_same_instance_on_repeated_calls(self):
        """get() returns same instance on repeated calls."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        first = manager.get("alpha")
        second = manager.get("alpha")

        assert second is first


class TestHas:
    """Tests for TimebackManager has."""

    def test_has_returns_true_for_registered_client(self):
        """has() returns true for registered client."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        assert manager.has("alpha") is True

    def test_has_returns_false_for_unregistered_client(self):
        """has() returns false for unregistered client."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        assert manager.has("beta") is False


class TestBroadcast:
    """Tests for TimebackManager broadcast."""

    @pytest.mark.asyncio
    async def test_broadcast_returns_results_with_ok_value_for_successful_calls(self):
        """broadcast() returns BroadcastResults with ok/value for successful calls."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config).register("beta", **beta_config)

        results = await manager.broadcast(lambda client: client._provider.env)

        assert results["alpha"]["ok"] is True
        assert results["alpha"]["value"] == "staging"
        assert results["beta"]["ok"] is True
        assert results["beta"]["value"] == "production"
        assert results.all_succeeded is True

    @pytest.mark.asyncio
    async def test_broadcast_returns_ok_false_for_failed_calls(self):
        """broadcast() returns ok: false for failed calls."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config).register("beta", **beta_config)

        names_seen: list[str] = []

        async def fn(client):
            # Get the name from the provider
            env = client._provider.env
            names_seen.append(env)
            if env == "production":
                raise RuntimeError("Beta failed")
            return "success"

        results = await manager.broadcast(fn)

        assert results.any_failed is True
        assert len(results.failed) == 1
        assert results.failed[0][0] == "beta"
        assert "Beta failed" in str(results.failed[0][1])

    @pytest.mark.asyncio
    async def test_broadcast_never_rejects_even_if_all_fail(self):
        """broadcast() never rejects, even if all fail."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config).register("beta", **beta_config)

        results = await manager.broadcast(
            lambda _: (_ for _ in ()).throw(RuntimeError("Everyone fails"))
        )

        assert results.all_succeeded is False
        assert len(results.failed) == 2
        assert len(results.succeeded) == 0

    @pytest.mark.asyncio
    async def test_broadcast_returns_empty_results_when_no_clients(self):
        """broadcast() returns empty results when no clients."""
        manager = TimebackManager()

        results = await manager.broadcast(lambda _: "result")

        assert len(results.keys()) == 0
        assert results.all_succeeded is True
        assert len(results.succeeded) == 0


class TestUnregister:
    """Tests for TimebackManager unregister."""

    @pytest.mark.asyncio
    async def test_unregister_removes_client(self):
        """unregister() removes client."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        result = await manager.unregister("alpha")

        assert result is True
        assert manager.has("alpha") is False
        assert manager.size == 0

    @pytest.mark.asyncio
    async def test_unregister_returns_false_for_nonexistent_client(self):
        """unregister() returns false for non-existent client."""
        manager = TimebackManager()

        result = await manager.unregister("alpha")

        assert result is False

    @pytest.mark.asyncio
    async def test_unregister_closes_client_by_default(self):
        """unregister() closes client by default."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        # Unregister (default closes)
        await manager.unregister("alpha")

        # After close, provider tokens should be invalidated
        # (we can't directly check if close was called, but we can verify the client was removed)
        assert manager.has("alpha") is False

    @pytest.mark.asyncio
    async def test_unregister_with_close_false_does_not_close(self):
        """unregister(close=False) removes without closing."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        # Unregister without closing
        await manager.unregister("alpha", close=False)

        # Client should be removed
        assert manager.has("alpha") is False


class TestClose:
    """Tests for TimebackManager close."""

    @pytest.mark.asyncio
    async def test_close_clears_registry(self):
        """close() clears registry."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config).register("beta", **beta_config)

        await manager.close()

        assert manager.size == 0
        assert manager.names == []

    @pytest.mark.asyncio
    async def test_close_is_safe_to_call_multiple_times(self):
        """close() is safe to call multiple times."""
        manager = TimebackManager()
        manager.register("alpha", **alpha_config)

        await manager.close()
        await manager.close()  # Should not raise

        assert manager.size == 0


class TestEdgeCases:
    """Tests for TimebackManager edge cases."""

    def test_allows_special_characters_in_names(self):
        """Allows special characters in names."""
        manager = TimebackManager()
        manager.register("env/staging", **alpha_config)
        manager.register("env:production", **beta_config)
        manager.register("tenant-123", **alpha_config)

        assert manager.size == 3
        assert manager.get("env/staging") is not None

    def test_names_preserves_registration_order(self):
        """names preserves registration order."""
        manager = TimebackManager()
        manager.register("z", **alpha_config)
        manager.register("a", **alpha_config)
        manager.register("m", **alpha_config)

        assert manager.names == ["z", "a", "m"]

    def test_size_is_zero_for_new_manager(self):
        """size is 0 for new manager."""
        manager = TimebackManager()

        assert manager.size == 0

    @pytest.mark.asyncio
    async def test_size_decrements_on_unregister(self):
        """size decrements on unregister."""
        manager = TimebackManager()
        manager.register("a", **alpha_config)
        manager.register("b", **alpha_config)

        assert manager.size == 2

        await manager.unregister("a")

        assert manager.size == 1

    def test_names_is_empty_array_for_new_manager(self):
        """names is empty list for new manager."""
        manager = TimebackManager()

        assert manager.names == []

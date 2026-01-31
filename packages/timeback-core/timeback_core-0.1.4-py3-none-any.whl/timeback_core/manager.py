"""
Timeback Manager

Orchestration layer for managing multiple TimebackClient instances.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, TypeVar

from .broadcast import BroadcastResults
from .client import TimebackClient

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .types import TimebackClientConfig

T = TypeVar("T")


class TimebackManager:
    """
    Manages multiple TimebackClient instances.

    Use this when you need to:
    - Manage multiple clients with different configurations
    - Fan-out requests to multiple clients simultaneously
    - Aggregate data from multiple sources

    Example:
        ```python
        from timeback_core import TimebackManager

        manager = TimebackManager()
        manager.register("alpha", {
            "env": "production",
            "client_id": "...",
            "client_secret": "...",
        })
        manager.register("beta", {
            "env": "production",
            "client_id": "...",
            "client_secret": "...",
        })

        # Target a specific platform
        users = await manager.get("alpha").oneroster.users.list()

        # Broadcast to all platforms
        async def create_user(client):
            return await client.oneroster.users.create(user_data)

        results = await manager.broadcast(create_user)

        if results.all_succeeded:
            print("Synced to all platforms!")

        for name, user in results.succeeded:
            print(f"Created on {name}: {user}")

        for name, error in results.failed:
            print(f"Failed on {name}: {error}")

        # Cleanup
        await manager.close()
        ```
    """

    def __init__(self) -> None:
        """Create a new manager with no registered clients."""
        self._clients: dict[str, TimebackClient] = {}

    def register(
        self,
        name: str,
        config: TimebackClientConfig | None = None,
        **kwargs: Any,
    ) -> TimebackManager:
        """
        Register a new client with a given name.

        Args:
            name: Unique identifier for this client
            config: Configuration dict (env, base_url, or services mode)
            **kwargs: Alternative to config dict - pass individual args

        Returns:
            Self for method chaining

        Raises:
            ValueError: If a client with this name is already registered

        Example:
            ```python
            manager.register("alpha", env="staging", client_id="...", client_secret="...")
            # or
            manager.register("alpha", config={"env": "staging", ...})
            ```
        """
        if name in self._clients:
            raise ValueError(f'Client "{name}" is already registered')

        if config is not None:
            self._clients[name] = TimebackClient(config=config)
        else:
            self._clients[name] = TimebackClient(**kwargs)

        return self

    def get(self, name: str) -> TimebackClient:
        """
        Get a registered client by name.

        Args:
            name: The name used when registering the client

        Returns:
            The TimebackClient instance

        Raises:
            KeyError: If no client with this name is registered
        """
        if name not in self._clients:
            available = ", ".join(self._clients.keys()) or "(none)"
            raise KeyError(f'Client "{name}" is not registered. Available: {available}')

        return self._clients[name]

    def has(self, name: str) -> bool:
        """
        Check if a client with the given name is registered.

        Args:
            name: The name to check

        Returns:
            True if registered
        """
        return name in self._clients

    @property
    def names(self) -> list[str]:
        """Get all registered client names."""
        return list(self._clients.keys())

    @property
    def size(self) -> int:
        """Get the number of registered clients."""
        return len(self._clients)

    async def broadcast(
        self,
        fn: Callable[[TimebackClient], T | Awaitable[T]],
    ) -> BroadcastResults[T]:
        """
        Execute a function on all registered clients.

        Uses asyncio.gather with return_exceptions=True semantics —
        always completes, never raises. Each result indicates success
        or failure per client.

        All operations run in parallel.

        Args:
            fn: Async function to execute on each client

        Returns:
            BroadcastResults with typed property access and convenience methods

        Example:
            ```python
            async def get_users(client):
                return await client.oneroster.users.list()

            results = await manager.broadcast(get_users)

            if results.all_succeeded:
                all_users = results.values()

            for name, users in results.succeeded:
                print(f"{name}: {len(users)} users")
            ```
        """
        results_dict: dict[str, dict[str, Any]] = {}

        async def execute(name: str, client: TimebackClient) -> tuple[str, dict[str, Any]]:
            try:
                result = fn(client)
                # Handle both sync and async functions
                if asyncio.iscoroutine(result):
                    value = await result
                else:
                    value = result
                return name, {"ok": True, "value": value}
            except Exception as e:
                return name, {"ok": False, "error": e}

        # Execute all in parallel
        tasks = [execute(name, client) for name, client in self._clients.items()]
        completed = await asyncio.gather(*tasks)

        for name, result in completed:
            results_dict[name] = result

        return BroadcastResults(_results=results_dict)

    async def unregister(self, name: str, *, close: bool = True) -> bool:
        """
        Unregister a client by name.

        By default closes the client before removing.

        Args:
            name: The name of the client to remove
            close: If True (default), close the client before removing.
                   Set to False to just remove without closing.

        Returns:
            True if the client was removed, False if it didn't exist

        Example:
            ```python
            # Close and remove (default)
            await manager.unregister("alpha")

            # Just remove without closing (backward compat)
            await manager.unregister("alpha", close=False)
            ```
        """
        if name not in self._clients:
            return False

        if close:
            client = self._clients[name]
            await client.close()

        del self._clients[name]
        return True

    async def close(self) -> None:
        """
        Close all registered clients and clear the registry.

        Call this during application shutdown to release resources.
        """
        for client in self._clients.values():
            await client.close()

        self._clients.clear()


__all__ = ["TimebackManager"]

"""
Broadcast Results

Helper class for working with broadcast operation results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterator

T = TypeVar("T")


@dataclass
class BroadcastResults[T]:
    """
    Results from a broadcast operation across multiple clients.

    Provides both direct access by name and convenience methods for
    aggregating results.

    Example:
        ```python
        results = await manager.broadcast(lambda c: c.oneroster.users.list())

        # Direct access
        if results["alpha"].ok:
            print(results["alpha"].value)

        # Convenience methods
        if results.all_succeeded:
            print("All platforms synced!")

        for name, users in results.succeeded:
            print(f"Got {len(users)} users from {name}")

        for name, error in results.failed:
            print(f"Failed on {name}: {error}")
        ```
    """

    _results: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __getitem__(self, name: str) -> dict[str, Any]:
        """Get result for a specific client by name."""
        if name not in self._results:
            available = ", ".join(self._results.keys()) or "(none)"
            raise KeyError(f"No result for '{name}'. Available: {available}")
        return self._results[name]

    def __contains__(self, name: str) -> bool:
        """Check if a result exists for the given name."""
        return name in self._results

    def __iter__(self) -> Iterator[str]:
        """Iterate over client names."""
        return iter(self._results)

    def __len__(self) -> int:
        """Number of results."""
        return len(self._results)

    def keys(self) -> list[str]:
        """Get all client names."""
        return list(self._results.keys())

    def items(self) -> list[tuple[str, dict[str, Any]]]:
        """Get all (name, result) pairs."""
        return list[tuple[str, dict[str, Any]]](self._results.items())

    @property
    def succeeded(self) -> list[tuple[str, T]]:
        """
        Get all successful results as (name, value) tuples.

        Returns:
            List of (client_name, value) for successful operations
        """
        return [
            (name, result["value"])
            for name, result in self._results.items()
            if result.get("ok") is True
        ]

    @property
    def failed(self) -> list[tuple[str, Exception]]:
        """
        Get all failed results as (name, error) tuples.

        Returns:
            List of (client_name, error) for failed operations
        """
        return [
            (name, result["error"])
            for name, result in self._results.items()
            if result.get("ok") is False
        ]

    @property
    def all_succeeded(self) -> bool:
        """True if all operations succeeded."""
        return all(result.get("ok") is True for result in self._results.values())

    @property
    def any_failed(self) -> bool:
        """True if any operation failed."""
        return any(result.get("ok") is False for result in self._results.values())

    def values(self) -> list[T]:
        """
        Get all successful values.

        Raises:
            RuntimeError: If any operation failed

        Returns:
            List of all values from successful operations
        """
        if self.any_failed:
            failed_names = ", ".join(name for name, _ in self.failed)
            raise RuntimeError(f"Cannot get values: operations failed for: {failed_names}")
        return [value for _, value in self.succeeded]


__all__ = ["BroadcastResults"]

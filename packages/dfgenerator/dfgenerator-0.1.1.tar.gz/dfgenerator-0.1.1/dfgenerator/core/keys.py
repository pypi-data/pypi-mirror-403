"""Key management for primary and foreign key relationships."""

from __future__ import annotations

from typing import Any, Callable, Dict, List


class KeyRegistry:
    """
    Registry that stores generated key values so other datasets can reference them.

    Keys are deterministic: the nth key for a keyspace always comes from index ``n``
    of the provided factory. Foreign keys reuse existing values in a round-robin
    manner to avoid randomness while ensuring referential integrity.
    """

    def __init__(self):
        self._values: Dict[str, List[Any]] = {}
        self._factories: Dict[str, Callable[[int], Any]] = {}

    def clear(self) -> None:
        """Reset all stored keyspaces (useful in tests)."""

        self._values.clear()
        self._factories.clear()

    def _ensure_factory(self, name: str, factory: Callable[[int], Any]) -> None:
        if name in self._factories and self._factories[name] is not factory:
            # Different factory requested for the same keyspace; prefer first.
            return
        self._factories.setdefault(name, factory)
        self._values.setdefault(name, [])

    def next(self, name: str, factory: Callable[[int], Any]) -> Any:
        """Create and store the next primary key value for a keyspace."""

        self._ensure_factory(name, factory)
        values = self._values[name]
        value = factory(len(values))
        values.append(value)
        return value

    def sample(self, name: str, index: int) -> Any:
        """
        Deterministically reuse an existing key for the given keyspace.

        Raises a ValueError if no keys exist yet.
        """

        values = self._values.get(name) or []
        if not values:
            raise ValueError(f"No keys available yet for keyspace '{name}'")
        return values[index % len(values)]


# Default registry shared across convenience helpers; tests may create their own.
default_registry = KeyRegistry()


def primary_key(
    keyspace: str,
    factory: Callable[[int], Any],
    *,
    registry: KeyRegistry = default_registry,
) -> Callable[[int], Any]:
    """
    Produce unique values for a keyspace and record them for later reuse.
    """

    def value(_: int) -> Any:
        return registry.next(keyspace, factory)

    return value


def foreign_key(keyspace: str, *, registry: KeyRegistry = default_registry) -> Callable[[int], Any]:
    """
    Reuse existing values from a keyspace in a deterministic round-robin fashion.
    """

    def value(index: int) -> Any:
        return registry.sample(keyspace, index)

    return value


__all__ = ["KeyRegistry", "primary_key", "foreign_key", "default_registry"]

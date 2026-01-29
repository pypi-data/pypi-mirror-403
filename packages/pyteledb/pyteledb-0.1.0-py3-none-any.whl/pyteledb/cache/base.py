"""Abstract cache interface for pyteledb.

Defines the contract for all cache implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """
    A cached value with metadata.

    Attributes:
        key: Cache key.
        value: Cached value.
        created_at: Monotonic timestamp when cached.
        ttl: Time-to-live in seconds.
        hits: Number of times this entry was accessed.
    """

    key: str
    value: T
    created_at: float
    ttl: float
    hits: int = 0


class BaseCache(ABC):
    """
    Abstract base class for cache implementations.

    All cache implementations must inherit from this and implement
    the abstract methods. Caches are async-first for consistency
    with the rest of pyteledb.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """
        Get a value from the cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        ...

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (None = use default).
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key.

        Returns:
            True if the key existed and was deleted.
        """
        ...

    @abstractmethod
    async def clear(self) -> int:
        """
        Clear all values from the cache.

        Returns:
            Number of entries cleared.
        """
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key.

        Returns:
            True if key exists and is not expired.
        """
        ...

    async def get_or_set(
        self,
        key: str,
        factory: Any,
        ttl: float | None = None,
    ) -> Any:
        """
        Get a value, or set it using the factory if not present.

        Args:
            key: Cache key.
            factory: Callable or coroutine to produce the value.
            ttl: Time-to-live in seconds.

        Returns:
            The cached or newly set value.
        """
        value = await self.get(key)
        if value is not None:
            return value

        # Call factory (handle both sync and async)
        if callable(factory):
            import asyncio

            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
        else:
            value = factory

        await self.set(key, value, ttl)
        return value

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from the cache.

        Args:
            keys: List of cache keys.

        Returns:
            Dictionary of key -> value for found entries.
        """
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: float | None = None,
    ) -> None:
        """
        Set multiple values in the cache.

        Args:
            items: Dictionary of key -> value.
            ttl: Time-to-live in seconds.
        """
        for key, value in items.items():
            await self.set(key, value, ttl)

    async def delete_many(self, keys: list[str]) -> int:
        """
        Delete multiple keys from the cache.

        Args:
            keys: List of cache keys.

        Returns:
            Number of keys deleted.
        """
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count

    @abstractmethod
    async def stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats (size, hits, misses, etc.).
        """
        ...

    async def close(self) -> None:  # noqa: B027
        """
        Close the cache and release resources.

        Override in implementations that need cleanup.
        """
        pass

    async def __aenter__(self) -> BaseCache:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Async context manager exit."""
        await self.close()

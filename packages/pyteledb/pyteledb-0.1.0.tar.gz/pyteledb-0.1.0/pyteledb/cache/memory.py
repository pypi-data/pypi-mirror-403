"""In-memory cache implementation with TTL and LRU eviction."""

from __future__ import annotations

import asyncio
import contextlib
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from pyteledb.cache.base import BaseCache, CacheEntry
from pyteledb.utils.time import monotonic_timestamp, ttl_expired


@dataclass
class MemoryCacheConfig:
    """Configuration for MemoryCache."""

    default_ttl: float = 300.0  # 5 minutes
    max_size: int = 1000  # Maximum number of entries
    cleanup_interval: float = 60.0  # Seconds between cleanup runs


@dataclass
class CacheStats:
    """Statistics for cache operations."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    expirations: int = 0


class MemoryCache(BaseCache):
    """
    In-memory cache with TTL expiration and LRU eviction.

    Thread-safe through asyncio locks. Uses OrderedDict for
    efficient LRU ordering.
    """

    def __init__(self, config: MemoryCacheConfig | None = None) -> None:
        """
        Initialize the memory cache.

        Args:
            config: Cache configuration (uses defaults if None).
        """
        self.config = config or MemoryCacheConfig()
        self._cache: OrderedDict[str, CacheEntry[Any]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = CacheStats()
        self._cleanup_task: asyncio.Task[None] | None = None

    async def start_cleanup(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task
            self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """Background loop to clean expired entries."""
        while True:
            await asyncio.sleep(self.config.cleanup_interval)
            await self._cleanup_expired()

    async def _cleanup_expired(self) -> int:
        """Remove all expired entries."""
        expired_keys: list[str] = []

        async with self._lock:
            for key, entry in self._cache.items():
                if ttl_expired(entry.created_at, entry.ttl):
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                self._stats.expirations += 1

        return len(expired_keys)

    def _evict_lru(self) -> None:
        """Evict the least recently used entry (must hold lock)."""
        if self._cache:
            self._cache.popitem(last=False)
            self._stats.evictions += 1

    async def get(self, key: str) -> Any | None:
        """Get a value from the cache."""
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                return None

            # Check expiration
            if ttl_expired(entry.created_at, entry.ttl):
                del self._cache[key]
                self._stats.expirations += 1
                self._stats.misses += 1
                return None

            # Update LRU order and hit count
            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats.hits += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        """Set a value in the cache."""
        async with self._lock:
            # Evict if at capacity and key is new
            if key not in self._cache and len(self._cache) >= self.config.max_size:
                self._evict_lru()

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=monotonic_timestamp(),
                ttl=ttl if ttl is not None else self.config.default_ttl,
            )
            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._stats.sets += 1

    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.deletes += 1
                return True
            return False

    async def clear(self) -> int:
        """Clear all values from the cache."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if ttl_expired(entry.created_at, entry.ttl):
                del self._cache[key]
                self._stats.expirations += 1
                return False
            return True

    async def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._stats.hits + self._stats.misses
            hit_rate = self._stats.hits / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.config.max_size,
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "hit_rate": hit_rate,
                "sets": self._stats.sets,
                "deletes": self._stats.deletes,
                "evictions": self._stats.evictions,
                "expirations": self._stats.expirations,
            }

    async def close(self) -> None:
        """Close the cache and stop cleanup."""
        await self.stop_cleanup()
        await self.clear()

    def size(self) -> int:
        """Get the current cache size (sync, for convenience)."""
        return len(self._cache)

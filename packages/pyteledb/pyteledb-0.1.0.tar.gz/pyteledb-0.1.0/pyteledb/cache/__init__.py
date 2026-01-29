"""Cache layer for ephemeral local acceleration."""

from pyteledb.cache.base import BaseCache, CacheEntry
from pyteledb.cache.memory import MemoryCache

__all__ = [
    "BaseCache",
    "CacheEntry",
    "MemoryCache",
]


def get_sqlite_cache() -> type:
    """Get SQLiteCache class if aiosqlite is available."""
    from pyteledb.cache.sqlite import SQLiteCache

    return SQLiteCache

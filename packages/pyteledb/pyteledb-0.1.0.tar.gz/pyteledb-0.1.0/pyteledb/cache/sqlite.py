"""SQLite-backed cache for persistent local caching.

Requires optional dependency: pip install pyteledb[sqlite]
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import aiosqlite
except ImportError as e:
    raise ImportError(
        "SQLite cache requires aiosqlite. Install with: pip install pyteledb[sqlite]"
    ) from e

from pyteledb.cache.base import BaseCache
from pyteledb.utils.time import utc_timestamp


@dataclass
class SQLiteCacheConfig:
    """Configuration for SQLiteCache."""

    db_path: str | Path = ":memory:"
    default_ttl: float = 3600.0  # 1 hour
    table_name: str = "pyteledb_cache"


class SQLiteCache(BaseCache):
    """
    SQLite-backed cache with persistent storage.

    Unlike MemoryCache, this survives process restarts.
    Useful for larger cache capacities or when persistence is desired.
    """

    def __init__(self, config: SQLiteCacheConfig | None = None) -> None:
        """
        Initialize the SQLite cache.

        Args:
            config: Cache configuration (uses defaults if None).
        """
        self.config = config or SQLiteCacheConfig()
        self._db: aiosqlite.Connection | None = None
        self._initialized = False
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

    async def _ensure_initialized(self) -> aiosqlite.Connection:
        """Ensure database is connected and table exists."""
        if self._db is None:
            self._db = await aiosqlite.connect(self.config.db_path)
            await self._db.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config.table_name} (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            await self._db.execute(
                f"CREATE INDEX IF NOT EXISTS idx_expires ON {self.config.table_name}(expires_at)"
            )
            await self._db.commit()
            self._initialized = True
        return self._db

    async def get(self, key: str) -> Any | None:
        """Get a value from the cache."""
        db = await self._ensure_initialized()
        now = utc_timestamp()

        async with db.execute(
            f"""
            SELECT value FROM {self.config.table_name}
            WHERE key = ? AND expires_at > ?
            """,
            (key, now),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            self._stats["misses"] += 1
            return None

        self._stats["hits"] += 1
        return json.loads(row[0])

    async def set(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        """Set a value in the cache."""
        db = await self._ensure_initialized()
        now = utc_timestamp()
        ttl = ttl if ttl is not None else self.config.default_ttl
        expires_at = now + ttl

        await db.execute(
            f"""
            INSERT OR REPLACE INTO {self.config.table_name}
            (key, value, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (key, json.dumps(value), now, expires_at),
        )
        await db.commit()
        self._stats["sets"] += 1

    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        db = await self._ensure_initialized()

        cursor = await db.execute(
            f"DELETE FROM {self.config.table_name} WHERE key = ?",
            (key,),
        )
        await db.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            self._stats["deletes"] += 1
        return deleted

    async def clear(self) -> int:
        """Clear all values from the cache."""
        db = await self._ensure_initialized()

        async with db.execute(f"SELECT COUNT(*) FROM {self.config.table_name}") as cursor:
            row = await cursor.fetchone()
            count = row[0] if row else 0

        await db.execute(f"DELETE FROM {self.config.table_name}")
        await db.commit()
        return count

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        db = await self._ensure_initialized()
        now = utc_timestamp()

        async with db.execute(
            f"""
            SELECT 1 FROM {self.config.table_name}
            WHERE key = ? AND expires_at > ?
            """,
            (key, now),
        ) as cursor:
            row = await cursor.fetchone()

        return row is not None

    async def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        db = await self._ensure_initialized()
        now = utc_timestamp()

        cursor = await db.execute(
            f"DELETE FROM {self.config.table_name} WHERE expires_at <= ?",
            (now,),
        )
        await db.commit()
        return cursor.rowcount

    async def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        db = await self._ensure_initialized()
        now = utc_timestamp()

        async with db.execute(
            f"SELECT COUNT(*) FROM {self.config.table_name} WHERE expires_at > ?",
            (now,),
        ) as cursor:
            row = await cursor.fetchone()
            size = row[0] if row else 0

        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

        return {
            "size": size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": hit_rate,
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "db_path": str(self.config.db_path),
        }

    async def close(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            await self._db.close()
            self._db = None
            self._initialized = False

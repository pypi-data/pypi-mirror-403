"""Main TelegramDatabase class.

The primary user-facing abstraction for Telegram-native persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyteledb.cache.base import BaseCache
from pyteledb.cache.memory import MemoryCache
from pyteledb.core.locks import LockContext, LockManager
from pyteledb.core.pointers import Pointer
from pyteledb.core.record import Record
from pyteledb.core.root import RootIndex, parse_root_text
from pyteledb.exceptions import (
    DatabaseNotInitializedError,
    RecordNotFoundError,
)
from pyteledb.storage.serializer import serialize
from pyteledb.storage.versioning import check_version
from pyteledb.telegram.client import ClientConfig, TelegramClient
from pyteledb.telegram.messages import MessageManager
from pyteledb.telegram.pins import PinManager
from pyteledb.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Configuration for TelegramDatabase."""

    # Telegram settings
    bot_token: str
    chat_id: int | str

    # Database settings
    db_name: str = "pyteledb"

    # Cache settings
    cache_enabled: bool = True
    cache_ttl: float = 300.0  # 5 minutes
    cache_max_size: int = 1000

    # Write settings
    use_locking: bool = True
    lock_ttl: float = 30.0


class TelegramDatabase:
    """
    Telegram-native embedded database.

    Uses a Telegram channel or group as the persistence layer.
    Records are stored as messages, with a pinned message as the root index.

    Example:
        ```python
        async with TelegramDatabase(config) as db:
            await db.initialize()
            record = await db.insert({"name": "Alice", "age": 30})
            fetched = await db.get(record.id)
        ```
    """

    def __init__(
        self,
        config: DatabaseConfig,
        cache: BaseCache | None = None,
    ) -> None:
        """
        Initialize the database.

        Args:
            config: Database configuration.
            cache: Optional cache instance (uses MemoryCache if not provided).
        """
        self.config = config

        # Telegram client
        client_config = ClientConfig(token=config.bot_token)
        self._client = TelegramClient(client_config)
        self._messages = MessageManager(self._client, config.chat_id)
        self._pins = PinManager(self._client, config.chat_id)

        # Lock manager
        self._locks = LockManager(self._client, config.chat_id)

        # Cache
        if config.cache_enabled:
            from pyteledb.cache.memory import MemoryCacheConfig

            self._cache: BaseCache | None = cache or MemoryCache(
                MemoryCacheConfig(
                    default_ttl=config.cache_ttl,
                    max_size=config.cache_max_size,
                )
            )
        else:
            self._cache = None

        # Root index
        self._root: RootIndex | None = None
        self._initialized = False

    async def __aenter__(self) -> TelegramDatabase:
        """Async context manager entry."""
        await self._client._ensure_client()
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the database and release resources."""
        if self._cache:
            await self._cache.close()
        await self._client.close()

    # =========================================================================
    # Initialization
    # =========================================================================

    async def initialize(self, force: bool = False) -> RootIndex:
        """
        Initialize the database.

        Creates the root index if it doesn't exist.

        Args:
            force: Overwrite existing root index.

        Returns:
            The root index.

        Raises:
            DatabaseAlreadyExistsError: If database exists and force=False.
        """
        # Check for existing root
        existing = await self._load_root()
        if existing:
            if not force:
                self._root = existing
                self._initialized = True
                logger.info(f"Loaded existing database: {existing.db_name}")
                return existing
            # Force reinitialize
            logger.warning("Reinitializing database (force=True)")

        # Create new root
        self._root = RootIndex.create(self.config.db_name)

        # Save as pinned message
        root_text = serialize(self._root.to_dict())
        message_id = await self._pins.create_and_pin(root_text)
        self._root.message_id = message_id

        # Update with message ID
        root_text = serialize(self._root.to_dict())
        await self._pins.update_pinned(root_text, message_id)

        self._initialized = True
        logger.info(f"Created new database: {self._root.db_name}")
        return self._root

    async def _load_root(self) -> RootIndex | None:
        """Load the root index from the pinned message."""
        text = await self._pins.get_pinned_text()
        if text:
            return parse_root_text(text)
        return None

    async def _save_root(self) -> None:
        """Save the root index to the pinned message."""
        if not self._root:
            raise DatabaseNotInitializedError("Database not initialized")

        self._root = self._root.next_version()
        root_text = serialize(self._root.to_dict())
        await self._pins.update_pinned(root_text, self._root.message_id)

    def _ensure_initialized(self) -> None:
        """Ensure database is initialized."""
        if not self._initialized or not self._root:
            raise DatabaseNotInitializedError("Database not initialized. Call initialize() first.")

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def insert(
        self,
        data: dict[str, Any],
        *,
        record_id: str | None = None,
        tags: list[str] | None = None,
    ) -> Record:
        """
        Insert a new record.

        Args:
            data: Record payload.
            record_id: Custom record ID (auto-generated if None).
            tags: Optional tags.

        Returns:
            The created record.
        """
        self._ensure_initialized()

        # Create record
        record = Record.create(data, record_id=record_id, tags=tags)

        # Use locking if enabled
        if self.config.use_locking:
            async with LockContext(self._locks, "write", self.config.lock_ttl):
                return await self._do_insert(record)
        else:
            return await self._do_insert(record)

    async def _do_insert(self, record: Record) -> Record:
        """Perform the actual insert."""
        assert self._root is not None

        # Send message with record data
        record_text = serialize(record.to_dict())
        msg = await self._messages.send(record_text)
        record.metadata.message_id = msg.message_id

        # Update pointers - append to tail
        if self._root.main_chain.tail:
            # Link to existing tail
            record.metadata.prev_id = self._root.main_chain.tail.record_id
            # TODO: Update the tail record's next pointer
            # This requires editing the tail message

        # Update root
        if self._root.main_chain.head is None:
            self._root.main_chain.head = Pointer(
                record_id=record.id,
                message_id=record.message_id,
            )

        self._root.main_chain.tail = Pointer(
            record_id=record.id,
            message_id=record.message_id,
        )
        self._root.main_chain.length += 1
        self._root.record_count += 1

        await self._save_root()

        # Cache the record
        if self._cache:
            await self._cache.set(
                f"record:{record.id}",
                record.to_dict(),
                self.config.cache_ttl,
            )

        logger.debug(f"Inserted record {record.id}")
        return record

    async def get(self, record_id: str) -> Record:
        """
        Get a record by ID.

        Args:
            record_id: Record ID to fetch.

        Returns:
            The record.

        Raises:
            RecordNotFoundError: If record not found.
        """
        self._ensure_initialized()

        # Check cache first
        if self._cache:
            cached = await self._cache.get(f"record:{record_id}")
            if cached:
                return Record.from_dict(cached)

        # TODO: Implement message lookup
        # This requires either:
        # 1. Scanning from head/tail following pointers
        # 2. Storing a message_id index in the root

        raise RecordNotFoundError(
            f"Record {record_id} not found",
            record_id=record_id,
        )

    async def update(
        self,
        record_id: str,
        data: dict[str, Any],
        *,
        expected_version: int | None = None,
    ) -> Record:
        """
        Update a record.

        Args:
            record_id: Record ID to update.
            data: New payload data.
            expected_version: Expected version for optimistic locking.

        Returns:
            The updated record.

        Raises:
            RecordNotFoundError: If record not found.
            VersionConflictError: If version mismatch.
        """
        self._ensure_initialized()

        # Fetch current record
        record = await self.get(record_id)

        # Check version if specified
        if expected_version is not None:
            check_version(expected_version, record.version, record_id)

        # Create new version
        updated = record.next_version()
        updated.payload = data
        updated.update_checksum()

        # Use locking if enabled
        if self.config.use_locking:
            async with LockContext(self._locks, f"record:{record_id}", self.config.lock_ttl):
                return await self._do_update(updated)
        else:
            return await self._do_update(updated)

    async def _do_update(self, record: Record) -> Record:
        """Perform the actual update."""
        if record.message_id is None:
            raise RecordNotFoundError(
                f"Record {record.id} has no message_id",
                record_id=record.id,
            )

        # Edit the message
        record_text = serialize(record.to_dict())
        await self._messages.edit(record.message_id, record_text)

        # Update cache
        if self._cache:
            await self._cache.set(
                f"record:{record.id}",
                record.to_dict(),
                self.config.cache_ttl,
            )

        logger.debug(f"Updated record {record.id} to version {record.version}")
        return record

    async def delete(self, record_id: str) -> bool:
        """
        Delete a record.

        Args:
            record_id: Record ID to delete.

        Returns:
            True if deleted.

        Raises:
            RecordNotFoundError: If record not found.
        """
        self._ensure_initialized()

        record = await self.get(record_id)

        if self.config.use_locking:
            async with LockContext(self._locks, f"record:{record_id}", self.config.lock_ttl):
                return await self._do_delete(record)
        else:
            return await self._do_delete(record)

    async def _do_delete(self, record: Record) -> bool:
        """Perform the actual delete."""
        assert self._root is not None

        if record.message_id is None:
            raise RecordNotFoundError(
                f"Record {record.id} has no message_id",
                record_id=record.id,
            )

        # Delete the message
        await self._messages.delete(record.message_id)

        # Update pointers
        # TODO: Relink prev/next records

        # Update root
        self._root.record_count -= 1
        self._root.main_chain.length -= 1

        if self._root.main_chain.head and self._root.main_chain.head.record_id == record.id:
            # Deleted head - update to next
            self._root.main_chain.head = (
                Pointer(record_id=record.metadata.next_id) if record.metadata.next_id else None
            )

        if self._root.main_chain.tail and self._root.main_chain.tail.record_id == record.id:
            # Deleted tail - update to prev
            self._root.main_chain.tail = (
                Pointer(record_id=record.metadata.prev_id) if record.metadata.prev_id else None
            )

        await self._save_root()

        # Remove from cache
        if self._cache:
            await self._cache.delete(f"record:{record.id}")

        logger.debug(f"Deleted record {record.id}")
        return True

    # =========================================================================
    # Query Operations
    # =========================================================================

    async def count(self) -> int:
        """Get the total number of records."""
        self._ensure_initialized()
        assert self._root is not None
        return self._root.record_count

    async def exists(self, record_id: str) -> bool:
        """Check if a record exists."""
        try:
            await self.get(record_id)
            return True
        except RecordNotFoundError:
            return False

    # =========================================================================
    # Database Info
    # =========================================================================

    async def info(self) -> dict[str, Any]:
        """Get database information."""
        self._ensure_initialized()
        assert self._root is not None

        cache_stats = {}
        if self._cache:
            cache_stats = await self._cache.stats()

        return {
            **self._root.stats(),
            "cache": cache_stats,
            "config": {
                "chat_id": self.config.chat_id,
                "cache_enabled": self.config.cache_enabled,
                "locking_enabled": self.config.use_locking,
            },
        }

    @property
    def name(self) -> str:
        """Get the database name."""
        return self._root.db_name if self._root else self.config.db_name

    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return self._initialized

    @property
    def record_count(self) -> int:
        """Get the record count (0 if not initialized)."""
        return self._root.record_count if self._root else 0

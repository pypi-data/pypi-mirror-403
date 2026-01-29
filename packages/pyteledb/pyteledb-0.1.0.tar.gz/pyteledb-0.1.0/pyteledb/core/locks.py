"""Soft locking for write coordination.

Telegram provides no transactions, so we use soft locks
for write coordination and conflict prevention.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyteledb.exceptions import LockError, LockTimeoutError
from pyteledb.utils.ids import generate_short_id
from pyteledb.utils.logging import get_logger
from pyteledb.utils.time import monotonic_timestamp, utc_timestamp

if TYPE_CHECKING:
    from pyteledb.telegram.client import TelegramClient

logger = get_logger(__name__)


@dataclass
class Lock:
    """
    A soft lock for write coordination.

    Attributes:
        lock_id: Unique lock identifier.
        resource_id: Resource being locked.
        holder_id: Identifier of the lock holder.
        acquired_at: When the lock was acquired.
        expires_at: When the lock expires (auto-release).
        message_id: Telegram message ID storing the lock.
    """

    lock_id: str
    resource_id: str
    holder_id: str
    acquired_at: float
    expires_at: float
    message_id: int | None = None

    @classmethod
    def create(
        cls,
        resource_id: str,
        holder_id: str,
        ttl_seconds: float = 30.0,
    ) -> Lock:
        """Create a new lock."""
        now = utc_timestamp()
        return cls(
            lock_id=generate_short_id(12),
            resource_id=resource_id,
            holder_id=holder_id,
            acquired_at=now,
            expires_at=now + ttl_seconds,
        )

    def is_expired(self) -> bool:
        """Check if the lock has expired."""
        return utc_timestamp() > self.expires_at

    def remaining_seconds(self) -> float:
        """Get remaining time until expiry."""
        return max(0, self.expires_at - utc_timestamp())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "lid": self.lock_id,
            "res": self.resource_id,
            "holder": self.holder_id,
            "acq": self.acquired_at,
            "exp": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Lock:
        """Create from dictionary."""
        return cls(
            lock_id=data["lid"],
            resource_id=data["res"],
            holder_id=data["holder"],
            acquired_at=data["acq"],
            expires_at=data["exp"],
        )


class LockManager:
    """
    Manages soft locks via Telegram messages.

    Locks are stored as temporary messages that get edited
    or deleted on release.
    """

    def __init__(
        self,
        client: TelegramClient,
        chat_id: int | str,
        holder_id: str | None = None,
    ) -> None:
        """
        Initialize the lock manager.

        Args:
            client: Telegram client.
            chat_id: Chat ID for lock storage.
            holder_id: Identifier for this lock holder.
        """
        self.client = client
        self.chat_id = chat_id
        self.holder_id = holder_id or generate_short_id(8)
        self._local_locks: dict[str, Lock] = {}
        self._lock = asyncio.Lock()

    async def acquire(
        self,
        resource_id: str,
        ttl_seconds: float = 30.0,
        timeout_seconds: float | None = None,
        retry_delay: float = 0.5,
    ) -> Lock:
        """
        Acquire a lock on a resource.

        Args:
            resource_id: Resource to lock.
            ttl_seconds: Lock duration.
            timeout_seconds: Maximum time to wait for lock.
            retry_delay: Delay between retry attempts.

        Returns:
            The acquired lock.

        Raises:
            LockTimeoutError: If timeout exceeded.
            LockError: If lock acquisition fails.
        """
        start = monotonic_timestamp()

        while True:
            async with self._lock:
                # Check for existing lock
                existing = self._local_locks.get(resource_id)
                if existing and not existing.is_expired():
                    if existing.holder_id == self.holder_id:
                        # We already hold this lock, refresh it
                        return await self._refresh_lock(existing, ttl_seconds)
                    # Someone else holds it
                elif existing and existing.is_expired():
                    # Stale lock, clean it up
                    await self._release_lock(existing)

                # Try to acquire
                try:
                    lock = await self._create_lock(resource_id, ttl_seconds)
                    self._local_locks[resource_id] = lock
                    logger.debug(f"Acquired lock on {resource_id}: {lock.lock_id}")
                    return lock
                except LockError:
                    pass  # Someone beat us to it

            # Check timeout
            if timeout_seconds is not None:
                elapsed = monotonic_timestamp() - start
                if elapsed > timeout_seconds:
                    raise LockTimeoutError(
                        f"Timeout acquiring lock on {resource_id}",
                        details={"resource_id": resource_id, "timeout": timeout_seconds},
                    )

            await asyncio.sleep(retry_delay)

    async def release(self, lock: Lock) -> bool:
        """
        Release a lock.

        Args:
            lock: The lock to release.

        Returns:
            True if released successfully.
        """
        async with self._lock:
            if lock.resource_id in self._local_locks:
                del self._local_locks[lock.resource_id]
            return await self._release_lock(lock)

    async def release_by_resource(self, resource_id: str) -> bool:
        """
        Release a lock by resource ID.

        Args:
            resource_id: Resource to unlock.

        Returns:
            True if released, False if not held.
        """
        async with self._lock:
            lock = self._local_locks.pop(resource_id, None)
            if lock:
                return await self._release_lock(lock)
            return False

    async def _create_lock(
        self,
        resource_id: str,
        ttl_seconds: float,
    ) -> Lock:
        """Create a lock via Telegram message."""
        import json

        lock = Lock.create(resource_id, self.holder_id, ttl_seconds)
        lock_text = f"🔒 {json.dumps(lock.to_dict())}"

        result = await self.client.send_message(
            self.chat_id,
            lock_text,
            disable_notification=True,
        )
        lock.message_id = result["message_id"]
        return lock

    async def _release_lock(self, lock: Lock) -> bool:
        """Release a lock by deleting its message."""
        if lock.message_id:
            try:
                await self.client.delete_message(self.chat_id, lock.message_id)
                logger.debug(f"Released lock {lock.lock_id}")
                return True
            except Exception as e:
                logger.warning(f"Failed to release lock {lock.lock_id}: {e}")
        return False

    async def _refresh_lock(self, lock: Lock, ttl_seconds: float) -> Lock:
        """Refresh an existing lock."""
        import json

        lock.expires_at = utc_timestamp() + ttl_seconds
        lock_text = f"🔒 {json.dumps(lock.to_dict())}"

        if lock.message_id:
            await self.client.edit_message_text(
                self.chat_id,
                lock.message_id,
                lock_text,
            )
        return lock

    async def check_stale_locks(self, max_age_seconds: float = 300.0) -> list[Lock]:
        """
        Find stale locks that may need cleanup.

        Args:
            max_age_seconds: Consider locks older than this stale.

        Returns:
            List of potentially stale locks.
        """
        stale: list[Lock] = []
        now = utc_timestamp()

        async with self._lock:
            for lock in self._local_locks.values():
                if now - lock.acquired_at > max_age_seconds:
                    stale.append(lock)

        return stale

    def held_locks(self) -> list[str]:
        """Get list of resources we currently hold locks on."""
        return list(self._local_locks.keys())


class LockContext:
    """Context manager for lock acquisition/release."""

    def __init__(
        self,
        manager: LockManager,
        resource_id: str,
        ttl_seconds: float = 30.0,
        timeout_seconds: float | None = None,
    ) -> None:
        self._manager = manager
        self._resource_id = resource_id
        self._ttl = ttl_seconds
        self._timeout = timeout_seconds
        self._lock: Lock | None = None

    async def __aenter__(self) -> Lock:
        self._lock = await self._manager.acquire(
            self._resource_id,
            ttl_seconds=self._ttl,
            timeout_seconds=self._timeout,
        )
        return self._lock

    async def __aexit__(self, *_: Any) -> None:
        if self._lock:
            await self._manager.release(self._lock)

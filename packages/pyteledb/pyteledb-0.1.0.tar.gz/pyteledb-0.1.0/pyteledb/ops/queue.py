"""Write queue management for ordered, reliable writes.

Provides ordered batching and retry queue for failed operations.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from pyteledb.utils.logging import get_logger
from pyteledb.utils.time import monotonic_timestamp

logger = get_logger(__name__)


class WriteStatus(Enum):
    """Status of a write operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WriteOperation:
    """
    A queued write operation.

    Attributes:
        id: Unique operation ID.
        operation: The async callable to execute.
        args: Arguments to pass to the operation.
        kwargs: Keyword arguments to pass.
        status: Current status.
        attempts: Number of execution attempts.
        max_retries: Maximum retry attempts.
        created_at: When the operation was queued.
        error: Last error if failed.
    """

    id: str
    operation: Callable[..., Awaitable[Any]]
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    status: WriteStatus = WriteStatus.PENDING
    attempts: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=monotonic_timestamp)
    error: Exception | None = None
    result: Any = None

    @classmethod
    def create(
        cls,
        operation: Callable[..., Awaitable[Any]],
        *args: Any,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> WriteOperation:
        """Create a new write operation."""
        return cls(
            id=uuid4().hex[:16],
            operation=operation,
            args=args,
            kwargs=kwargs,
            max_retries=max_retries,
        )


@dataclass
class QueueConfig:
    """Configuration for WriteQueue."""

    max_size: int = 1000
    batch_size: int = 10
    batch_delay: float = 0.1  # Seconds between batches
    retry_delay: float = 1.0  # Base retry delay


class WriteQueue:
    """
    Ordered write queue with batching and retry support.

    Ensures writes are executed in order, with automatic
    retry for transient failures.
    """

    def __init__(self, config: QueueConfig | None = None) -> None:
        """
        Initialize the write queue.

        Args:
            config: Queue configuration.
        """
        self.config = config or QueueConfig()
        self._queue: asyncio.Queue[WriteOperation] = asyncio.Queue(maxsize=self.config.max_size)
        self._retry_queue: asyncio.Queue[WriteOperation] = asyncio.Queue()
        self._processing = False
        self._processor_task: asyncio.Task[None] | None = None
        self._pending: dict[str, WriteOperation] = {}

    async def enqueue(
        self,
        operation: Callable[..., Awaitable[Any]],
        *args: Any,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> str:
        """
        Add a write operation to the queue.

        Args:
            operation: Async callable to execute.
            *args: Arguments to pass.
            max_retries: Maximum retry attempts.
            **kwargs: Keyword arguments.

        Returns:
            Operation ID for tracking.
        """
        op = WriteOperation.create(
            operation,
            *args,
            max_retries=max_retries,
            **kwargs,
        )
        await self._queue.put(op)
        self._pending[op.id] = op
        return op.id

    async def start(self) -> None:
        """Start the queue processor."""
        if not self._processing:
            self._processing = True
            self._processor_task = asyncio.create_task(self._process_loop())

    async def stop(self, wait: bool = True) -> None:
        """
        Stop the queue processor.

        Args:
            wait: Wait for pending operations to complete.
        """
        self._processing = False
        if self._processor_task:
            if not wait:
                self._processor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._processor_task
            self._processor_task = None

    async def _process_loop(self) -> None:
        """Main processing loop."""
        while self._processing:
            # Process retry queue first
            await self._process_retries()

            # Process main queue in batches
            batch: list[WriteOperation] = []
            while len(batch) < self.config.batch_size:
                try:
                    op = self._queue.get_nowait()
                    batch.append(op)
                except asyncio.QueueEmpty:
                    break

            if batch:
                await self._process_batch(batch)
            else:
                # No work, wait a bit
                await asyncio.sleep(self.config.batch_delay)

    async def _process_batch(self, batch: list[WriteOperation]) -> None:
        """Process a batch of operations."""
        for op in batch:
            await self._execute_operation(op)
            await asyncio.sleep(self.config.batch_delay)

    async def _process_retries(self) -> None:
        """Process operations from retry queue."""
        while True:
            try:
                op = self._retry_queue.get_nowait()
                await self._execute_operation(op)
            except asyncio.QueueEmpty:
                break

    async def _execute_operation(self, op: WriteOperation) -> None:
        """Execute a single operation."""
        op.status = WriteStatus.IN_PROGRESS
        op.attempts += 1

        try:
            result = await op.operation(*op.args, **op.kwargs)
            op.result = result
            op.status = WriteStatus.COMPLETED
            logger.debug(f"Operation {op.id} completed")

        except Exception as e:
            op.error = e
            logger.warning(f"Operation {op.id} failed: {e}")

            if op.attempts < op.max_retries:
                op.status = WriteStatus.RETRYING
                # Exponential backoff
                delay = self.config.retry_delay * (2 ** (op.attempts - 1))
                await asyncio.sleep(delay)
                await self._retry_queue.put(op)
            else:
                op.status = WriteStatus.FAILED
                logger.error(f"Operation {op.id} failed after {op.attempts} attempts")

    def get_operation(self, operation_id: str) -> WriteOperation | None:
        """Get an operation by ID."""
        return self._pending.get(operation_id)

    def pending_count(self) -> int:
        """Get the number of pending operations."""
        return self._queue.qsize() + self._retry_queue.qsize()

    async def wait_for(
        self,
        operation_id: str,
        timeout: float | None = None,
    ) -> WriteOperation:
        """
        Wait for an operation to complete.

        Args:
            operation_id: Operation ID to wait for.
            timeout: Maximum wait time in seconds.

        Returns:
            The completed operation.

        Raises:
            KeyError: If operation not found.
            asyncio.TimeoutError: If timeout exceeded.
        """
        op = self._pending.get(operation_id)
        if op is None:
            raise KeyError(f"Operation {operation_id} not found")

        start = monotonic_timestamp()
        while op.status in (WriteStatus.PENDING, WriteStatus.IN_PROGRESS, WriteStatus.RETRYING):
            if timeout and (monotonic_timestamp() - start) > timeout:
                raise asyncio.TimeoutError(f"Timeout waiting for operation {operation_id}")
            await asyncio.sleep(0.1)

        return op

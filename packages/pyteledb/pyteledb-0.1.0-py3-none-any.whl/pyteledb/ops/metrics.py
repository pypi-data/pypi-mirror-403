"""Observability metrics for pyteledb.

Provides operation counters, latency tracking, and cache statistics.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from pyteledb.utils.time import monotonic_timestamp


@dataclass
class OperationMetrics:
    """Metrics for a single operation type."""

    name: str
    total_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0

    def record(self, latency_ms: float, success: bool = True) -> None:
        """Record an operation."""
        self.total_count += 1
        self.total_latency_ms += latency_ms
        self.min_latency_ms = min(self.min_latency_ms, latency_ms)
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)

        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        if self.total_count == 0:
            return 0.0
        return self.total_latency_ms / self.total_count

    @property
    def success_rate(self) -> float:
        """Success rate as a fraction."""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "min_latency_ms": self.min_latency_ms if self.total_count > 0 else 0,
            "max_latency_ms": self.max_latency_ms,
        }


class Metrics:
    """
    Central metrics collector for pyteledb.

    Thread-safe metric collection with support for
    operation timing, counters, and custom gauges.
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._operations: dict[str, OperationMetrics] = {}
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._start_time = monotonic_timestamp()

    async def record_operation(
        self,
        name: str,
        latency_ms: float,
        success: bool = True,
    ) -> None:
        """
        Record an operation.

        Args:
            name: Operation name.
            latency_ms: Latency in milliseconds.
            success: Whether the operation succeeded.
        """
        async with self._lock:
            if name not in self._operations:
                self._operations[name] = OperationMetrics(name=name)
            self._operations[name].record(latency_ms, success)

    def time_operation(self, name: str) -> OperationTimer:
        """
        Create a context manager to time an operation.

        Args:
            name: Operation name.

        Returns:
            Context manager that records timing on exit.
        """
        return OperationTimer(self, name)

    async def increment(self, name: str, value: int = 1) -> int:
        """
        Increment a counter.

        Args:
            name: Counter name.
            value: Amount to increment.

        Returns:
            New counter value.
        """
        async with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value
            return self._counters[name]

    async def set_gauge(self, name: str, value: float) -> None:
        """
        Set a gauge value.

        Args:
            name: Gauge name.
            value: Gauge value.
        """
        async with self._lock:
            self._gauges[name] = value

    async def get_counter(self, name: str) -> int:
        """Get a counter value."""
        async with self._lock:
            return self._counters.get(name, 0)

    async def get_gauge(self, name: str) -> float | None:
        """Get a gauge value."""
        async with self._lock:
            return self._gauges.get(name)

    async def get_operation_metrics(self, name: str) -> OperationMetrics | None:
        """Get metrics for an operation."""
        async with self._lock:
            return self._operations.get(name)

    async def snapshot(self) -> dict[str, Any]:
        """
        Get a snapshot of all metrics.

        Returns:
            Dictionary with all metrics.
        """
        async with self._lock:
            uptime = monotonic_timestamp() - self._start_time

            return {
                "uptime_seconds": uptime,
                "operations": {
                    name: metrics.to_dict() for name, metrics in self._operations.items()
                },
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }

    async def reset(self) -> None:
        """Reset all metrics."""
        async with self._lock:
            self._operations.clear()
            self._counters.clear()
            self._gauges.clear()
            self._start_time = monotonic_timestamp()


class OperationTimer:
    """Context manager for timing operations."""

    def __init__(self, metrics: Metrics, name: str) -> None:
        self._metrics = metrics
        self._name = name
        self._start: float = 0
        self._success = True

    async def __aenter__(self) -> OperationTimer:
        self._start = monotonic_timestamp()
        return self

    async def __aexit__(self, exc_type: Any, *_: Any) -> None:
        latency_ms = (monotonic_timestamp() - self._start) * 1000
        success = exc_type is None and self._success
        await self._metrics.record_operation(self._name, latency_ms, success)

    def mark_failure(self) -> None:
        """Mark the operation as failed."""
        self._success = False


# Global metrics instance
_global_metrics: Metrics | None = None


def get_metrics() -> Metrics:
    """Get or create the global metrics instance."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = Metrics()
    return _global_metrics

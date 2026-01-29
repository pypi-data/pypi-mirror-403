"""Time utilities for pyteledb.

Provides consistent time handling for TTL, timestamps, and expiration checks.
Uses monotonic time where appropriate to avoid clock skew issues.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone


def monotonic_timestamp() -> float:
    """
    Get a monotonic timestamp for TTL calculations.

    Returns:
        Monotonic time in seconds (not related to wall clock).
    """
    return time.monotonic()


def utc_now() -> datetime:
    """
    Get the current UTC datetime.

    Returns:
        Timezone-aware datetime in UTC.
    """
    return datetime.now(timezone.utc)


def utc_timestamp() -> float:
    """
    Get the current UTC timestamp as seconds since epoch.

    Returns:
        Unix timestamp in seconds.
    """
    return time.time()


def ttl_expired(created_at: float, ttl_seconds: float) -> bool:
    """
    Check if a TTL has expired based on monotonic time.

    Args:
        created_at: Monotonic timestamp when the item was created.
        ttl_seconds: Time-to-live in seconds.

    Returns:
        True if the TTL has expired, False otherwise.
    """
    return monotonic_timestamp() - created_at > ttl_seconds


def seconds_until_expiry(created_at: float, ttl_seconds: float) -> float:
    """
    Calculate seconds remaining until expiry.

    Args:
        created_at: Monotonic timestamp when the item was created.
        ttl_seconds: Time-to-live in seconds.

    Returns:
        Seconds until expiry (negative if already expired).
    """
    elapsed = monotonic_timestamp() - created_at
    return ttl_seconds - elapsed


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Human-readable duration string (e.g., "2h 30m 15s").
    """
    if seconds < 0:
        return "expired"

    parts: list[str] = []

    hours = int(seconds // 3600)
    if hours:
        parts.append(f"{hours}h")
        seconds %= 3600

    minutes = int(seconds // 60)
    if minutes:
        parts.append(f"{minutes}m")
        seconds %= 60

    if seconds or not parts:
        parts.append(f"{int(seconds)}s")

    return " ".join(parts)

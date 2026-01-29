"""ID generation utilities for pyteledb.

Provides unique, deterministic ID generation for records.
"""

from __future__ import annotations

import hashlib
import secrets
import time
import uuid


def generate_record_id() -> str:
    """
    Generate a unique record ID.

    Uses UUID4 for uniqueness, represented as a hex string.
    Format: 32 character lowercase hex string.

    Returns:
        Unique record ID string.
    """
    return uuid.uuid4().hex


def generate_short_id(length: int = 12) -> str:
    """
    Generate a short random ID.

    Uses cryptographically secure random bytes.

    Args:
        length: Length of the ID in characters (default 12).

    Returns:
        Random hex string of specified length.
    """
    # Each byte = 2 hex chars, so we need length // 2 bytes
    num_bytes = (length + 1) // 2
    return secrets.token_hex(num_bytes)[:length]


def deterministic_id(*components: str) -> str:
    """
    Generate a deterministic ID from input components.

    Useful for creating predictable IDs for the same input.
    Uses SHA-256 hash truncated to 32 characters.

    Args:
        *components: String components to hash.

    Returns:
        Deterministic 32-character hex ID.
    """
    combined = "|".join(components)
    return hashlib.sha256(combined.encode()).hexdigest()[:32]


def timestamp_id() -> str:
    """
    Generate a timestamp-prefixed unique ID.

    Format: <timestamp_hex>-<random_hex>
    Useful for roughly time-ordered IDs.

    Returns:
        Timestamp-prefixed unique ID.
    """
    # Milliseconds since epoch as hex
    ts = hex(int(time.time() * 1000))[2:]
    # Random suffix for uniqueness
    suffix = secrets.token_hex(8)
    return f"{ts}-{suffix}"


def validate_record_id(record_id: str) -> bool:
    """
    Validate that a string is a valid record ID format.

    Args:
        record_id: String to validate.

    Returns:
        True if valid record ID format, False otherwise.
    """
    if not isinstance(record_id, str):
        return False
    if len(record_id) != 32:
        return False
    try:
        int(record_id, 16)
        return True
    except ValueError:
        return False

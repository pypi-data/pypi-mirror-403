"""Payload serialization for Telegram message storage.

Handles JSON encoding/decoding with size limit awareness.
"""

from __future__ import annotations

import json
import zlib
from typing import Any

from pyteledb.exceptions import PayloadTooLargeError, SerializationError

# Telegram message text limit (UTF-8 characters)
MAX_MESSAGE_TEXT_SIZE = 4096

# Maximum size for document caption
MAX_CAPTION_SIZE = 1024

# Threshold for compression (bytes)
COMPRESSION_THRESHOLD = 1024


def serialize(
    data: Any,
    *,
    compress: bool = False,
    max_size: int | None = None,
) -> str:
    """
    Serialize data to a JSON string for Telegram message storage.

    Args:
        data: Data to serialize (must be JSON-serializable).
        compress: Whether to compress the output (base64-encoded zlib).
        max_size: Maximum allowed size in bytes (default: Telegram limit).

    Returns:
        JSON string representation.

    Raises:
        SerializationError: If serialization fails.
        PayloadTooLargeError: If result exceeds max_size.
    """
    max_size = max_size or MAX_MESSAGE_TEXT_SIZE

    try:
        json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as e:
        raise SerializationError(f"Failed to serialize data: {e}") from e

    # Apply compression if requested and beneficial
    if compress and len(json_str.encode("utf-8")) > COMPRESSION_THRESHOLD:
        import base64

        compressed = zlib.compress(json_str.encode("utf-8"), level=6)
        encoded = base64.b64encode(compressed).decode("ascii")
        # Prefix with marker for deserialization
        result = f"$Z${encoded}"
    else:
        result = json_str

    # Check size limit
    result_bytes = len(result.encode("utf-8"))
    if result_bytes > max_size:
        raise PayloadTooLargeError(
            f"Serialized payload ({result_bytes} bytes) exceeds limit ({max_size} bytes)",
            size=result_bytes,
            max_size=max_size,
        )

    return result


def deserialize(data: str) -> Any:
    """
    Deserialize data from a JSON string.

    Automatically handles compressed payloads.

    Args:
        data: JSON string (possibly compressed).

    Returns:
        Deserialized Python object.

    Raises:
        SerializationError: If deserialization fails.
    """
    if not data:
        raise SerializationError("Cannot deserialize empty string")

    try:
        # Check for compression marker
        if data.startswith("$Z$"):
            import base64

            encoded = data[3:]  # Remove marker
            compressed = base64.b64decode(encoded)
            json_str = zlib.decompress(compressed).decode("utf-8")
            return json.loads(json_str)

        return json.loads(data)
    except (json.JSONDecodeError, zlib.error, ValueError) as e:
        raise SerializationError(f"Failed to deserialize data: {e}") from e


def estimate_size(data: Any) -> int:
    """
    Estimate the serialized size of data.

    Args:
        data: Data to estimate size for.

    Returns:
        Estimated size in bytes.
    """
    try:
        json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return len(json_str.encode("utf-8"))
    except (TypeError, ValueError):
        return -1


def fits_in_message(data: Any, margin: int = 100) -> bool:
    """
    Check if data will fit in a Telegram message.

    Args:
        data: Data to check.
        margin: Safety margin in bytes.

    Returns:
        True if data fits, False otherwise.
    """
    size = estimate_size(data)
    return 0 <= size <= (MAX_MESSAGE_TEXT_SIZE - margin)


def fits_in_caption(data: Any, margin: int = 50) -> bool:
    """
    Check if data will fit in a document caption.

    Args:
        data: Data to check.
        margin: Safety margin in bytes.

    Returns:
        True if data fits, False otherwise.
    """
    size = estimate_size(data)
    return 0 <= size <= (MAX_CAPTION_SIZE - margin)

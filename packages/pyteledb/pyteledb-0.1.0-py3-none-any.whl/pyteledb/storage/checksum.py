"""Data integrity via checksums.

Provides corruption detection for stored records.
"""

from __future__ import annotations

import hashlib
import zlib
from enum import Enum
from typing import Any

from pyteledb.exceptions import CorruptionError


class ChecksumAlgorithm(Enum):
    """Supported checksum algorithms."""

    CRC32 = "crc32"
    SHA256 = "sha256"
    MD5 = "md5"


def compute_checksum(
    data: str | bytes,
    algorithm: ChecksumAlgorithm = ChecksumAlgorithm.CRC32,
) -> str:
    """
    Compute a checksum for the given data.

    Args:
        data: Data to checksum (string or bytes).
        algorithm: Checksum algorithm to use.

    Returns:
        Hex string of the checksum.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    if algorithm == ChecksumAlgorithm.CRC32:
        # CRC32 returns an unsigned int, format as 8-char hex
        checksum = zlib.crc32(data) & 0xFFFFFFFF
        return f"{checksum:08x}"

    elif algorithm == ChecksumAlgorithm.SHA256:
        return hashlib.sha256(data).hexdigest()

    elif algorithm == ChecksumAlgorithm.MD5:
        return hashlib.md5(data).hexdigest()

    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")


def verify_checksum(
    data: str | bytes,
    expected: str,
    algorithm: ChecksumAlgorithm = ChecksumAlgorithm.CRC32,
) -> bool:
    """
    Verify that data matches the expected checksum.

    Args:
        data: Data to verify.
        expected: Expected checksum value.
        algorithm: Checksum algorithm used.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual = compute_checksum(data, algorithm)
    return actual == expected


def verify_checksum_or_raise(
    data: str | bytes,
    expected: str,
    algorithm: ChecksumAlgorithm = ChecksumAlgorithm.CRC32,
    context: dict[str, Any] | None = None,
) -> None:
    """
    Verify checksum and raise CorruptionError if mismatch.

    Args:
        data: Data to verify.
        expected: Expected checksum value.
        algorithm: Checksum algorithm used.
        context: Additional context for error message.

    Raises:
        CorruptionError: If checksum doesn't match.
    """
    actual = compute_checksum(data, algorithm)
    if actual != expected:
        raise CorruptionError(
            f"Checksum mismatch: expected {expected}, got {actual}",
            details={
                "expected": expected,
                "actual": actual,
                "algorithm": algorithm.value,
                **(context or {}),
            },
        )


def compute_record_checksum(
    record_id: str,
    version: int,
    payload: str,
) -> str:
    """
    Compute a checksum for a record combining identity and payload.

    Args:
        record_id: Record ID.
        version: Record version.
        payload: Serialized payload.

    Returns:
        Checksum string.
    """
    combined = f"{record_id}:{version}:{payload}"
    return compute_checksum(combined, ChecksumAlgorithm.CRC32)

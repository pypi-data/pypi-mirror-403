"""Tests for checksum module."""

from __future__ import annotations

import pytest

from pyteledb.exceptions import CorruptionError
from pyteledb.storage.checksum import (
    ChecksumAlgorithm,
    compute_checksum,
    compute_record_checksum,
    verify_checksum,
    verify_checksum_or_raise,
)


class TestChecksum:
    """Tests for checksum functions."""

    def test_compute_checksum_crc32(self) -> None:
        """Test CRC32 checksum computation."""
        data = "Hello, World!"
        checksum = compute_checksum(data, ChecksumAlgorithm.CRC32)

        assert isinstance(checksum, str)
        assert len(checksum) == 8  # 8 hex chars for CRC32

    def test_compute_checksum_sha256(self) -> None:
        """Test SHA256 checksum computation."""
        data = "Hello, World!"
        checksum = compute_checksum(data, ChecksumAlgorithm.SHA256)

        assert isinstance(checksum, str)
        assert len(checksum) == 64  # 64 hex chars for SHA256

    def test_compute_checksum_bytes(self) -> None:
        """Test checksum with bytes input."""
        data = b"Hello, World!"
        checksum = compute_checksum(data)

        assert isinstance(checksum, str)

    def test_verify_checksum_valid(self) -> None:
        """Test verification of valid checksum."""
        data = "test data"
        checksum = compute_checksum(data)

        assert verify_checksum(data, checksum) is True

    def test_verify_checksum_invalid(self) -> None:
        """Test verification of invalid checksum."""
        data = "test data"

        assert verify_checksum(data, "00000000") is False

    def test_verify_checksum_or_raise(self) -> None:
        """Test verification with exception."""
        data = "test data"
        checksum = compute_checksum(data)

        # Should not raise
        verify_checksum_or_raise(data, checksum)

        # Should raise
        with pytest.raises(CorruptionError):
            verify_checksum_or_raise(data, "00000000")

    def test_compute_record_checksum(self) -> None:
        """Test record-specific checksum."""
        checksum = compute_record_checksum(
            record_id="abc123",
            version=1,
            payload='{"name":"Alice"}',
        )

        assert isinstance(checksum, str)
        assert len(checksum) == 8

    def test_checksum_deterministic(self) -> None:
        """Test that checksums are deterministic."""
        data = "same data"

        checksum1 = compute_checksum(data)
        checksum2 = compute_checksum(data)

        assert checksum1 == checksum2

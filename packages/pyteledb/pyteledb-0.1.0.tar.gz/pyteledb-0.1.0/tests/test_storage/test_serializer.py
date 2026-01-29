"""Tests for serializer module."""

from __future__ import annotations

import pytest

from pyteledb.exceptions import PayloadTooLargeError, SerializationError
from pyteledb.storage.serializer import (
    deserialize,
    estimate_size,
    fits_in_message,
    serialize,
)


class TestSerializer:
    """Tests for serialization functions."""

    def test_serialize_simple(self) -> None:
        """Test serializing simple data."""
        data = {"name": "Alice", "score": 100}
        result = serialize(data)

        assert isinstance(result, str)
        assert "Alice" in result

    def test_deserialize_simple(self) -> None:
        """Test deserializing simple data."""
        json_str = '{"name":"Alice","score":100}'
        result = deserialize(json_str)

        assert result == {"name": "Alice", "score": 100}

    def test_roundtrip(self, sample_record_data: dict) -> None:
        """Test serialization roundtrip."""
        serialized = serialize(sample_record_data)
        deserialized = deserialize(serialized)

        assert deserialized == sample_record_data

    def test_serialize_with_compression(self) -> None:
        """Test compression for large payloads."""
        # Create data larger than compression threshold
        data = {"text": "x" * 2000}
        result = serialize(data, compress=True)

        # Should be compressed (starts with marker)
        assert result.startswith("$Z$")

        # Should round-trip correctly
        restored = deserialize(result)
        assert restored == data

    def test_serialize_too_large(self) -> None:
        """Test error on oversized payload."""
        data = {"text": "x" * 5000}

        with pytest.raises(PayloadTooLargeError):
            serialize(data, max_size=1000)

    def test_deserialize_empty(self) -> None:
        """Test error on empty string."""
        with pytest.raises(SerializationError):
            deserialize("")

    def test_deserialize_invalid_json(self) -> None:
        """Test error on invalid JSON."""
        with pytest.raises(SerializationError):
            deserialize("not valid json")

    def test_estimate_size(self) -> None:
        """Test size estimation."""
        data = {"name": "Alice"}
        size = estimate_size(data)

        assert size > 0
        assert size == len(serialize(data).encode("utf-8"))

    def test_fits_in_message(self) -> None:
        """Test message size check."""
        small_data = {"x": 1}
        large_data = {"text": "x" * 5000}

        assert fits_in_message(small_data) is True
        assert fits_in_message(large_data) is False

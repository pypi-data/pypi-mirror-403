"""Tests for Record class."""

from __future__ import annotations

import pytest

from pyteledb.core.record import Record, RecordMetadata


class TestRecord:
    """Tests for Record class."""

    def test_create_record(self, sample_record_data: dict) -> None:
        """Test creating a new record."""
        record = Record.create(sample_record_data)

        assert record.id is not None
        assert len(record.id) == 32  # UUID hex
        assert record.version == 1
        assert record.payload == sample_record_data
        assert record.metadata.checksum is not None

    def test_create_record_with_custom_id(self, sample_record_data: dict) -> None:
        """Test creating a record with custom ID."""
        custom_id = "a" * 32
        record = Record.create(sample_record_data, record_id=custom_id)

        assert record.id == custom_id

    def test_create_record_with_tags(self, sample_record_data: dict) -> None:
        """Test creating a record with tags."""
        tags = ["user", "active"]
        record = Record.create(sample_record_data, tags=tags)

        assert record.metadata.tags == tags

    def test_verify_checksum(self, sample_record_data: dict) -> None:
        """Test checksum verification."""
        record = Record.create(sample_record_data)

        assert record.verify_checksum() is True

        # Corrupt the payload
        record.payload["name"] = "Corrupted"
        assert record.verify_checksum() is False

    def test_next_version(self, sample_record_data: dict) -> None:
        """Test version incrementing."""
        record = Record.create(sample_record_data)
        assert record.version == 1

        updated = record.next_version()
        assert updated.version == 2
        assert updated.id == record.id

    def test_to_dict_and_from_dict(self, sample_record_data: dict) -> None:
        """Test serialization round-trip."""
        record = Record.create(sample_record_data, tags=["test"])
        record.metadata.message_id = 12345

        data = record.to_dict()
        restored = Record.from_dict(data)

        assert restored.id == record.id
        assert restored.version == record.version
        assert restored.payload == record.payload
        assert restored.message_id == 12345
        assert restored.metadata.tags == ["test"]


class TestRecordMetadata:
    """Tests for RecordMetadata class."""

    def test_to_dict_and_from_dict(self) -> None:
        """Test metadata serialization."""
        metadata = RecordMetadata(
            record_id="abc123",
            message_id=456,
            prev_id="prev",
            next_id="next",
            tags=["tag1", "tag2"],
        )

        data = metadata.to_dict()
        restored = RecordMetadata.from_dict(data)

        assert restored.record_id == "abc123"
        assert restored.message_id == 456
        assert restored.prev_id == "prev"
        assert restored.next_id == "next"
        assert restored.tags == ["tag1", "tag2"]

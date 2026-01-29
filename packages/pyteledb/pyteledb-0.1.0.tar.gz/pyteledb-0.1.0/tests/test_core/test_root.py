"""Tests for RootIndex class."""

from __future__ import annotations

import pytest

from pyteledb.core.root import RootIndex, is_valid_root, parse_root_text


class TestRootIndex:
    """Tests for RootIndex class."""

    def test_create_root(self) -> None:
        """Test creating a new root index."""
        root = RootIndex.create("test_db")

        assert root.db_name == "test_db"
        assert root.db_id is not None
        assert root.version is not None
        assert root.version.version == 1
        assert root.record_count == 0
        assert root.is_empty()

    def test_next_version(self) -> None:
        """Test version incrementing."""
        root = RootIndex.create("test_db")
        assert root.version.version == 1

        updated = root.next_version()
        assert updated.version.version == 2
        assert updated.db_id == root.db_id

    def test_to_dict_and_from_dict(self) -> None:
        """Test serialization round-trip."""
        root = RootIndex.create("test_db", metadata={"key": "value"})
        root.message_id = 123

        data = root.to_dict()
        restored = RootIndex.from_dict(data)

        assert restored.db_name == "test_db"
        assert restored.db_id == root.db_id
        assert restored.message_id == 123
        assert restored.metadata == {"key": "value"}

    def test_stats(self) -> None:
        """Test stats generation."""
        root = RootIndex.create("test_db")
        stats = root.stats()

        assert stats["name"] == "test_db"
        assert stats["record_count"] == 0
        assert stats["segment_count"] == 0

    def test_is_valid_root(self, sample_root_data: dict) -> None:
        """Test root validation."""
        assert is_valid_root(sample_root_data) is True
        assert is_valid_root({}) is False
        assert is_valid_root({"_": "PTDB"}) is False
        assert is_valid_root({"_": "WRONG", "name": "x", "id": "y"}) is False

    def test_parse_root_text(self, sample_root_data: dict) -> None:
        """Test parsing root from JSON text."""
        import json

        text = json.dumps(sample_root_data)
        root = parse_root_text(text)

        assert root is not None
        assert root.db_name == "test_db"

    def test_parse_root_text_invalid(self) -> None:
        """Test parsing invalid JSON."""
        assert parse_root_text("not json") is None
        assert parse_root_text('{"_": "WRONG"}') is None
        assert parse_root_text("") is None

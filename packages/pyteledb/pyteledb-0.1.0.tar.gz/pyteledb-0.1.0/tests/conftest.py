"""Pytest configuration and fixtures for pyteledb tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_record_data() -> dict:
    """Sample record data for testing."""
    return {
        "user_id": 12345,
        "name": "Test User",
        "score": 100,
        "active": True,
    }


@pytest.fixture
def sample_root_data() -> dict:
    """Sample root index data for testing."""
    return {
        "_": "PTDB",
        "v": 1,
        "name": "test_db",
        "id": "abc123def456",
        "ver": {"v": 1, "c": 1700000000.0, "u": 1700000000.0},
        "mid": 123,
        "chain": {"head": None, "tail": None, "len": 0},
        "segs": [],
        "count": 0,
        "ts_c": 1700000000.0,
        "ts_u": 1700000000.0,
        "meta": {},
    }

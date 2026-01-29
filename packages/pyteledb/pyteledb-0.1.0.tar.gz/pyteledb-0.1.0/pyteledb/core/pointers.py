"""Pointer management for linked-list/log structure.

Records are linked via forward/backward references.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Pointer:
    """
    A pointer to another record.

    Attributes:
        record_id: Target record ID.
        message_id: Target message ID (for direct fetch).
        segment_id: Segment this pointer belongs to (optional).
    """

    record_id: str
    message_id: int | None = None
    segment_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rid": self.record_id,
            "mid": self.message_id,
            "seg": self.segment_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Pointer:
        """Create from dictionary."""
        return cls(
            record_id=data["rid"],
            message_id=data.get("mid"),
            segment_id=data.get("seg"),
        )


@dataclass
class PointerChain:
    """
    A chain of pointers for traversing records.

    Supports bidirectional traversal and segment management.

    Attributes:
        head: First record in the chain.
        tail: Last record in the chain.
        length: Number of records in the chain.
        segment_id: Identifier for this segment.
    """

    head: Pointer | None = None
    tail: Pointer | None = None
    length: int = 0
    segment_id: str | None = None

    def is_empty(self) -> bool:
        """Check if the chain is empty."""
        return self.head is None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "head": self.head.to_dict() if self.head else None,
            "tail": self.tail.to_dict() if self.tail else None,
            "len": self.length,
            "seg": self.segment_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PointerChain:
        """Create from dictionary."""
        return cls(
            head=Pointer.from_dict(data["head"]) if data.get("head") else None,
            tail=Pointer.from_dict(data["tail"]) if data.get("tail") else None,
            length=data.get("len", 0),
            segment_id=data.get("seg"),
        )


@dataclass
class Segment:
    """
    A segment of the record log.

    Large databases can be split into segments for better
    performance and organization.

    Attributes:
        segment_id: Unique segment identifier.
        chain: Pointer chain for this segment.
        prev_segment: Previous segment ID.
        next_segment: Next segment ID.
        record_count: Number of records in segment.
        created_at: Creation timestamp.
        sealed: Whether segment is closed to new records.
    """

    segment_id: str
    chain: PointerChain = field(default_factory=PointerChain)
    prev_segment: str | None = None
    next_segment: str | None = None
    record_count: int = 0
    created_at: float = 0.0
    sealed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sid": self.segment_id,
            "chain": self.chain.to_dict(),
            "prev": self.prev_segment,
            "next": self.next_segment,
            "count": self.record_count,
            "ts": self.created_at,
            "sealed": self.sealed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Segment:
        """Create from dictionary."""
        return cls(
            segment_id=data["sid"],
            chain=PointerChain.from_dict(data["chain"]) if data.get("chain") else PointerChain(),
            prev_segment=data.get("prev"),
            next_segment=data.get("next"),
            record_count=data.get("count", 0),
            created_at=data.get("ts", 0.0),
            sealed=data.get("sealed", False),
        )


def link_records(
    prev_record_id: str,
    next_record_id: str,
    records: dict[str, Any],
) -> None:
    """
    Link two records together in-place.

    Args:
        prev_record_id: ID of the previous record.
        next_record_id: ID of the next record.
        records: Dictionary of record_id -> record data.
    """
    if prev_record_id in records:
        records[prev_record_id]["meta"]["next"] = next_record_id
    if next_record_id in records:
        records[next_record_id]["meta"]["prev"] = prev_record_id


def unlink_record(
    record_id: str,
    records: dict[str, Any],
) -> tuple[str | None, str | None]:
    """
    Unlink a record from its chain.

    Args:
        record_id: ID of the record to unlink.
        records: Dictionary of record_id -> record data.

    Returns:
        Tuple of (prev_id, next_id) that were linked.
    """
    if record_id not in records:
        return None, None

    record = records[record_id]
    prev_id = record["meta"].get("prev")
    next_id = record["meta"].get("next")

    # Update neighbors
    if prev_id and prev_id in records:
        records[prev_id]["meta"]["next"] = next_id
    if next_id and next_id in records:
        records[next_id]["meta"]["prev"] = prev_id

    # Clear this record's pointers
    record["meta"]["prev"] = None
    record["meta"]["next"] = None

    return prev_id, next_id

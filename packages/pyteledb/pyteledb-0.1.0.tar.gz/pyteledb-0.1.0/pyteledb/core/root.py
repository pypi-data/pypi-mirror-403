"""Root index management via pinned message.

The root index is the entry point for all database operations.
Stored as the pinned message in the Telegram chat.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pyteledb.core.pointers import PointerChain, Segment
from pyteledb.storage.versioning import RecordVersion
from pyteledb.utils.ids import generate_short_id
from pyteledb.utils.time import utc_timestamp

# Magic header for root index identification
ROOT_MAGIC = "PTDB"
ROOT_VERSION = 1


@dataclass
class RootIndex:
    """
    Root index for the Telegram database.

    Contains:
    - Database metadata
    - Pointers to record chains/segments
    - Statistics and housekeeping info

    Attributes:
        db_name: Human-readable database name.
        db_id: Unique database identifier.
        version: Root index version info.
        message_id: Telegram message ID storing this root.
        main_chain: Main record chain pointers.
        segments: List of segments for segmented storage.
        record_count: Total number of records.
        created_at: Database creation timestamp.
        updated_at: Last update timestamp.
        metadata: Additional database metadata.
    """

    db_name: str
    db_id: str = field(default_factory=lambda: generate_short_id(16))
    version: RecordVersion | None = None
    message_id: int | None = None
    main_chain: PointerChain = field(default_factory=PointerChain)
    segments: list[Segment] = field(default_factory=list)
    record_count: int = 0
    created_at: float = field(default_factory=utc_timestamp)
    updated_at: float = field(default_factory=utc_timestamp)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        db_name: str,
        *,
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RootIndex:
        """
        Create a new root index.

        Args:
            db_name: Database name.
            created_by: Creator identifier.
            metadata: Additional metadata.

        Returns:
            New RootIndex instance.
        """
        return cls(
            db_name=db_name,
            version=RecordVersion.initial(created_by),
            metadata=metadata or {},
        )

    def next_version(self, updated_by: str | None = None) -> RootIndex:
        """
        Create an updated version of this root index.

        Args:
            updated_by: Updater identifier.

        Returns:
            New RootIndex with incremented version.
        """
        import copy

        new = copy.deepcopy(self)
        new.version = self.version.next(updated_by) if self.version else None
        new.updated_at = utc_timestamp()
        return new

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "_": ROOT_MAGIC,
            "v": ROOT_VERSION,
            "name": self.db_name,
            "id": self.db_id,
            "ver": self.version.to_dict() if self.version else None,
            "mid": self.message_id,
            "chain": self.main_chain.to_dict(),
            "segs": [s.to_dict() for s in self.segments],
            "count": self.record_count,
            "ts_c": self.created_at,
            "ts_u": self.updated_at,
            "meta": self.metadata if self.metadata else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RootIndex:
        """
        Create from dictionary.

        Raises:
            ValueError: If data is not a valid root index.
        """
        # Validate magic header
        if data.get("_") != ROOT_MAGIC:
            raise ValueError("Invalid root index: missing magic header")

        version = None
        if data.get("ver"):
            version = RecordVersion.from_dict(data["ver"])

        chain = PointerChain()
        if data.get("chain"):
            chain = PointerChain.from_dict(data["chain"])

        segments = []
        for seg_data in data.get("segs", []):
            segments.append(Segment.from_dict(seg_data))

        return cls(
            db_name=data["name"],
            db_id=data["id"],
            version=version,
            message_id=data.get("mid"),
            main_chain=chain,
            segments=segments,
            record_count=data.get("count", 0),
            created_at=data.get("ts_c", 0.0),
            updated_at=data.get("ts_u", 0.0),
            metadata=data.get("meta") or {},
        )

    def get_head_message_id(self) -> int | None:
        """Get the message ID of the first record."""
        if self.main_chain.head:
            return self.main_chain.head.message_id
        return None

    def get_tail_message_id(self) -> int | None:
        """Get the message ID of the last record."""
        if self.main_chain.tail:
            return self.main_chain.tail.message_id
        return None

    def is_empty(self) -> bool:
        """Check if the database is empty."""
        return self.record_count == 0

    def stats(self) -> dict[str, Any]:
        """Get database statistics."""
        return {
            "name": self.db_name,
            "id": self.db_id,
            "record_count": self.record_count,
            "segment_count": len(self.segments),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version.version if self.version else 0,
        }


def is_valid_root(data: dict[str, Any]) -> bool:
    """
    Check if data represents a valid root index.

    Args:
        data: Dictionary to validate.

    Returns:
        True if valid root index structure.
    """
    return (
        isinstance(data, dict) and data.get("_") == ROOT_MAGIC and "name" in data and "id" in data
    )


def parse_root_text(text: str) -> RootIndex | None:
    """
    Parse root index from message text.

    Args:
        text: Message text containing serialized root.

    Returns:
        RootIndex if valid, None otherwise.
    """
    import json

    try:
        data = json.loads(text)
        if is_valid_root(data):
            return RootIndex.from_dict(data)
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    return None

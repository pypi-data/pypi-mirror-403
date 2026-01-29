"""Record dataclass representing a stored entity.

Records are the fundamental unit of storage in pyteledb.
Each record maps to one or more Telegram messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pyteledb.storage.checksum import compute_record_checksum
from pyteledb.storage.versioning import RecordVersion
from pyteledb.utils.ids import generate_record_id


@dataclass
class RecordMetadata:
    """
    Metadata for a record.

    Attributes:
        record_id: Unique record identifier.
        message_id: Telegram message ID storing this record.
        version: Version information.
        checksum: Data integrity checksum.
        prev_id: Previous record ID in chain (if linked).
        next_id: Next record ID in chain (if linked).
        file_id: Telegram file ID if payload stored as document.
        tags: Optional tags for categorization.
    """

    record_id: str
    message_id: int | None = None
    version: RecordVersion | None = None
    checksum: str | None = None
    prev_id: str | None = None
    next_id: str | None = None
    file_id: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rid": self.record_id,
            "mid": self.message_id,
            "ver": self.version.to_dict() if self.version else None,
            "chk": self.checksum,
            "prev": self.prev_id,
            "next": self.next_id,
            "fid": self.file_id,
            "tags": self.tags if self.tags else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecordMetadata:
        """Create from dictionary."""
        version = None
        if data.get("ver"):
            version = RecordVersion.from_dict(data["ver"])

        return cls(
            record_id=data["rid"],
            message_id=data.get("mid"),
            version=version,
            checksum=data.get("chk"),
            prev_id=data.get("prev"),
            next_id=data.get("next"),
            file_id=data.get("fid"),
            tags=data.get("tags") or [],
        )


@dataclass
class Record:
    """
    A stored record in the Telegram database.

    Attributes:
        metadata: Record metadata.
        payload: The actual data (JSON-serializable).
    """

    metadata: RecordMetadata
    payload: dict[str, Any]

    @classmethod
    def create(
        cls,
        payload: dict[str, Any],
        *,
        record_id: str | None = None,
        tags: list[str] | None = None,
        created_by: str | None = None,
    ) -> Record:
        """
        Create a new record.

        Args:
            payload: Record data.
            record_id: Custom record ID (auto-generated if None).
            tags: Optional tags.
            created_by: Creator identifier.

        Returns:
            New Record instance.
        """
        rid = record_id or generate_record_id()
        version = RecordVersion.initial(created_by)

        metadata = RecordMetadata(
            record_id=rid,
            version=version,
            tags=tags or [],
        )

        record = cls(metadata=metadata, payload=payload)
        record.update_checksum()
        return record

    def update_checksum(self) -> str:
        """Recompute and store the checksum."""
        import json

        payload_str = json.dumps(self.payload, separators=(",", ":"), sort_keys=True)
        version = self.metadata.version.version if self.metadata.version else 0
        checksum = compute_record_checksum(
            self.metadata.record_id,
            version,
            payload_str,
        )
        self.metadata.checksum = checksum
        return checksum

    def verify_checksum(self) -> bool:
        """Verify the record's checksum."""
        import json

        if not self.metadata.checksum:
            return False

        payload_str = json.dumps(self.payload, separators=(",", ":"), sort_keys=True)
        version = self.metadata.version.version if self.metadata.version else 0
        expected = compute_record_checksum(
            self.metadata.record_id,
            version,
            payload_str,
        )
        return self.metadata.checksum == expected

    def next_version(self, updated_by: str | None = None) -> Record:
        """
        Create an updated version of this record.

        Args:
            updated_by: Updater identifier.

        Returns:
            New Record with incremented version.
        """
        new_version = self.metadata.version.next(updated_by) if self.metadata.version else None

        new_metadata = RecordMetadata(
            record_id=self.metadata.record_id,
            message_id=self.metadata.message_id,
            version=new_version,
            prev_id=self.metadata.prev_id,
            next_id=self.metadata.next_id,
            file_id=self.metadata.file_id,
            tags=list(self.metadata.tags),
        )

        return Record(metadata=new_metadata, payload=dict(self.payload))

    @property
    def id(self) -> str:
        """Get the record ID."""
        return self.metadata.record_id

    @property
    def message_id(self) -> int | None:
        """Get the message ID."""
        return self.metadata.message_id

    @property
    def version(self) -> int:
        """Get the version number."""
        return self.metadata.version.version if self.metadata.version else 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "meta": self.metadata.to_dict(),
            "data": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Record:
        """Create from dictionary."""
        return cls(
            metadata=RecordMetadata.from_dict(data["meta"]),
            payload=data["data"],
        )

    def __repr__(self) -> str:
        return f"Record(id={self.id!r}, version={self.version}, message_id={self.message_id})"

"""Record versioning for optimistic concurrency control.

Provides version tracking and conflict detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyteledb.exceptions import VersionConflictError
from pyteledb.utils.time import utc_timestamp


@dataclass
class RecordVersion:
    """
    Version metadata for a record.

    Attributes:
        version: Monotonically increasing version number.
        created_at: Unix timestamp when record was created.
        updated_at: Unix timestamp of last update.
        created_by: Identifier of creator (optional).
        updated_by: Identifier of last updater (optional).
    """

    version: int
    created_at: float
    updated_at: float
    created_by: str | None = None
    updated_by: str | None = None

    @classmethod
    def initial(cls, created_by: str | None = None) -> RecordVersion:
        """
        Create initial version for a new record.

        Args:
            created_by: Optional identifier of creator.

        Returns:
            New RecordVersion at version 1.
        """
        now = utc_timestamp()
        return cls(
            version=1,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )

    def next(self, updated_by: str | None = None) -> RecordVersion:
        """
        Create the next version for an update.

        Args:
            updated_by: Optional identifier of updater.

        Returns:
            New RecordVersion with incremented version.
        """
        return RecordVersion(
            version=self.version + 1,
            created_at=self.created_at,
            updated_at=utc_timestamp(),
            created_by=self.created_by,
            updated_by=updated_by or self.updated_by,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation.
        """
        return {
            "v": self.version,
            "c": self.created_at,
            "u": self.updated_at,
            "cb": self.created_by,
            "ub": self.updated_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecordVersion:
        """
        Create from dictionary.

        Args:
            data: Dictionary with version data.

        Returns:
            RecordVersion instance.
        """
        return cls(
            version=data["v"],
            created_at=data["c"],
            updated_at=data["u"],
            created_by=data.get("cb"),
            updated_by=data.get("ub"),
        )


def check_version(
    expected: int,
    actual: int,
    record_id: str | None = None,
) -> None:
    """
    Check that actual version matches expected.

    Args:
        expected: Expected version number.
        actual: Actual version number.
        record_id: Optional record ID for error context.

    Raises:
        VersionConflictError: If versions don't match.
    """
    if expected != actual:
        raise VersionConflictError(
            f"Version conflict: expected {expected}, got {actual}",
            expected_version=expected,
            actual_version=actual,
            details={"record_id": record_id} if record_id else None,
        )


def is_newer(a: RecordVersion, b: RecordVersion) -> bool:
    """
    Check if version A is newer than version B.

    Args:
        a: First version.
        b: Second version.

    Returns:
        True if A is newer than B.
    """
    return a.version > b.version


def merge_versions(
    local: RecordVersion,
    remote: RecordVersion,
) -> tuple[RecordVersion, bool]:
    """
    Merge two versions, returning the newer one.

    Args:
        local: Local version.
        remote: Remote version.

    Returns:
        Tuple of (winning version, True if remote won).
    """
    if remote.version > local.version:
        return remote, True
    return local, False

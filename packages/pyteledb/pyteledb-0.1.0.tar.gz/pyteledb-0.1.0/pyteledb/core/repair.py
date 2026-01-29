"""Crash recovery and state repair.

Provides tools for detecting and repairing inconsistent state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pyteledb.utils.logging import get_logger
from pyteledb.utils.time import utc_timestamp

logger = get_logger(__name__)


class IssueType(Enum):
    """Types of issues that can be detected."""

    ORPHANED_RECORD = "orphaned_record"
    BROKEN_POINTER = "broken_pointer"
    MISSING_RECORD = "missing_record"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    VERSION_CONFLICT = "version_conflict"
    STALE_LOCK = "stale_lock"
    ROOT_CORRUPTION = "root_corruption"
    DUPLICATE_ID = "duplicate_id"


class RepairAction(Enum):
    """Types of repair actions."""

    RELINK = "relink"
    DELETE = "delete"
    RECOMPUTE_CHECKSUM = "recompute_checksum"
    UPDATE_ROOT = "update_root"
    RELEASE_LOCK = "release_lock"
    SKIP = "skip"


@dataclass
class Issue:
    """
    A detected issue in the database.

    Attributes:
        issue_type: Type of issue.
        description: Human-readable description.
        record_id: Affected record ID (if applicable).
        message_id: Affected message ID (if applicable).
        details: Additional issue details.
        suggested_action: Recommended repair action.
    """

    issue_type: IssueType
    description: str
    record_id: str | None = None
    message_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)
    suggested_action: RepairAction = RepairAction.SKIP

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.issue_type.value,
            "desc": self.description,
            "rid": self.record_id,
            "mid": self.message_id,
            "details": self.details,
            "action": self.suggested_action.value,
        }


@dataclass
class RepairResult:
    """Result of a single repair action."""

    issue: Issue
    action_taken: RepairAction
    success: bool
    message: str


@dataclass
class RepairReport:
    """
    Complete report from a repair operation.

    Attributes:
        started_at: When the repair started.
        completed_at: When the repair completed.
        issues_found: Number of issues detected.
        issues_fixed: Number of issues repaired.
        issues_skipped: Number of issues not repaired.
        results: Individual repair results.
        summary: Human-readable summary.
    """

    started_at: float = field(default_factory=utc_timestamp)
    completed_at: float | None = None
    issues_found: int = 0
    issues_fixed: int = 0
    issues_skipped: int = 0
    results: list[RepairResult] = field(default_factory=list)
    summary: str = ""

    def add_result(self, result: RepairResult) -> None:
        """Add a repair result."""
        self.results.append(result)
        self.issues_found += 1
        if result.success:
            self.issues_fixed += 1
        else:
            self.issues_skipped += 1

    def finalize(self) -> None:
        """Finalize the report."""
        self.completed_at = utc_timestamp()
        duration = self.completed_at - self.started_at
        self.summary = (
            f"Repair completed in {duration:.2f}s. "
            f"Found {self.issues_found} issues, "
            f"fixed {self.issues_fixed}, "
            f"skipped {self.issues_skipped}."
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "issues_skipped": self.issues_skipped,
            "results": [
                {
                    "issue": r.issue.to_dict(),
                    "action": r.action_taken.value,
                    "success": r.success,
                    "message": r.message,
                }
                for r in self.results
            ],
            "summary": self.summary,
        }


class RepairTool:
    """
    Tool for detecting and repairing database issues.

    All repairs are explicit, inspectable, and deterministic.
    """

    def __init__(self) -> None:
        """Initialize the repair tool."""
        self._issues: list[Issue] = []

    def add_issue(self, issue: Issue) -> None:
        """Add a detected issue."""
        self._issues.append(issue)
        logger.warning(f"Issue detected: {issue.issue_type.value} - {issue.description}")

    def clear_issues(self) -> None:
        """Clear all detected issues."""
        self._issues.clear()

    @property
    def issues(self) -> list[Issue]:
        """Get all detected issues."""
        return list(self._issues)

    @property
    def issue_count(self) -> int:
        """Get the number of issues."""
        return len(self._issues)

    def check_pointer_chain(
        self,
        records: dict[str, dict[str, Any]],
        head_id: str | None,
    ) -> list[Issue]:
        """
        Check a pointer chain for issues.

        Args:
            records: Dictionary of record_id -> record data.
            head_id: ID of the chain head.

        Returns:
            List of detected issues.
        """
        issues: list[Issue] = []

        if not head_id:
            return issues

        visited: set[str] = set()
        current_id = head_id

        while current_id:
            if current_id in visited:
                issues.append(
                    Issue(
                        issue_type=IssueType.BROKEN_POINTER,
                        description=f"Circular reference detected at {current_id}",
                        record_id=current_id,
                        suggested_action=RepairAction.RELINK,
                    )
                )
                break

            visited.add(current_id)

            if current_id not in records:
                issues.append(
                    Issue(
                        issue_type=IssueType.MISSING_RECORD,
                        description=f"Record {current_id} referenced but not found",
                        record_id=current_id,
                        suggested_action=RepairAction.RELINK,
                    )
                )
                break

            record = records[current_id]
            meta = record.get("meta", {})
            next_id = meta.get("next")
            prev_id = meta.get("prev")

            # Verify backward pointer
            if prev_id and prev_id in records:
                prev_record = records[prev_id]
                prev_next = prev_record.get("meta", {}).get("next")
                if prev_next != current_id:
                    issues.append(
                        Issue(
                            issue_type=IssueType.BROKEN_POINTER,
                            description=f"Inconsistent prev/next between {prev_id} and {current_id}",
                            record_id=current_id,
                            details={"prev_id": prev_id, "prev_next": prev_next},
                            suggested_action=RepairAction.RELINK,
                        )
                    )

            current_id = next_id

        return issues

    def check_checksums(
        self,
        records: dict[str, dict[str, Any]],
    ) -> list[Issue]:
        """
        Verify checksums for all records.

        Args:
            records: Dictionary of record_id -> record data.

        Returns:
            List of checksum issues.
        """
        from pyteledb.core.record import Record

        issues: list[Issue] = []

        for record_id, record_data in records.items():
            try:
                record = Record.from_dict(record_data)
                if not record.verify_checksum():
                    issues.append(
                        Issue(
                            issue_type=IssueType.CHECKSUM_MISMATCH,
                            description=f"Checksum mismatch for record {record_id}",
                            record_id=record_id,
                            suggested_action=RepairAction.RECOMPUTE_CHECKSUM,
                        )
                    )
            except Exception as e:
                issues.append(
                    Issue(
                        issue_type=IssueType.CHECKSUM_MISMATCH,
                        description=f"Cannot verify checksum for {record_id}: {e}",
                        record_id=record_id,
                        suggested_action=RepairAction.SKIP,
                    )
                )

        return issues

    def find_orphaned_records(
        self,
        records: dict[str, dict[str, Any]],
        head_id: str | None,
    ) -> list[Issue]:
        """
        Find records not reachable from the chain head.

        Args:
            records: Dictionary of record_id -> record data.
            head_id: ID of the chain head.

        Returns:
            List of orphaned record issues.
        """
        issues: list[Issue] = []

        if not head_id:
            # All records are orphaned if no head
            for record_id in records:
                issues.append(
                    Issue(
                        issue_type=IssueType.ORPHANED_RECORD,
                        description=f"Orphaned record {record_id} (no chain head)",
                        record_id=record_id,
                        suggested_action=RepairAction.RELINK,
                    )
                )
            return issues

        # Traverse chain to find reachable records
        reachable: set[str] = set()
        current_id = head_id

        while current_id and current_id in records:
            if current_id in reachable:
                break
            reachable.add(current_id)
            current_id = records[current_id].get("meta", {}).get("next")

        # Find orphaned
        for record_id in records:
            if record_id not in reachable:
                issues.append(
                    Issue(
                        issue_type=IssueType.ORPHANED_RECORD,
                        description=f"Orphaned record {record_id} (not in chain)",
                        record_id=record_id,
                        suggested_action=RepairAction.RELINK,
                    )
                )

        return issues

    def generate_report(self) -> RepairReport:
        """
        Generate a report of all detected issues.

        Returns:
            RepairReport with all issues.
        """
        report = RepairReport()
        for issue in self._issues:
            result = RepairResult(
                issue=issue,
                action_taken=RepairAction.SKIP,
                success=False,
                message="Not yet repaired",
            )
            report.add_result(result)
        report.finalize()
        return report

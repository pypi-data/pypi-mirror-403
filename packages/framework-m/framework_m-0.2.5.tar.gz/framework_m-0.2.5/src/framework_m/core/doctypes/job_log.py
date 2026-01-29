"""JobLog DocType - Background job execution log.

Stores job execution history for monitoring and debugging.
Tracks job status through Queued → Running → Success/Failed.

Example:
    # Log a queued job
    log = JobLog(
        job_id="job-abc123",
        job_name="send_daily_report",
        status="queued",
    )

    # Update when job starts
    log.status = "running"
    log.started_at = datetime.now(UTC)

    # Update when job completes
    log.status = "success"
    log.completed_at = datetime.now(UTC)
    log.result = {"emails_sent": 100}
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(UTC)


class JobLog(BaseDocType):
    """Background job execution log.

    Records job execution status and results for monitoring,
    debugging, and audit purposes.

    Attributes:
        job_id: Unique job identifier from job queue
        job_name: Name of the job function
        status: Current status (queued/running/success/failed)
        enqueued_at: When the job was added to queue
        started_at: When the job started executing
        completed_at: When the job finished
        error: Error message if job failed
        result: Job result data if successful
    """

    # Job identification
    job_id: str = Field(
        ...,
        description="Unique job identifier from job queue",
        min_length=1,
    )

    job_name: str = Field(
        ...,
        description="Name of the job function",
        min_length=1,
    )

    # Status tracking
    status: str = Field(
        ...,
        description="Job status: queued, running, success, or failed",
    )

    # Timestamps
    enqueued_at: datetime = Field(
        default_factory=_utc_now,
        description="When the job was added to queue",
    )

    started_at: datetime | None = Field(
        default=None,
        description="When the job started executing",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="When the job finished (success or failure)",
    )

    # Results
    error: str | None = Field(
        default=None,
        description="Error message if job failed",
    )

    result: dict[str, Any] | None = Field(
        default=None,
        description="Job result data if successful",
    )

    @property
    def duration_seconds(self) -> float | None:
        """Calculate job duration in seconds.

        Returns:
            Duration in seconds if job has started and completed, None otherwise.
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    class Meta:
        """DocType metadata configuration."""

        # API exposure - enables auto-generated CRUD endpoints
        api_resource: ClassVar[bool] = True

        # Hide from Desk UI sidebar (internal system DocType)
        show_in_desk: ClassVar[bool] = False

        # List view configuration for Admin UI
        list_fields: ClassVar[list[str]] = [
            "job_id",
            "job_name",
            "status",
            "enqueued_at",
            "error",
        ]

        # Authentication and authorization
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True

        # Permissions (read-only for most users)
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],
            "write": ["Admin"],
            "create": ["Admin"],
            "delete": ["Admin"],
        }


__all__ = ["JobLog"]

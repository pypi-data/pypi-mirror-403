"""JobLogger - Service for logging job execution status.

This module provides the JobLogger service that tracks job
execution through the queued → running → success/failed lifecycle.

Example:
    >>> logger = InMemoryJobLogger()
    >>> log = await logger.log_enqueue("job-123", "send_email")
    >>> await logger.log_start("job-123")
    >>> await logger.log_success("job-123", result={"sent": True})
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

from framework_m.core.doctypes.job_log import JobLog


class JobLoggerProtocol(Protocol):
    """Protocol for job execution logging.

    Defines the interface for logging job status transitions.
    Implementations may store in memory, database, or external service.
    """

    async def log_enqueue(self, job_id: str, job_name: str) -> JobLog:
        """Log that a job was enqueued.

        Args:
            job_id: Unique job identifier
            job_name: Name of the job function

        Returns:
            Created JobLog entry
        """
        ...

    async def log_start(self, job_id: str) -> JobLog | None:
        """Log that a job started executing.

        Args:
            job_id: Job identifier

        Returns:
            Updated JobLog or None if not found
        """
        ...

    async def log_success(
        self, job_id: str, result: dict[str, Any] | None = None
    ) -> JobLog | None:
        """Log that a job completed successfully.

        Args:
            job_id: Job identifier
            result: Optional job result data

        Returns:
            Updated JobLog or None if not found
        """
        ...

    async def log_failure(self, job_id: str, error: str) -> JobLog | None:
        """Log that a job failed.

        Args:
            job_id: Job identifier
            error: Error message

        Returns:
            Updated JobLog or None if not found
        """
        ...

    async def get_log(self, job_id: str) -> JobLog | None:
        """Get a job log by ID.

        Args:
            job_id: Job identifier

        Returns:
            JobLog or None if not found
        """
        ...


class InMemoryJobLogger:
    """In-memory job logger for development and testing.

    Stores job logs in memory. For production, use a database-backed
    implementation.
    """

    def __init__(self) -> None:
        """Initialize with empty log storage."""
        self._logs: dict[str, JobLog] = {}

    async def log_enqueue(self, job_id: str, job_name: str) -> JobLog:
        """Log that a job was enqueued."""
        log = JobLog(
            job_id=job_id,
            job_name=job_name,
            status="queued",
        )
        self._logs[job_id] = log
        return log

    async def log_start(self, job_id: str) -> JobLog | None:
        """Log that a job started executing."""
        log = self._logs.get(job_id)
        if log is None:
            return None

        # Update status - create new instance since Pydantic is immutable
        updated = JobLog(
            job_id=log.job_id,
            job_name=log.job_name,
            status="running",
            enqueued_at=log.enqueued_at,
            started_at=datetime.now(UTC),
        )
        self._logs[job_id] = updated
        return updated

    async def log_success(
        self, job_id: str, result: dict[str, Any] | None = None
    ) -> JobLog | None:
        """Log that a job completed successfully."""
        log = self._logs.get(job_id)
        if log is None:
            return None

        updated = JobLog(
            job_id=log.job_id,
            job_name=log.job_name,
            status="success",
            enqueued_at=log.enqueued_at,
            started_at=log.started_at,
            completed_at=datetime.now(UTC),
            result=result,
        )
        self._logs[job_id] = updated
        return updated

    async def log_failure(self, job_id: str, error: str) -> JobLog | None:
        """Log that a job failed."""
        log = self._logs.get(job_id)
        if log is None:
            return None

        updated = JobLog(
            job_id=log.job_id,
            job_name=log.job_name,
            status="failed",
            enqueued_at=log.enqueued_at,
            started_at=log.started_at,
            completed_at=datetime.now(UTC),
            error=error,
        )
        self._logs[job_id] = updated
        return updated

    async def get_log(self, job_id: str) -> JobLog | None:
        """Get a job log by ID."""
        return self._logs.get(job_id)


# Convenience type alias
JobLogger = InMemoryJobLogger

__all__ = [
    "InMemoryJobLogger",
    "JobLogger",
    "JobLoggerProtocol",
]

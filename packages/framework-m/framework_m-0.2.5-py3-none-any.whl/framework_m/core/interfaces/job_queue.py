"""Job Queue Protocol - Core interface for background job processing.

This module defines the JobQueueProtocol for async task processing.
Supports various backends: Arq (Redis), Celery, etc.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field, computed_field


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class JobStatus(StrEnum):
    """Status of a background job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobInfo(BaseModel):
    """Information about a background job.

    Tracks the lifecycle and result of a queued job.

    Attributes:
        id: Unique job identifier
        name: Job function name
        status: Current job status
        enqueued_at: When the job was added to queue
        started_at: When job execution started (optional)
        completed_at: When job finished (optional)
        result: Job result on success (optional)
        error: Error message on failure (optional)
    """

    id: str
    name: str
    status: JobStatus
    enqueued_at: datetime = Field(default_factory=_utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_complete(self) -> bool:
        """Check if job has finished (success, failed, or cancelled)."""
        return self.status in (JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED)


class JobQueueProtocol(Protocol):
    """Protocol defining the contract for job queue implementations.

    This is the primary port for background task processing in the
    hexagonal architecture.

    Implementations include:
    - ArqJobQueue: Redis-backed queue using Arq
    - CeleryJobQueue: Celery distributed task queue

    Example usage:
        queue: JobQueueProtocol = container.get(JobQueueProtocol)

        # Enqueue a job
        job_id = await queue.enqueue("send_email", to="user@example.com")

        # Check status
        job = await queue.get_status(job_id)
        if job.is_complete:
            print(f"Job finished: {job.result}")

        # Schedule recurring job
        await queue.schedule("cleanup_temp", cron="0 0 * * *")
    """

    async def enqueue(self, job_name: str, **kwargs: Any) -> str:
        """Add a job to the queue for immediate processing.

        Args:
            job_name: Name of the registered job function
            **kwargs: Arguments to pass to the job function

        Returns:
            Unique job ID for tracking
        """
        ...

    async def schedule(self, job_name: str, cron: str, **kwargs: Any) -> str:
        """Schedule a recurring job using cron syntax.

        Args:
            job_name: Name of the registered job function
            cron: Cron expression (e.g., "0 0 * * *" for daily at midnight)
            **kwargs: Arguments to pass to the job function

        Returns:
            Schedule ID for tracking/cancellation
        """
        ...

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending or running job.

        Args:
            job_id: ID of the job to cancel

        Returns:
            True if job was cancelled, False if already completed
        """
        ...

    async def get_status(self, job_id: str) -> JobInfo | None:
        """Get current status and info for a job.

        Args:
            job_id: ID of the job to check

        Returns:
            JobInfo if job exists, None otherwise
        """
        ...

    async def retry(self, job_id: str) -> str:
        """Retry a failed job.

        Creates a new job with the same parameters.

        Args:
            job_id: ID of the failed job to retry

        Returns:
            New job ID for the retry

        Raises:
            ValueError: If original job not found or wasn't failed
        """
        ...


__all__ = [
    "JobInfo",
    "JobQueueProtocol",
    "JobStatus",
]

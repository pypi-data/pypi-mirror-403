"""In-Memory Job Queue - Development/testing implementation.

This module provides an in-memory implementation of JobQueueProtocol
for local development and testing without external dependencies.

Jobs are executed immediately in the same process using asyncio.
For production, use Taskiq with NATS JetStream.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from framework_m.adapters.jobs.job_logger import (
    InMemoryJobLogger,
    JobLogger,
    JobLoggerProtocol,
)
from framework_m.core.interfaces.job_queue import JobInfo, JobStatus


class InMemoryJobQueue:
    """In-memory job queue for development and testing.

    Implements JobQueueProtocol using asyncio for immediate execution.
    Jobs run in the background without blocking the caller.

    Note:
        This implementation is NOT suitable for production:
        - Jobs are lost on process restart
        - No distributed execution
        - Scheduled jobs use asyncio.sleep (not persistent)

    Example:
        >>> queue = InMemoryJobQueue()
        >>> queue.register_job("send_email", send_email_handler)
        >>> job_id = await queue.enqueue("send_email", to="user@example.com")
        >>> status = await queue.get_status(job_id)
    """

    def __init__(self) -> None:
        """Initialize the in-memory job queue."""
        self._jobs: dict[str, JobInfo] = {}
        self._job_handlers: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._job_kwargs: dict[str, dict[str, Any]] = {}
        self._running_tasks: dict[str, asyncio.Task[Any]] = {}
        self._scheduled_jobs: dict[str, asyncio.Task[Any]] = {}

    def register_job(
        self, job_name: str, handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """Register a job handler function.

        Args:
            job_name: Name to register the job under
            handler: Async function to call when job is executed
        """
        self._job_handlers[job_name] = handler

    async def enqueue(self, job_name: str, **kwargs: Any) -> str:
        """Add a job to the queue for immediate processing.

        The job is executed in a background task.

        Args:
            job_name: Name of the registered job function
            **kwargs: Arguments to pass to the job function

        Returns:
            Unique job ID for tracking

        Raises:
            ValueError: If job_name is not registered
        """
        if job_name not in self._job_handlers:
            raise ValueError(f"Job '{job_name}' is not registered")

        job_id = str(uuid4())
        job_info = JobInfo(
            id=job_id,
            name=job_name,
            status=JobStatus.PENDING,
            enqueued_at=datetime.now(UTC),
        )
        self._jobs[job_id] = job_info
        self._job_kwargs[job_id] = kwargs

        # Execute in background
        task = asyncio.create_task(self._execute_job(job_id, job_name, kwargs))
        self._running_tasks[job_id] = task

        return job_id

    async def _execute_job(
        self, job_id: str, job_name: str, kwargs: dict[str, Any]
    ) -> None:
        """Execute a job and update its status.

        Args:
            job_id: The job's unique ID
            job_name: Name of the job handler
            kwargs: Arguments to pass to the handler
        """
        job_info = self._jobs[job_id]
        job_info.status = JobStatus.RUNNING
        job_info.started_at = datetime.now(UTC)

        try:
            handler = self._job_handlers[job_name]
            result = await handler(**kwargs)
            job_info.status = JobStatus.SUCCESS
            job_info.result = result if isinstance(result, dict) else {"result": result}
        except asyncio.CancelledError:
            job_info.status = JobStatus.CANCELLED
        except Exception as e:
            job_info.status = JobStatus.FAILED
            job_info.error = str(e)
        finally:
            job_info.completed_at = datetime.now(UTC)
            self._running_tasks.pop(job_id, None)

    async def schedule(self, job_name: str, cron: str, **kwargs: Any) -> str:
        """Schedule a recurring job using cron syntax.

        Note: In-memory implementation uses simplified scheduling.
        Only supports basic intervals for development purposes.

        Args:
            job_name: Name of the registered job function
            cron: Cron expression (simplified: only interval in seconds for dev)
            **kwargs: Arguments to pass to the job function

        Returns:
            Schedule ID for tracking/cancellation
        """
        if job_name not in self._job_handlers:
            raise ValueError(f"Job '{job_name}' is not registered")

        schedule_id = str(uuid4())

        # For in-memory, we'll just store the schedule info
        # Real implementation would parse cron and schedule appropriately
        job_info = JobInfo(
            id=schedule_id,
            name=f"scheduled:{job_name}",
            status=JobStatus.PENDING,
            enqueued_at=datetime.now(UTC),
        )
        self._jobs[schedule_id] = job_info
        self._job_kwargs[schedule_id] = {"cron": cron, **kwargs}

        return schedule_id

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending or running job.

        Args:
            job_id: ID of the job to cancel

        Returns:
            True if job was cancelled, False if already completed or not found
        """
        job_info = self._jobs.get(job_id)
        if job_info is None:
            return False

        if job_info.is_complete:
            return False

        # Cancel running task if exists
        task = self._running_tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        # Cancel scheduled job if exists
        scheduled_task = self._scheduled_jobs.get(job_id)
        if scheduled_task and not scheduled_task.done():
            scheduled_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await scheduled_task

        job_info.status = JobStatus.CANCELLED
        job_info.completed_at = datetime.now(UTC)
        return True

    async def get_status(self, job_id: str) -> JobInfo | None:
        """Get current status and info for a job.

        Args:
            job_id: ID of the job to check

        Returns:
            JobInfo if job exists, None otherwise
        """
        return self._jobs.get(job_id)

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
        job_info = self._jobs.get(job_id)
        if job_info is None:
            raise ValueError(f"Job '{job_id}' not found")

        if job_info.status != JobStatus.FAILED:
            raise ValueError(
                f"Job '{job_id}' is not failed (status: {job_info.status})"
            )

        # Get original kwargs and re-enqueue
        original_kwargs = self._job_kwargs.get(job_id, {})
        job_name = job_info.name

        return await self.enqueue(job_name, **original_kwargs)

    def list_jobs(self, status: JobStatus | None = None) -> list[JobInfo]:
        """List all jobs, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of JobInfo objects
        """
        if status is None:
            return list(self._jobs.values())
        return [job for job in self._jobs.values() if job.status == status]

    def clear(self) -> None:
        """Clear all jobs and cancel running tasks.

        Useful for testing cleanup.
        """
        for task in self._running_tasks.values():
            if not task.done():
                task.cancel()
        for task in self._scheduled_jobs.values():
            if not task.done():
                task.cancel()

        self._jobs.clear()
        self._job_kwargs.clear()
        self._running_tasks.clear()
        self._scheduled_jobs.clear()


__all__ = [
    "InMemoryJobLogger",
    "InMemoryJobQueue",
    "JobLogger",
    "JobLoggerProtocol",
]

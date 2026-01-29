"""Taskiq Job Queue Adapter - Production implementation with NATS JetStream.

This module provides a production-ready implementation of JobQueueProtocol
using Taskiq with NATS JetStream for reliable, cross-platform job processing.

For local development without NATS, use InMemoryJobQueue instead.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from framework_m.core.interfaces.job_queue import JobInfo, JobStatus
from framework_m.core.types.job_context import JobContext, JobMetadata

# Type variables for decorator
P = ParamSpec("P")
R = TypeVar("R")


async def get_job_context(context: Any | None = None) -> JobContext:
    """Taskiq dependency that provides JobContext to job functions.

    This dependency can be used with TaskiqDepends() to inject
    context into job functions, providing access to job metadata.

    Args:
        context: Taskiq Context (injected by Taskiq if using TaskiqDepends)

    Returns:
        JobContext with metadata and optional services

    Example:
        >>> from taskiq import TaskiqDepends
        >>> @job(name="send_email")
        ... async def send_email(
        ...     to: str,
        ...     ctx: JobContext = TaskiqDepends(get_job_context),
        ... ) -> bool:
        ...     print(f"Job ID: {ctx.metadata.job_id}")
        ...     return True
    """
    # If no context provided (testing), return minimal context
    if context is None:
        return JobContext(
            metadata=JobMetadata(
                job_id="test-job-id",
                job_name="test_job",
                enqueued_at=datetime.now(UTC),
                started_at=datetime.now(UTC),
            )
        )

    # Extract from Taskiq Context
    task_id = getattr(context.message, "task_id", "unknown")
    task_name = getattr(context.message, "task_name", "unknown")

    # Extract user_id from labels if provided
    labels = getattr(context.message, "labels", {})
    user_id = labels.get("user_id") if labels else None

    return JobContext(
        metadata=JobMetadata(
            job_id=task_id,
            job_name=task_name,
            enqueued_at=datetime.now(UTC),  # Approximation
            started_at=datetime.now(UTC),
            user_id=user_id,
        ),
        # db_session and event_bus can be added when needed
        db_session=None,
        event_bus=None,
    )


def build_cron_expression(
    *,
    minute: int | str = "*",
    hour: int | str = "*",
    day: int | str = "*",
    month: int | str = "*",
    day_of_week: int | str = "*",
) -> str:
    """Build a cron expression from component parts.

    Args:
        minute: Minute (0-59) or expression (e.g., "*/15")
        hour: Hour (0-23) or expression (e.g., "9-17")
        day: Day of month (1-31)
        month: Month (1-12)
        day_of_week: Day of week (0-6, 0=Sunday)

    Returns:
        Cron expression string (e.g., "0 9 * * *")

    Example:
        >>> build_cron_expression(hour=9, minute=0)
        '0 9 * * *'
        >>> build_cron_expression(hour="*/6", minute=0)
        '0 */6 * * *'
    """
    return f"{minute} {hour} {day} {month} {day_of_week}"


def cron(
    job_name: str,
    *,
    minute: int | str = "*",
    hour: int | str = "*",
    day: int | str = "*",
    month: int | str = "*",
    day_of_week: int | str = "*",
) -> dict[str, Any]:
    """Create a cron schedule for a job.

    This creates a schedule definition that can be loaded into
    Taskiq's scheduler at worker startup.

    Args:
        job_name: Name of the job to schedule
        minute: Minute (0-59) or expression
        hour: Hour (0-23) or expression
        day: Day of month (1-31)
        month: Month (1-12)
        day_of_week: Day of week (0-6)

    Returns:
        Schedule definition dict

    Example:
        >>> # Daily at 9:00 AM
        >>> cron("send_daily_report", hour=9, minute=0)
        >>> # Every 6 hours
        >>> cron("cleanup", hour="*/6", minute=0)
        >>> # Monday at 2:00 PM
        >>> cron("weekly_task", hour=14, minute=0, day_of_week=1)
    """
    cron_expr = build_cron_expression(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )

    return {
        "task_name": job_name,
        "cron": cron_expr,
    }


class JobRegistry:
    """Registry for job handlers.

    Stores mapping of job names to handler functions.
    Used for job discovery and lookup.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._handlers: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        handler: Callable[..., Awaitable[Any]],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a job handler.

        Args:
            name: Job name for lookup
            handler: Async function to execute
            metadata: Optional job metadata (retry, timeout, etc.)
        """
        self._handlers[name] = handler
        self._metadata[name] = metadata or {}

    def get(self, name: str) -> Callable[..., Awaitable[Any]] | None:
        """Get a registered handler by name.

        Args:
            name: Job name

        Returns:
            Handler function or None if not found
        """
        return self._handlers.get(name)

    def get_metadata(self, name: str) -> dict[str, Any]:
        """Get job metadata by name.

        Args:
            name: Job name

        Returns:
            Metadata dict (empty if not found)
        """
        return self._metadata.get(name, {})

    def list(self) -> list[str]:
        """List all registered job names.

        Returns:
            List of job names
        """
        return list(self._handlers.keys())


# Global registry singleton
_global_registry: JobRegistry | None = None


def get_global_registry() -> JobRegistry:
    """Get the global job registry singleton.

    Returns:
        The global JobRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = JobRegistry()
    return _global_registry


def job(
    name: str,
    *,
    retry: int = 3,
    timeout: int = 300,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator to register a function as a background job.

    This decorator registers the function in the global JobRegistry
    and attaches metadata for Taskiq configuration.

    Args:
        name: Job name (must be unique)
        retry: Number of retries on failure (default: 3)
        timeout: Job timeout in seconds (default: 300)

    Returns:
        Decorator function

    Example:
        >>> @job(name="send_email", retry=5)
        ... async def send_email(to: str, subject: str) -> bool:
        ...     # Job logic
        ...     return True
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        # Store metadata on function
        func._job_meta = {  # type: ignore[attr-defined]
            "name": name,
            "retry": retry,
            "timeout": timeout,
        }

        # Register in global registry
        registry = get_global_registry()
        registry.register(name, func, func._job_meta)  # type: ignore[attr-defined]

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return await func(*args, **kwargs)

        # Copy metadata to wrapper
        wrapper._job_meta = func._job_meta  # type: ignore[attr-defined]

        return wrapper

    return decorator


class TaskiqJobQueueAdapter:
    """Job queue adapter using Taskiq with NATS JetStream.

    Implements JobQueueProtocol for production use with NATS.

    Example:
        >>> from taskiq_nats import PullBasedJetStreamBroker
        >>> broker = PullBasedJetStreamBroker(servers=["nats://localhost:4222"])
        >>> adapter = TaskiqJobQueueAdapter(broker=broker)
        >>> job_id = await adapter.enqueue("send_email", to="user@example.com")
    """

    def __init__(
        self,
        broker: Any | None = None,
        nats_url: str | None = None,
    ) -> None:
        """Initialize the Taskiq adapter.

        Args:
            broker: Optional pre-configured Taskiq broker
            nats_url: NATS server URL (used if broker not provided)
        """
        self._nats_url = nats_url or os.environ.get("NATS_URL", "nats://localhost:4222")
        self._broker = broker or self._create_broker()
        self._tasks: dict[str, Any] = {}
        self._job_store: dict[str, JobInfo] = {}

    def _create_broker(self) -> Any:
        """Create a Taskiq broker with NATS JetStream.

        Returns:
            Configured PullBasedJetStreamBroker
        """
        try:
            from taskiq_nats import PullBasedJetStreamBroker

            return PullBasedJetStreamBroker(
                servers=[self._nats_url],
                stream_name="framework_m_jobs",
            )
        except ImportError as e:
            raise ImportError(
                "taskiq-nats is required for TaskiqJobQueueAdapter. "
                "Install with: pip install taskiq-nats"
            ) from e

    def register_task(self, name: str, task: Any) -> None:
        """Register a Taskiq task for enqueuing.

        Args:
            name: Task name
            task: Taskiq task object (result of @broker.task)
        """
        self._tasks[name] = task

    async def enqueue(self, job_name: str, **kwargs: Any) -> str:
        """Add a job to the queue for processing.

        Args:
            job_name: Name of the registered job
            **kwargs: Arguments to pass to the job

        Returns:
            Job ID for tracking

        Raises:
            ValueError: If job is not registered
        """
        task = self._tasks.get(job_name)
        if task is None:
            raise ValueError(f"Job '{job_name}' is not registered")

        # Enqueue via Taskiq
        result = await task.kiq(**kwargs)

        # Store job info
        job_id: str = str(result.task_id)
        self._job_store[job_id] = JobInfo(
            id=job_id,
            name=job_name,
            status=JobStatus.PENDING,
            enqueued_at=datetime.now(UTC),
        )

        return job_id

    async def schedule(self, job_name: str, cron: str, **kwargs: Any) -> str:
        """Schedule a recurring job.

        Args:
            job_name: Name of the registered job
            cron: Cron expression
            **kwargs: Arguments for the job

        Returns:
            Schedule ID

        Raises:
            ValueError: If job is not registered
        """
        task = self._tasks.get(job_name)
        if task is None:
            raise ValueError(f"Job '{job_name}' is not registered")

        # For now, store schedule info
        # Full implementation would use TaskiqScheduler
        from uuid import uuid4

        schedule_id = str(uuid4())
        self._job_store[schedule_id] = JobInfo(
            id=schedule_id,
            name=f"scheduled:{job_name}",
            status=JobStatus.PENDING,
            enqueued_at=datetime.now(UTC),
        )

        return schedule_id

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending or running job.

        Args:
            job_id: ID of the job to cancel

        Returns:
            True if cancelled, False otherwise
        """
        if self._broker.result_backend is None:
            return False

        job_info = self._job_store.get(job_id)
        if job_info is None:
            return False

        if job_info.is_complete:
            return False

        # Mark as cancelled
        job_info.status = JobStatus.CANCELLED
        job_info.completed_at = datetime.now(UTC)
        return True

    async def get_status(self, job_id: str) -> JobInfo | None:
        """Get job status.

        Args:
            job_id: Job ID

        Returns:
            JobInfo or None if not found
        """
        # Check local store first
        if job_id in self._job_store:
            return self._job_store[job_id]

        # Try to get from result backend
        if self._broker.result_backend is None:
            return None

        try:
            result = await self._broker.result_backend.get_result(job_id)

            if result.is_ready:
                status = JobStatus.FAILED if result.is_err else JobStatus.SUCCESS
                return JobInfo(
                    id=job_id,
                    name="unknown",  # Result backend doesn't store name
                    status=status,
                    enqueued_at=datetime.now(UTC),
                    completed_at=datetime.now(UTC),
                    result=result.return_value if not result.is_err else None,
                    error=str(result.return_value) if result.is_err else None,
                )
            else:
                return JobInfo(
                    id=job_id,
                    name="unknown",
                    status=JobStatus.RUNNING,
                    enqueued_at=datetime.now(UTC),
                )
        except Exception:
            return None

    async def retry(self, job_id: str) -> str:
        """Retry a failed job.

        Args:
            job_id: ID of the failed job

        Returns:
            New job ID

        Raises:
            ValueError: If job not found or not failed
        """
        job_info = self._job_store.get(job_id)
        if job_info is None:
            raise ValueError(f"Job '{job_id}' not found")

        if job_info.status != JobStatus.FAILED:
            raise ValueError(
                f"Job '{job_id}' is not failed (status: {job_info.status})"
            )

        # Re-enqueue the job
        job_name = job_info.name
        return await self.enqueue(job_name)


def create_taskiq_broker(
    nats_url: str | None = None,
    stream_name: str = "framework_m_jobs",
) -> Any:
    """Create a Taskiq broker with NATS JetStream.

    Factory function for creating properly configured brokers.

    Args:
        nats_url: NATS server URL (defaults to NATS_URL env var)
        stream_name: JetStream stream name

    Returns:
        Configured PullBasedJetStreamBroker
    """
    from taskiq_nats import PullBasedJetStreamBroker

    url = nats_url or os.environ.get("NATS_URL", "nats://localhost:4222")
    return PullBasedJetStreamBroker(servers=[url], stream_name=stream_name)


__all__ = [
    "JobContext",
    "JobRegistry",
    "TaskiqJobQueueAdapter",
    "build_cron_expression",
    "create_taskiq_broker",
    "cron",
    "get_global_registry",
    "get_job_context",
    "job",
]

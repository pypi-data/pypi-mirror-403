"""Job Management API - REST endpoints for job monitoring and control.

This module provides Litestar endpoints for managing background jobs:
- List jobs
- Get job status
- Cancel jobs
- Retry failed jobs

Example:
    >>> from litestar import Litestar
    >>> from framework_m.adapters.web.job_router import create_job_router
    >>> router = create_job_router()
    >>> app = Litestar(route_handlers=[router])
"""

from __future__ import annotations

from typing import Any

from litestar import Router, get, post
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_400_BAD_REQUEST

from framework_m.adapters.jobs import InMemoryJobQueue, JobLogger

# Module-level instances (will be initialized on first use or dependency injection)
_job_queue: InMemoryJobQueue | None = None
_job_logger: JobLogger | None = None


def get_job_queue() -> InMemoryJobQueue:
    """Get the job queue instance.

    Returns:
        Job queue instance
    """
    global _job_queue
    if _job_queue is None:
        _job_queue = InMemoryJobQueue()
    return _job_queue


def get_job_logger() -> JobLogger:
    """Get the job logger instance.

    Returns:
        Job logger instance
    """
    global _job_logger
    if _job_logger is None:
        _job_logger = JobLogger()
    return _job_logger


@get("/")
async def list_jobs(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List jobs with optional status filter.

    Args:
        status: Optional status filter (queued, running, success, failed)
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip

    Returns:
        Dict with jobs list
    """
    logger = get_job_logger()

    # Get all logs from logger
    logs = list(logger._logs.values())

    # Filter by status if provided
    if status:
        logs = [log for log in logs if log.status == status]

    # Apply pagination
    paginated = logs[offset : offset + limit]

    return {
        "jobs": [
            {
                "job_id": log.job_id,
                "job_name": log.job_name,
                "status": log.status,
                "enqueued_at": log.enqueued_at.isoformat(),
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "completed_at": (
                    log.completed_at.isoformat() if log.completed_at else None
                ),
                "error": log.error,
            }
            for log in paginated
        ],
        "total": len(logs),
        "limit": limit,
        "offset": offset,
    }


@get("/{job_id:str}")
async def get_job_status(job_id: str) -> dict[str, Any]:
    """Get status and details for a specific job.

    Args:
        job_id: Job identifier

    Returns:
        Job info dict

    Raises:
        NotFoundException: If job not found
    """
    queue = get_job_queue()
    job = await queue.get_status(job_id)

    if job is None:
        raise NotFoundException(detail=f"Job '{job_id}' not found")

    return {
        "id": job.id,
        "name": job.name,
        "status": job.status.value,
        "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error": job.error,
        "result": job.result,
    }


@post("/{job_id:str}/cancel")
async def cancel_job(job_id: str) -> dict[str, Any]:
    """Cancel a pending or running job.

    Args:
        job_id: Job identifier

    Returns:
        Dict with cancelled status

    Raises:
        NotFoundException: If job not found or already completed
    """
    queue = get_job_queue()
    cancelled = await queue.cancel(job_id)

    if not cancelled:
        raise NotFoundException(
            detail=f"Job '{job_id}' not found or already completed",
        )

    return {"cancelled": True, "job_id": job_id}


@post("/{job_id:str}/retry")
async def retry_job(job_id: str) -> dict[str, Any]:
    """Retry a failed job.

    Creates a new job with the same parameters.

    Args:
        job_id: Job identifier of the failed job

    Returns:
        Dict with new job ID

    Raises:
        ClientException: If job not failed or not found
    """
    from litestar.exceptions import ClientException

    queue = get_job_queue()

    try:
        new_job_id = await queue.retry(job_id)
    except ValueError as e:
        raise ClientException(status_code=HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return {"new_job_id": new_job_id, "original_job_id": job_id}


def create_job_router() -> Router:
    """Create the job management router.

    Returns:
        Litestar Router with job endpoints
    """
    return Router(
        path="/api/v1/jobs",
        route_handlers=[list_jobs, get_job_status, cancel_job, retry_job],
        tags=["jobs"],
    )


__all__ = [
    "cancel_job",
    "create_job_router",
    "get_job_status",
    "list_jobs",
    "retry_job",
]

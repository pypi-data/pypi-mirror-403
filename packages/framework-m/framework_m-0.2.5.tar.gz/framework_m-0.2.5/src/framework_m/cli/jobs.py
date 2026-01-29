"""Job CLI Commands - Job management from command line.

This module provides CLI commands for managing background jobs:
- job list - List registered jobs
- job run - Run a job immediately
- job status - Check job status

Usage:
    m job list              # List all registered jobs
    m job run send_email    # Run job immediately
    m job status job-123    # Check job status
"""

from __future__ import annotations

import asyncio
import sys
from typing import Annotated, Any

import cyclopts

job_app = cyclopts.App(name="job", help="Job management commands")


@job_app.command(name="list")
def list_jobs() -> None:
    """List all registered job handlers.

    Shows all jobs that have been registered with the @job decorator.
    """
    from framework_m.adapters.jobs.taskiq_adapter import get_global_registry

    registry = get_global_registry()
    jobs = registry.list()

    if not jobs:
        print("No jobs registered.")
        print("Register jobs using the @job decorator:")
        print("  @job(name='my_job')")
        print("  async def my_job(): ...")
        return

    print(f"Registered jobs ({len(jobs)}):")
    print("-" * 40)

    for job_name in sorted(jobs):
        metadata = registry.get_metadata(job_name)
        retry = metadata.get("retry", 3)
        timeout = metadata.get("timeout", 300)
        print(f"  {job_name}")
        print(f"    retry: {retry}, timeout: {timeout}s")


@job_app.command(name="run")
def run_job(
    name: Annotated[str, cyclopts.Parameter(help="Name of the job to run")],
    kwargs_json: Annotated[
        str,
        cyclopts.Parameter(name="--kwargs", help="JSON string of keyword arguments"),
    ] = "{}",
) -> None:
    """Run a job immediately.

    Enqueues the job for immediate processing. The job runs
    asynchronously in the worker process.
    """
    import json

    from framework_m.adapters.jobs.taskiq_adapter import get_global_registry

    registry = get_global_registry()

    if name not in registry.list():
        print(f"Error: Job '{name}' is not registered.", file=sys.stderr)
        print("Use 'job list' to see available jobs.", file=sys.stderr)
        raise SystemExit(1)

    # Parse kwargs
    try:
        kwargs: dict[str, Any] = json.loads(kwargs_json)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in --kwargs: {e}", file=sys.stderr)
        raise SystemExit(1) from e

    async def _run() -> str:
        from framework_m.adapters.factory import get_job_queue

        queue = get_job_queue()
        job_id = await queue.enqueue(name, **kwargs)
        return job_id

    print(f"Enqueueing job '{name}'...")
    job_id = asyncio.run(_run())
    print(f"Job enqueued: {job_id}")
    print(f"Use 'job status {job_id}' to check status.")


@job_app.command(name="status")
def job_status(
    job_id: Annotated[str, cyclopts.Parameter(help="Job ID to check")],
) -> None:
    """Check the status of a job.

    Shows the current status, timestamps, and result/error
    for a specific job.
    """

    async def get_status() -> None:
        from framework_m.adapters.factory import get_job_queue

        queue = get_job_queue()
        status_info = await queue.get_status(job_id)

        if status_info is None:
            print(f"Job '{job_id}' not found.", file=sys.stderr)
            raise SystemExit(1)

        print(f"Job: {status_info.name}")
        print(f"ID: {status_info.id}")
        print(f"Status: {status_info.status.value}")

        if status_info.enqueued_at:
            print(f"Enqueued: {status_info.enqueued_at.isoformat()}")
        if status_info.started_at:
            print(f"Started: {status_info.started_at.isoformat()}")
        if status_info.completed_at:
            print(f"Completed: {status_info.completed_at.isoformat()}")

        if status_info.error:
            print(f"Error: {status_info.error}")
        if status_info.result:
            print(f"Result: {status_info.result}")

    asyncio.run(get_status())


__all__ = [
    "job_app",
]

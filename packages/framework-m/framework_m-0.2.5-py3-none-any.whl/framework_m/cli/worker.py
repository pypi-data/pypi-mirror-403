"""Worker CLI - Background job processing command.

This module provides the `m worker` CLI command for running
Taskiq workers that process background jobs from NATS JetStream.

Usage:
    m worker              # Start worker with default settings
    m worker --concurrency 4  # Start with 4 concurrent workers
"""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Annotated, cast

import cyclopts

if TYPE_CHECKING:
    from taskiq import AsyncBroker

# Default worker configuration
DEFAULT_CONCURRENCY = 4
DEFAULT_NATS_URL = "nats://localhost:4222"


def get_nats_url() -> str:
    """Get NATS URL from environment or default.

    Returns:
        NATS server URL
    """
    return os.environ.get("NATS_URL", DEFAULT_NATS_URL)


def get_broker() -> AsyncBroker:
    """Get or create the Taskiq broker.

    Returns:
        Configured Taskiq broker for NATS JetStream
    """
    from framework_m.adapters.jobs.taskiq_adapter import create_taskiq_broker

    return cast("AsyncBroker", create_taskiq_broker(nats_url=get_nats_url()))


def discover_jobs() -> list[str]:
    """Discover all registered jobs.

    Scans the global job registry for registered job handlers.

    Returns:
        List of registered job names
    """
    from framework_m.adapters.jobs.taskiq_adapter import get_global_registry

    registry = get_global_registry()
    return registry.list()


async def load_scheduled_jobs() -> list[dict[str, str]]:
    """Load enabled scheduled jobs from database.

    Queries the ScheduledJob DocType for enabled jobs and
    returns them in Taskiq schedule format. Also includes
    built-in system jobs like outbox processing.

    Returns:
        List of schedule dicts with 'task_name' and 'cron' keys

    Example:
        >>> schedules = await load_scheduled_jobs()
        >>> # [{"task_name": "daily_report", "cron": "0 9 * * *"}]
    """
    # Built-in system jobs
    schedules: list[dict[str, str]] = [
        # Process outbox entries every minute
        {"task_name": "process_outbox", "cron": "* * * * *"},
    ]

    try:
        from framework_m.core.doctypes.scheduled_job import ScheduledJob

        # Query enabled jobs only
        # Note: This uses the DocType query API from Phase 02
        # If not available yet, gracefully return empty list
        jobs = await ScheduledJob.query().filter(enabled=True).all()  # type: ignore[attr-defined]

        schedules.extend(
            [
                {
                    "task_name": job.name,
                    "cron": job.cron_expression,
                }
                for job in jobs
            ]
        )
    except Exception:
        # If ScheduledJob not available or DB not ready, return built-in only
        # This allows worker to start even without full DocType system
        pass

    return schedules


async def _run_worker_async(
    broker: AsyncBroker,
    concurrency: int = DEFAULT_CONCURRENCY,
) -> None:
    """Run the Taskiq worker asynchronously.

    Args:
        broker: Configured Taskiq broker
        concurrency: Number of concurrent workers
    """
    # Discover and log registered jobs
    jobs = discover_jobs()
    if jobs:
        print(f"Discovered {len(jobs)} jobs: {', '.join(jobs)}")
    else:
        print("No jobs discovered. Register jobs with @job decorator.")

    print(f"Starting worker with concurrency={concurrency}...")
    print(f"NATS URL: {get_nats_url()}")

    try:
        # Import and run the Taskiq receiver
        from taskiq.receiver import Receiver

        # Start the broker first
        await broker.startup()

        # Create receiver with run_startup=False since we already called startup
        finish_event = asyncio.Event()
        receiver = Receiver(broker, max_async_tasks=concurrency, run_startup=False)

        print("Worker listening for jobs... (Ctrl+C to stop)")
        await receiver.listen(finish_event)
    except KeyboardInterrupt:
        print("\nShutting down worker...")
    finally:
        await broker.shutdown()


def run_worker(concurrency: int = DEFAULT_CONCURRENCY) -> None:
    """Run the Taskiq worker (synchronous wrapper).

    Args:
        concurrency: Number of concurrent workers
    """
    broker = get_broker()
    asyncio.run(_run_worker_async(broker, concurrency))


def worker_command(
    concurrency: Annotated[
        int,
        cyclopts.Parameter(name="--concurrency", help="Number of concurrent workers"),
    ] = DEFAULT_CONCURRENCY,
    verbose: Annotated[
        bool,
        cyclopts.Parameter(name="--verbose", help="Enable verbose logging"),
    ] = False,
) -> None:
    """Start the Taskiq worker for processing background jobs.

    The worker connects to NATS JetStream and processes jobs from the queue.
    Set NATS_URL environment variable to configure the NATS server.

    Examples:
        m worker                    # Default concurrency
        m worker --concurrency 8    # 8 concurrent workers
        NATS_URL=nats://prod:4222 m worker
    """
    if verbose:
        print("Verbose mode enabled")

    print("Framework M Worker")
    print("=" * 40)

    run_worker(concurrency=concurrency)


__all__ = [
    "DEFAULT_CONCURRENCY",
    "DEFAULT_NATS_URL",
    "_run_worker_async",
    "discover_jobs",
    "get_broker",
    "get_nats_url",
    "load_scheduled_jobs",
    "run_worker",
    "worker_command",
]

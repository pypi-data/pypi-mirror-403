"""Outbox Worker - Background processing of outbox entries.

This module provides a background job that processes pending
OutboxEntry records, dispatching them to their targets.

Example:
    # Run manually
    await process_outbox(batch_size=100)

    # Scheduled via worker
    cron("process_outbox", minute="*/1")  # Every minute
"""

from __future__ import annotations

import logging
from typing import Any

from framework_m.adapters.jobs.taskiq_adapter import job

logger = logging.getLogger(__name__)


async def dispatch_to_target(entry: Any) -> None:
    """Dispatch an outbox entry to its target.

    Args:
        entry: The OutboxEntry to dispatch

    Raises:
        Exception: If dispatch fails
    """
    target = entry.target

    # Route based on target prefix
    if target.startswith("api."):
        await _dispatch_to_api(target, entry.payload)
    elif target.startswith("event."):
        await _dispatch_to_event_bus(target, entry.payload)
    else:
        logger.warning("Unknown target type: %s", target)


async def _dispatch_to_api(target: str, payload: dict[str, Any]) -> None:
    """Dispatch to an external API endpoint."""

    # Extract API endpoint from target (e.g., "api.payment_gateway")
    api_name = target.replace("api.", "")

    # TODO: Look up API endpoint from configuration
    # For now, log the dispatch
    logger.info("Dispatching to API %s: %s", api_name, payload)

    # Example implementation:
    # async with httpx.AsyncClient() as client:
    #     await client.post(endpoint_url, json=payload)


async def _dispatch_to_event_bus(target: str, payload: dict[str, Any]) -> None:
    """Dispatch to the event bus."""
    from framework_m.adapters.factory import get_event_bus
    from framework_m.core.interfaces.event_bus import Event

    event_type = target.replace("event.", "")
    bus = get_event_bus()

    event = Event(
        type=event_type,
        source="outbox_worker",
        data=payload,
    )

    await bus.publish(event_type, event)
    logger.info("Published event %s from outbox", event_type)


@job(name="process_outbox")
async def process_outbox(batch_size: int = 100) -> dict[str, int]:
    """Process pending outbox entries.

    Fetches pending entries from the outbox table and dispatches
    them to their targets. Entries are marked as processed or
    failed based on the result.

    Args:
        batch_size: Maximum number of entries to process

    Returns:
        Dictionary with processed/failed counts
    """
    from sqlalchemy import MetaData
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    from framework_m.adapters.db.connection import ConnectionFactory
    from framework_m.adapters.db.outbox_repository import (
        OutboxRepository,
        create_outbox_table,
    )

    processed = 0
    failed = 0

    # Get session from ConnectionFactory
    factory = ConnectionFactory()
    engine = factory.get_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]

    # Create outbox table reference
    metadata = MetaData()
    outbox_table = create_outbox_table(metadata)
    repo = OutboxRepository(outbox_table)

    async with async_session() as session:
        pending = await repo.get_pending(session, limit=batch_size)

        if not pending:
            logger.debug("No pending outbox entries")
            return {"processed": 0, "failed": 0}

        logger.info("Processing %d outbox entries", len(pending))

        for entry in pending:
            try:
                await dispatch_to_target(entry)
                await repo.mark_processed(session, entry.id)
                processed += 1
            except Exception as e:
                logger.error(
                    "Failed to process outbox entry %s: %s",
                    entry.id,
                    str(e),
                )
                await repo.mark_failed(session, entry.id, str(e))
                failed += 1

        await session.commit()

    logger.info(
        "Outbox processing complete: %d processed, %d failed", processed, failed
    )
    return {"processed": processed, "failed": failed}


__all__ = [
    "dispatch_to_target",
    "process_outbox",
]

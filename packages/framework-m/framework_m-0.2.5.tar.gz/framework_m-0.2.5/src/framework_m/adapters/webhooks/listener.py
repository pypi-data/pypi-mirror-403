"""Webhook Listener - Subscribes to events and triggers webhook delivery.

This module provides the WebhookListener class that subscribes to
document lifecycle events and dispatches matching webhooks.

Example:
    >>> listener = WebhookListener(event_bus=bus)
    >>> await listener.start()
    >>> # ... listener handles events automatically
    >>> await listener.stop()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from framework_m.core.doctypes.webhook import Webhook
    from framework_m.core.interfaces.event_bus import Event, EventBusProtocol

logger = logging.getLogger(__name__)


class WebhookLoaderProtocol(Protocol):
    """Protocol for loading webhooks from storage."""

    async def load_active_webhooks(self) -> list[Webhook]:
        """Load all active webhooks."""
        ...


class WebhookDelivererProtocol(Protocol):
    """Protocol for delivering webhooks."""

    async def deliver(self, webhook: Webhook, event: Event) -> None:
        """Deliver an event to a webhook endpoint."""
        ...


class InMemoryWebhookLoader:
    """Simple in-memory webhook loader for development."""

    def __init__(self) -> None:
        self._webhooks: list[Webhook] = []

    def add_webhook(self, webhook: Webhook) -> None:
        """Add a webhook to the loader."""
        self._webhooks.append(webhook)

    async def load_active_webhooks(self) -> list[Webhook]:
        """Load all active webhooks."""
        return [w for w in self._webhooks if w.enabled]


class LoggingWebhookDeliverer:
    """Simple logging deliverer for development/testing."""

    async def deliver(self, webhook: Webhook, event: Event) -> None:
        """Log webhook delivery (no actual HTTP call)."""
        logger.info(
            "Would deliver webhook %s to %s for event %s",
            webhook.name,
            webhook.url,
            event.type,
        )


class WebhookListener:
    """Listens to events and dispatches matching webhooks.

    Subscribes to document lifecycle events and triggers webhook
    delivery for matching webhook configurations.

    Example:
        >>> event_bus = get_event_bus()
        >>> listener = WebhookListener(event_bus=event_bus)
        >>> await listener.start()
    """

    def __init__(
        self,
        event_bus: EventBusProtocol,
        webhook_loader: WebhookLoaderProtocol | None = None,
        deliverer: WebhookDelivererProtocol | None = None,
    ) -> None:
        """Initialize the webhook listener.

        Args:
            event_bus: Event bus to subscribe to
            webhook_loader: Loader for fetching active webhooks
            deliverer: Deliverer for sending webhook requests
        """
        self._event_bus = event_bus
        self._webhook_loader = webhook_loader or InMemoryWebhookLoader()
        self._deliverer = deliverer or LoggingWebhookDeliverer()
        self._subscription_id: str | None = None

    async def start(self) -> None:
        """Start listening to events.

        Subscribes to all document events (doc.>).
        """
        # Subscribe to all doc events using pattern
        self._subscription_id = await self._event_bus.subscribe_pattern(
            "doc.>",
            self.handle_event,
        )
        logger.info("Webhook listener started, subscription: %s", self._subscription_id)

    async def stop(self) -> None:
        """Stop listening to events.

        Unsubscribes from events.
        """
        if self._subscription_id:
            await self._event_bus.unsubscribe(self._subscription_id)
            logger.info("Webhook listener stopped")
            self._subscription_id = None

    async def handle_event(self, event: Event) -> None:
        """Handle an incoming event.

        Loads active webhooks, filters by event type and doctype,
        and triggers delivery for matching webhooks.

        Args:
            event: The event to process
        """
        # Load active webhooks
        webhooks = await self._webhook_loader.load_active_webhooks()

        # Filter and deliver
        for webhook in webhooks:
            if self._webhook_matches(webhook, event):
                try:
                    await self._deliverer.deliver(webhook, event)
                    logger.debug(
                        "Delivered webhook %s for event %s",
                        webhook.name,
                        event.type,
                    )
                except Exception as e:
                    logger.error(
                        "Failed to deliver webhook %s: %s",
                        webhook.name,
                        str(e),
                    )

    def _webhook_matches(self, webhook: Webhook, event: Event) -> bool:
        """Check if a webhook matches an event.

        Args:
            webhook: The webhook configuration
            event: The event to check

        Returns:
            True if webhook should receive this event
        """
        # Check event type matches
        if webhook.event != event.type:
            return False

        # Check doctype filter if set
        if webhook.doctype_filter:
            # DocEvent types have 'doctype' attribute
            event_doctype = getattr(event, "doctype", None)
            if event_doctype != webhook.doctype_filter:
                return False

        return True


__all__ = [
    "InMemoryWebhookLoader",
    "LoggingWebhookDeliverer",
    "WebhookDelivererProtocol",
    "WebhookListener",
    "WebhookLoaderProtocol",
]

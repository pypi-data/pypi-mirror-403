"""Webhook Delivery - HTTP delivery with signatures and retries.

This module provides the HttpWebhookDeliverer for sending webhook
notifications to external endpoints with HMAC-SHA256 signatures
and exponential backoff retry logic.

Example:
    >>> deliverer = HttpWebhookDeliverer()
    >>> await deliverer.deliver(webhook, event)
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from framework_m.core.doctypes.webhook import Webhook
    from framework_m.core.interfaces.event_bus import Event

logger = logging.getLogger(__name__)


def generate_signature(payload: bytes, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload.

    Args:
        payload: The request body bytes
        secret: The webhook secret key

    Returns:
        Hex-encoded HMAC-SHA256 signature
    """
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


class HttpWebhookDeliverer:
    """HTTP webhook deliverer with signatures and retries.

    Delivers webhook events to external HTTP endpoints with:
    - HMAC-SHA256 signature verification
    - Configurable timeout (default: 30s)
    - Exponential backoff retry (default: 3 retries)

    Example:
        >>> deliverer = HttpWebhookDeliverer(max_retries=5, timeout=60.0)
        >>> await deliverer.deliver(webhook, event)
    """

    def __init__(
        self,
        max_retries: int = 3,
        timeout: float = 30.0,
        base_delay: float = 1.0,
    ) -> None:
        """Initialize the HTTP webhook deliverer.

        Args:
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            base_delay: Base delay for exponential backoff
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.base_delay = base_delay

    async def deliver(self, webhook: Webhook, event: Event) -> None:
        """Deliver an event to a webhook endpoint.

        Serializes the event to JSON and sends it to the webhook URL
        with optional signature header. Retries on failure with
        exponential backoff.

        Args:
            webhook: The webhook configuration
            event: The event to deliver

        Raises:
            httpx.HTTPError: If delivery fails after all retries
        """
        # Serialize event to JSON
        payload = event.model_dump_json().encode()

        # Build headers
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            **webhook.headers,
        }

        # Add signature if secret is set
        if webhook.secret:
            signature = generate_signature(payload, webhook.secret)
            headers["X-Webhook-Signature"] = signature

        # Attempt delivery with retries
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=webhook.method,
                        url=webhook.url,
                        content=payload,
                        headers=headers,
                    )
                    response.raise_for_status()

                logger.info(
                    "Webhook %s delivered successfully to %s (status: %d)",
                    webhook.name,
                    webhook.url,
                    response.status_code,
                )
                return

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.base_delay * (2**attempt)
                    logger.warning(
                        "Webhook %s delivery failed (attempt %d/%d), "
                        "retrying in %.1fs: %s",
                        webhook.name,
                        attempt + 1,
                        self.max_retries + 1,
                        delay,
                        str(e),
                    )
                    await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(
            "Webhook %s delivery failed after %d attempts: %s",
            webhook.name,
            self.max_retries + 1,
            str(last_error),
        )
        if last_error:
            raise last_error


__all__ = [
    "HttpWebhookDeliverer",
    "generate_signature",
]

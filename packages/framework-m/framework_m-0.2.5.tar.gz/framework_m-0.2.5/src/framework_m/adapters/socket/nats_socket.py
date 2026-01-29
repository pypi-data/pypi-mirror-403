"""NATS Socket Adapter - Distributed WebSocket backplane using NATS.

This module provides the NatsSocketAdapter that implements SocketProtocol
using NATS as the message backplane for Kubernetes/distributed deployments.

Example:
    >>> adapter = NatsSocketAdapter(nats_url="nats://localhost:4222")
    >>> await adapter.connect()
    >>> await adapter.broadcast("doc.updated", {"doctype": "Invoice"})
    >>> await adapter.disconnect()
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import nats
from nats.aio.client import Client as NatsClient
from nats.aio.msg import Msg

logger = logging.getLogger(__name__)


class NatsSocketAdapter:
    """NATS socket adapter for distributed WebSocket backplane.

    Implements SocketProtocol using NATS as the message broker,
    enabling real-time communication across multiple pods in Kubernetes.

    The adapter publishes messages to NATS subjects:
    - `ws.<topic>` for broadcast messages
    - `ws.user.<user_id>` for user-specific messages

    Example:
        >>> adapter = NatsSocketAdapter(nats_url="nats://localhost:4222")
        >>> await adapter.connect()
        >>> await adapter.subscribe("ws.>", message_handler)
        >>> await adapter.broadcast("doc.updated", {"id": "123"})
    """

    def __init__(self, nats_url: str = "nats://localhost:4222") -> None:
        """Initialize the NATS socket adapter.

        Args:
            nats_url: NATS server URL
        """
        self._nats_url = nats_url
        self._nc: NatsClient | None = None
        self._subscriptions: list[Any] = []

    async def connect(self) -> None:
        """Connect to NATS server.

        Establishes connection to the NATS server for publishing
        and subscribing to messages.
        """
        self._nc = await nats.connect(self._nats_url)
        logger.info("Connected to NATS at %s", self._nats_url)

    async def disconnect(self) -> None:
        """Disconnect from NATS server.

        Closes all subscriptions and the connection.
        """
        if self._nc:
            await self._nc.close()
            logger.info("Disconnected from NATS")

    async def broadcast(self, topic: str, message: dict[str, Any]) -> None:
        """Broadcast a message to all subscribers.

        Publishes the message to NATS subject `ws.<topic>`.

        Args:
            topic: The topic to broadcast to
            message: The message payload
        """
        if not self._nc:
            logger.warning("Not connected to NATS, cannot broadcast")
            return

        subject = f"ws.{topic}"
        payload = json.dumps(message).encode()
        await self._nc.publish(subject, payload)
        logger.debug("Broadcast to %s: %s", subject, message)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """Send a message to a specific user.

        Publishes the message to NATS subject `ws.user.<user_id>`.

        Args:
            user_id: The user ID to send to
            message: The message payload
        """
        if not self._nc:
            logger.warning("Not connected to NATS, cannot send to user")
            return

        subject = f"ws.user.{user_id}"
        payload = json.dumps(message).encode()
        await self._nc.publish(subject, payload)
        logger.debug("Sent to user %s: %s", user_id, message)

    async def subscribe(
        self,
        subject: str,
        callback: Callable[[Msg], Awaitable[None]],
    ) -> None:
        """Subscribe to a NATS subject.

        Args:
            subject: NATS subject pattern (e.g., "ws.>")
            callback: Async callback for received messages
        """
        if not self._nc:
            logger.warning("Not connected to NATS, cannot subscribe")
            return

        sub = await self._nc.subscribe(subject, cb=callback)
        self._subscriptions.append(sub)
        logger.info("Subscribed to %s", subject)


__all__ = ["NatsSocketAdapter"]

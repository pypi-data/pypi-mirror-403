"""Webhook DocType - Outgoing webhook configuration.

Stores webhook configurations that subscribe to events and
deliver HTTP notifications to external endpoints.

Example:
    # Create a webhook for order creation
    webhook = Webhook(
        name="order_notification",
        event="doc.created",
        doctype_filter="Order",
        url="https://example.com/webhook",
        secret="my-secret-key",
    )

    # Query active webhooks for an event
    active = await Webhook.query().filter(
        event="doc.created",
        enabled=True,
    ).all()
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class Webhook(BaseDocType):
    """Outgoing webhook configuration.

    Defines webhooks that listen to events and deliver HTTP
    notifications to external endpoints with optional filtering.

    Attributes:
        name: Unique webhook identifier
        event: Event to listen to (e.g., "doc.created", "doc.updated")
        doctype_filter: Optional DocType filter (e.g., "Invoice")
        url: Webhook endpoint URL
        method: HTTP method (POST or PUT)
        headers: Custom HTTP headers to send
        enabled: Whether the webhook is active
        secret: Secret for HMAC-SHA256 signature verification
    """

    # Webhook identification
    name: str = Field(
        ...,
        description="Unique webhook identifier",
        min_length=1,
        max_length=255,
    )

    # Event subscription
    event: str = Field(
        ...,
        description="Event to listen to (e.g., 'doc.created')",
        min_length=1,
    )

    doctype_filter: str | None = Field(
        default=None,
        description="Filter by DocType (e.g., 'Invoice', 'Order')",
    )

    # Delivery configuration
    url: str = Field(
        ...,
        description="Webhook endpoint URL",
        min_length=1,
    )

    method: str = Field(
        default="POST",
        description="HTTP method (POST or PUT)",
    )

    headers: dict[str, Any] = Field(
        default_factory=dict,
        description="Custom HTTP headers to send with request",
    )

    # Status
    enabled: bool = Field(
        default=True,
        description="Whether the webhook is active",
    )

    # Security
    secret: str | None = Field(
        default=None,
        description="Secret for HMAC-SHA256 signature (X-Webhook-Signature header)",
    )

    class Meta:
        """DocType metadata configuration."""

        # Authentication and authorization
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True

        # Permissions (sensitive - admin only for create/delete)
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Manager", "Admin"],
            "write": ["Manager", "Admin"],
            "create": ["Admin"],
            "delete": ["Admin"],
        }


__all__ = ["Webhook"]

"""WebhookLog DocType - Webhook delivery audit log.

Stores webhook delivery attempts for auditing and debugging.
Tracks success/failure status, response codes, and errors.

Example:
    # Log a successful delivery
    log = WebhookLog(
        webhook="order_notification",
        event="doc.created",
        status="success",
        response_code=200,
        response_body='{"received": true}',
    )

    # Log a failed delivery
    log = WebhookLog(
        webhook="order_notification",
        event="doc.created",
        status="failed",
        response_code=500,
        error="Connection timeout after 30s",
    )
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(UTC)


class WebhookLog(BaseDocType):
    """Webhook delivery audit log.

    Records each webhook delivery attempt with status, response,
    and error information for debugging and auditing.

    Attributes:
        webhook: Reference to the Webhook DocType name
        event: The event that triggered the webhook
        status: Delivery status ('success' or 'failed')
        response_code: HTTP response status code
        response_body: HTTP response body (truncated)
        error: Error message if delivery failed
        timestamp: When the delivery was attempted
    """

    # Webhook reference
    webhook: str = Field(
        ...,
        description="Reference to Webhook name",
        min_length=1,
    )

    # Event information
    event: str = Field(
        ...,
        description="Event that triggered the webhook (e.g., 'doc.created')",
        min_length=1,
    )

    # Delivery status
    status: str = Field(
        ...,
        description="Delivery status: 'success' or 'failed'",
    )

    response_code: int = Field(
        ...,
        description="HTTP response status code",
    )

    response_body: str | None = Field(
        default=None,
        description="HTTP response body (may be truncated)",
    )

    error: str | None = Field(
        default=None,
        description="Error message if delivery failed",
    )

    # Timestamp
    timestamp: datetime = Field(
        default_factory=_utc_now,
        description="When the delivery was attempted",
    )

    class Meta:
        """DocType metadata configuration."""

        # Authentication and authorization
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True

        # Permissions (read-only for most users)
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Manager", "Admin"],
            "write": ["Admin"],
            "create": ["Admin"],
            "delete": ["Admin"],
        }


__all__ = ["WebhookLog"]

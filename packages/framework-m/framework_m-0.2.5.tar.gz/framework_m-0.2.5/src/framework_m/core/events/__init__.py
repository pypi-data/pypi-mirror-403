"""Document lifecycle events.

Standard events published when documents are created, updated, deleted,
submitted, or cancelled. These events enable decoupled event-driven
architecture for audit logging, notifications, and integrations.

Example:
    >>> from framework_m.core.events import DocCreated
    >>> event = DocCreated(doctype="Invoice", doc_name="INV-001")
    >>> await event_bus.publish("doc.created", event)
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from framework_m.core.interfaces.event_bus import Event


class DocEvent(Event):
    """Base class for document lifecycle events.

    Extends Event with document-specific fields.

    Attributes:
        doctype: The DocType name (e.g., "Invoice")
        doc_name: The document identifier (e.g., "INV-001")
        user_id: Optional user who triggered the event
    """

    doctype: str
    doc_name: str
    user_id: str | None = None
    # Override data to be optional with None default
    data: dict[str, Any] | None = None


class DocCreated(DocEvent):
    """Event published when a document is created.

    Example:
        >>> event = DocCreated(doctype="Invoice", doc_name="INV-001")
        >>> await bus.publish("doc.created", event)
    """

    type: str = Field(default="doc.created")


class DocUpdated(DocEvent):
    """Event published when a document is updated.

    Includes list of changed field names for efficient handling.

    Example:
        >>> event = DocUpdated(
        ...     doctype="Invoice",
        ...     doc_name="INV-001",
        ...     changed_fields=["status", "total"],
        ... )
    """

    type: str = Field(default="doc.updated")
    changed_fields: list[str] = Field(default_factory=list)


class DocDeleted(DocEvent):
    """Event published when a document is deleted.

    Example:
        >>> event = DocDeleted(doctype="Invoice", doc_name="INV-001")
    """

    type: str = Field(default="doc.deleted")


class DocSubmitted(DocEvent):
    """Event published when a document is submitted.

    Submitted documents typically become immutable or read-only.

    Example:
        >>> event = DocSubmitted(doctype="Invoice", doc_name="INV-001")
    """

    type: str = Field(default="doc.submitted")


class DocCancelled(DocEvent):
    """Event published when a document is cancelled.

    Example:
        >>> event = DocCancelled(
        ...     doctype="Invoice",
        ...     doc_name="INV-001",
        ...     reason="Customer requested cancellation",
        ... )
    """

    type: str = Field(default="doc.cancelled")
    reason: str | None = None


__all__ = [
    "DocCancelled",
    "DocCreated",
    "DocDeleted",
    "DocEvent",
    "DocSubmitted",
    "DocUpdated",
]

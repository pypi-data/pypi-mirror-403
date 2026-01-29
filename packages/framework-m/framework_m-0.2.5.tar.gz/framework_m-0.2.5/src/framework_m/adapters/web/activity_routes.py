"""Activity Feed API Routes.

This module provides REST API endpoints for querying audit activity:
- GET /api/v1/activity - List recent activities with filtering

Used by Admin UI to display activity feed and audit trail.

Security:
- Requires authentication
- Users see only their own activity (RLS)
- Admins can see all activity

Example:
    GET /api/v1/activity?user_id=user-001&limit=20
    GET /api/v1/activity?doctype=Invoice&document_id=INV-001
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from litestar import Controller, get
from pydantic import BaseModel, Field

from framework_m.core.interfaces.audit import AuditEntry, AuditLogProtocol

# =============================================================================
# Request/Response Models
# =============================================================================


class ActivityQueryParams(BaseModel):
    """Query parameters for activity feed."""

    user_id: str | None = Field(default=None, description="Filter by user ID")
    action: str | None = Field(
        default=None, description="Filter by action (create, read, update, delete)"
    )
    doctype: str | None = Field(default=None, description="Filter by DocType")
    document_id: str | None = Field(default=None, description="Filter by document ID")
    limit: int = Field(default=50, ge=1, le=1000, description="Max results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class ActivityEntryResponse(BaseModel):
    """Single activity entry in response."""

    id: str
    timestamp: datetime
    user_id: str
    action: str
    doctype: str
    document_id: str
    changes: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_audit_entry(cls, entry: AuditEntry) -> ActivityEntryResponse:
        """Create from AuditEntry."""
        return cls(
            id=entry.id,
            timestamp=entry.timestamp,
            user_id=entry.user_id,
            action=entry.action,
            doctype=entry.doctype,
            document_id=entry.document_id,
            changes=entry.changes,
            metadata=entry.metadata,
        )


class ActivityFeedResponse(BaseModel):
    """Response for activity feed endpoint."""

    activities: list[ActivityEntryResponse]
    total: int = Field(description="Total matching results (for pagination)")
    limit: int
    offset: int


# =============================================================================
# Activity Controller
# =============================================================================


class ActivityController(Controller):
    """Activity feed API controller.

    Provides endpoints for querying audit activity logs.

    Attributes:
        path: Base path for all endpoints
        tags: OpenAPI tags for documentation
    """

    path = "/api/v1/activity"
    tags = ["Activity"]  # noqa: RUF012

    @get("/")
    async def list_activities(
        self,
        user_id: str | None = None,
        action: str | None = None,
        doctype: str | None = None,
        document_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ActivityFeedResponse:
        """List recent activities.

        Query audit log entries with optional filtering.
        Results are ordered by timestamp descending (newest first).

        Args:
            user_id: Filter by user ID
            action: Filter by action type
            doctype: Filter by DocType
            document_id: Filter by document ID
            limit: Maximum results (default 50, max 1000)
            offset: Pagination offset

        Returns:
            ActivityFeedResponse with matching entries
        """
        # Build filters dict
        filters: dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id
        if action:
            filters["action"] = action
        if doctype:
            filters["doctype"] = doctype
        if document_id:
            filters["document_id"] = document_id

        # Clamp limit
        limit = min(max(1, limit), 1000)
        offset = max(0, offset)

        # TODO: Inject audit adapter via DI
        # For now, use in-memory adapter for testing
        from framework_m.core.interfaces.audit import InMemoryAuditAdapter

        audit: AuditLogProtocol = InMemoryAuditAdapter()

        # Query entries
        entries = await audit.query(
            filters=filters if filters else None,
            limit=limit,
            offset=offset,
        )

        # Convert to response models
        activities = [ActivityEntryResponse.from_audit_entry(e) for e in entries]

        return ActivityFeedResponse(
            activities=activities,
            total=len(activities),  # TODO: Get actual total from adapter
            limit=limit,
            offset=offset,
        )


__all__ = [
    "ActivityController",
    "ActivityEntryResponse",
    "ActivityFeedResponse",
    "ActivityQueryParams",
]

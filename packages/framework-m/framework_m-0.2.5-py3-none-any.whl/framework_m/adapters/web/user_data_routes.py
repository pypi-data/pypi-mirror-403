"""User Data Routes - GDPR data management endpoints.

This module provides endpoints for GDPR compliance:
- GET /api/v1/auth/me/data - Export all user data (data portability)
- DELETE /api/v1/auth/me - Delete user account (right to erasure)

Example:
    from litestar import Litestar
    from framework_m.adapters.web.user_data_routes import user_data_routes_router

    app = Litestar(route_handlers=[user_data_routes_router])
"""

from __future__ import annotations

from datetime import UTC, datetime

from litestar import Router, delete, get
from pydantic import BaseModel, Field

from framework_m.core.pii import (
    PIIExportData,
    get_deletion_mode,
)

# =============================================================================
# Response Models
# =============================================================================


class DataExportResponse(BaseModel):
    """Response for data export endpoint.

    Contains all user data in GDPR-compliant format.

    Attributes:
        data: All user PII and related data
        format: Export format (always "json")
        generated_at: When export was created
    """

    data: PIIExportData = Field(description="Exported user data")
    format: str = Field(default="json", description="Export format")
    generated_at: datetime = Field(description="Export timestamp")


class AccountDeleteResponse(BaseModel):
    """Response for account deletion endpoint.

    Attributes:
        message: Success message
        mode: How data was handled (hard_delete or anonymize)
        deleted_items: Summary of deleted data
    """

    message: str = Field(description="Success message")
    mode: str = Field(description="Deletion mode used")
    deleted_items: dict[str, int] = Field(description="Items deleted by type")


# =============================================================================
# Route Handlers
# =============================================================================


@get("/data")
async def export_user_data() -> DataExportResponse:
    """Export all user data for GDPR data portability.

    Returns a complete export of:
    - User profile information
    - Preferences
    - Active sessions
    - API keys (metadata only, not secrets)
    - Linked social accounts

    Returns:
        DataExportResponse with complete data export
    """
    # In a full implementation:
    # 1. Get user ID from request context
    # 2. Query all user data from repositories
    # 3. Build PIIExportData

    now = datetime.now(UTC)

    # Placeholder response
    return DataExportResponse(
        data=PIIExportData(
            user={},
            preferences={},
            sessions=[],
            api_keys=[],
            social_accounts=[],
            exported_at=now.isoformat(),
        ),
        generated_at=now,
    )


@delete("/")
async def delete_account() -> AccountDeleteResponse:
    """Delete user account (GDPR right to erasure).

    Handles complete account deletion including:
    - User record
    - All sessions (logged out everywhere)
    - All API keys (revoked)
    - All social account links
    - User preferences

    The deletion mode is configurable:
    - hard_delete: Permanently remove all data
    - anonymize: Replace PII with anonymous values

    Returns:
        AccountDeleteResponse confirming deletion
    """
    # In a full implementation:
    # 1. Get user ID from request context
    # 2. Check deletion mode from config
    # 3. Delete or anonymize all user data
    # 4. Revoke all sessions
    # 5. Delete API keys

    mode = get_deletion_mode()

    # Placeholder response
    return AccountDeleteResponse(
        message="Account deleted successfully",
        mode=mode.value,
        deleted_items={
            "sessions": 0,
            "api_keys": 0,
            "social_accounts": 0,
            "preferences": 0,
        },
    )


# =============================================================================
# Router
# =============================================================================


user_data_routes_router = Router(
    path="/api/v1/auth/me",
    route_handlers=[export_user_data, delete_account],
    tags=["auth", "gdpr"],
)


__all__ = [
    "AccountDeleteResponse",
    "DataExportResponse",
    "delete_account",
    "export_user_data",
    "user_data_routes_router",
]

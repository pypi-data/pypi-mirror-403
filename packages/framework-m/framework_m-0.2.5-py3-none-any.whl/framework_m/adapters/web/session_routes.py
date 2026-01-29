"""Session Routes - Session management endpoints.

This module provides REST endpoints for managing user sessions:
- GET /api/v1/auth/sessions - List user's active sessions
- DELETE /api/v1/auth/sessions/{id} - Revoke specific session
- DELETE /api/v1/auth/sessions - Logout all sessions

Sessions track browser/API logins and can be managed from any device.

Example:
    from litestar import Litestar
    from framework_m.adapters.web.session_routes import session_routes_router

    app = Litestar(route_handlers=[session_routes_router])
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from litestar import Router, delete, get
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass


# =============================================================================
# Response Models
# =============================================================================


class SessionInfo(BaseModel):
    """Session information for API response.

    Attributes:
        id: Session identifier
        ip_address: Client IP address
        user_agent: Client user agent (browser info)
        created_at: When session was created
        expires_at: When session will expire
        is_current: Whether this is the current session
    """

    id: str = Field(description="Session identifier")
    ip_address: str | None = Field(description="Client IP address")
    user_agent: str | None = Field(description="Client user agent")
    created_at: datetime | None = Field(description="Creation time")
    expires_at: datetime = Field(description="Expiration time")
    is_current: bool = Field(default=False, description="Is this the current session")


class SessionListResponse(BaseModel):
    """Response for session list endpoint.

    Attributes:
        sessions: List of active sessions
        count: Total number of sessions
    """

    sessions: list[SessionInfo] = Field(description="Active sessions")
    count: int = Field(description="Total session count")


class SessionRevokeResponse(BaseModel):
    """Response for session revocation.

    Attributes:
        message: Success message
        id: Revoked session ID
    """

    message: str = Field(description="Success message")
    id: str = Field(description="Revoked session ID")


class LogoutAllResponse(BaseModel):
    """Response for logout all endpoint.

    Attributes:
        message: Success message
        count: Number of sessions revoked
    """

    message: str = Field(description="Success message")
    count: int = Field(description="Sessions revoked")


# =============================================================================
# Route Handlers
# =============================================================================


@get("/")
async def list_sessions() -> SessionListResponse:
    """List all active sessions for the authenticated user.

    Returns sessions from all devices/browsers. Each session includes
    IP address and user agent for identification.

    Returns:
        SessionListResponse with list of active sessions
    """
    # In a full implementation:
    # 1. Get user ID from request context (UserContext)
    # 2. Get session store from app state
    # 3. Call session_store.list_for_user(user_id)
    # 4. Mark current session with is_current=True

    # Placeholder - return empty list
    return SessionListResponse(sessions=[], count=0)


@delete("/{session_id:str}")
async def revoke_session(session_id: str) -> SessionRevokeResponse:
    """Revoke (logout) a specific session.

    Use this to logout another device. Users can only revoke
    their own sessions.

    Args:
        session_id: Session ID to revoke

    Returns:
        SessionRevokeResponse confirming revocation

    Raises:
        NotFoundException: If session not found or not owned by user
    """
    # In a full implementation:
    # 1. Get user ID from request context
    # 2. Get session store from app state
    # 3. Verify session belongs to user
    # 4. Call session_store.delete(session_id)

    # Placeholder - pretend success
    return SessionRevokeResponse(
        message="Session revoked",
        id=session_id,
    )


@delete("/")
async def logout_all() -> LogoutAllResponse:
    """Logout all sessions for the authenticated user.

    This will log out all devices including the current one.
    The client should redirect to login after this.

    Returns:
        LogoutAllResponse with count of revoked sessions
    """
    # In a full implementation:
    # 1. Get user ID from request context
    # 2. Get session store from app state
    # 3. Call session_store.delete_all_for_user(user_id)

    # Placeholder - pretend success
    return LogoutAllResponse(
        message="All sessions revoked",
        count=0,
    )


# =============================================================================
# Router
# =============================================================================


session_routes_router = Router(
    path="/api/v1/auth/sessions",
    route_handlers=[list_sessions, revoke_session, logout_all],
    tags=["auth"],
)


__all__ = [
    "LogoutAllResponse",
    "SessionInfo",
    "SessionListResponse",
    "SessionRevokeResponse",
    "list_sessions",
    "logout_all",
    "revoke_session",
    "session_routes_router",
]

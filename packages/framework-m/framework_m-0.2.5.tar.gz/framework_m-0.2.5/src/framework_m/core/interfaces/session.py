"""SessionProtocol - Interface for session storage backends.

This module defines the protocol for session management and supporting
data structures. Sessions can be stored in Redis (default) or database.

Configuration in framework_config.toml:
    [auth.session]
    backend = "database"  # or "redis"
    ttl_seconds = 86400  # 24 hours
    cookie_name = "session_id"
    cookie_secure = true
    cookie_httponly = true
    cookie_samesite = "lax"
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from framework_m.cli.config import load_config

# =============================================================================
# Session Data Model
# =============================================================================


class SessionData(BaseModel):
    """Session data returned from session storage.

    Attributes:
        session_id: Unique session identifier
        user_id: Associated user ID
        expires_at: When the session expires
        ip_address: Client IP address (optional)
        user_agent: Client user agent (optional)
        created_at: When session was created
    """

    session_id: str = Field(description="Unique session identifier")
    user_id: str = Field(description="Associated user ID")
    expires_at: datetime = Field(description="Session expiration time")
    ip_address: str | None = Field(default=None, description="Client IP")
    user_agent: str | None = Field(default=None, description="Client user agent")
    created_at: datetime | None = Field(default=None, description="Creation time")


# =============================================================================
# Session Protocol
# =============================================================================


@runtime_checkable
class SessionProtocol(Protocol):
    """Protocol for session storage backends.

    Implementations can use Redis, database, or other storage.

    Methods:
        create: Create a new session
        get: Retrieve session by ID
        delete: Delete a session
        delete_all_for_user: Delete all sessions for a user
        list_for_user: List all sessions for a user
    """

    async def create(
        self,
        user_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> SessionData:
        """Create a new session.

        Args:
            user_id: User ID to create session for
            ip_address: Optional client IP
            user_agent: Optional client user agent

        Returns:
            Created SessionData with session_id
        """
        ...

    async def get(self, session_id: str) -> SessionData | None:
        """Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionData if found and not expired, None otherwise
        """
        ...

    async def delete(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    async def delete_all_for_user(self, user_id: str) -> int:
        """Delete all sessions for a user.

        Args:
            user_id: User whose sessions to delete

        Returns:
            Number of sessions deleted
        """
        ...

    async def list_for_user(self, user_id: str) -> list[SessionData]:
        """List all active sessions for a user.

        Args:
            user_id: User to list sessions for

        Returns:
            List of active SessionData
        """
        ...


# =============================================================================
# Session Configuration
# =============================================================================

DEFAULT_SESSION_CONFIG = {
    "backend": "database",
    "ttl_seconds": 86400,  # 24 hours
    "cookie_name": "session_id",
    "cookie_secure": True,
    "cookie_httponly": True,
    "cookie_samesite": "lax",
}


def get_session_config() -> dict[str, Any]:
    """Get session configuration from framework_config.toml.

    Returns:
        Session configuration with defaults applied
    """
    config = load_config()
    auth_config = config.get("auth", {})
    session_config = auth_config.get("session", {})

    return {
        **DEFAULT_SESSION_CONFIG,
        **session_config,
    }


__all__ = [
    "DEFAULT_SESSION_CONFIG",
    "SessionData",
    "SessionProtocol",
    "get_session_config",
]

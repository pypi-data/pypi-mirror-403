"""Auth Routes - Authentication API for Indie mode.

This module provides REST endpoints for authentication:
- GET /api/v1/auth/me - Get current user context
- POST /api/v1/auth/login - Authenticate and get token
- POST /api/v1/auth/logout - Logout (clear session)

These endpoints are primarily for Indie mode where authentication
is handled locally. In Federated mode, authentication is handled
by the external gateway.

Example:
    from litestar import Litestar
    from framework_m.adapters.web.auth_routes import auth_routes_router

    app = Litestar(route_handlers=[auth_routes_router])
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar import Router, get, post
from litestar.connection import Request
from litestar.exceptions import NotAuthorizedException
from pydantic import BaseModel, Field

from framework_m.core.exceptions import AuthenticationError
from framework_m.core.interfaces.identity import PasswordCredentials

if TYPE_CHECKING:
    from framework_m.core.services.user_manager import UserManager


# =============================================================================
# DTOs
# =============================================================================


class LoginRequest(BaseModel):
    """Login request body.

    Attributes:
        email: Email address (preferred)
        username: Username (alternative to email)
        password: Plain-text password
    """

    email: str | None = Field(default=None, description="Email address")
    username: str | None = Field(default=None, description="Username (alternative)")
    password: str = Field(description="Password")

    @property
    def login_id(self) -> str:
        """Get the login identifier (email or username)."""
        return self.email or self.username or ""


# =============================================================================
# Module-level UserManager (will be set via DI)
# =============================================================================

_user_manager: UserManager | None = None


def get_user_manager() -> UserManager:
    """Get the UserManager instance.

    In production, this is set via dependency injection.
    For testing, it can be patched.

    Returns:
        UserManager instance

    Raises:
        RuntimeError: If UserManager not configured
    """
    if _user_manager is None:
        raise RuntimeError(
            "UserManager not configured. "
            "Set it via dependency injection or configure_auth_routes()."
        )
    return _user_manager


def configure_auth_routes(user_manager: UserManager) -> None:
    """Configure auth routes with a UserManager instance.

    Call this during app startup to inject the UserManager.

    Args:
        user_manager: The UserManager to use for auth operations
    """
    global _user_manager
    _user_manager = user_manager


# =============================================================================
# Route Handlers
# =============================================================================


@get("/me")
async def get_current_user(request: Request[Any, Any, Any]) -> dict[str, Any]:
    """Get current authenticated user context.

    Returns user information from the authenticated context.
    In dev mode without authentication, returns a guest user.

    Args:
        request: The HTTP request with user context in state

    Returns:
        Dict with user info (id, email, name, roles, tenants, teams)
    """
    user = getattr(request.state, "user", None)

    if user is None:
        # Dev mode: return mock user info
        return {
            "authenticated": False,
            "id": "guest",
            "email": None,
            "name": "Guest User",
            "roles": [],
            "tenants": [],
            "teams": [],
            "is_system_user": False,
        }

    return {
        "authenticated": True,
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "roles": user.roles,
        "tenants": user.tenants,
        "teams": user.teams,
        "is_system_user": user.is_system_user,
    }


@post("/login")
async def login(data: LoginRequest) -> dict[str, Any]:
    """Authenticate user and return access token.

    Accepts username/email and password, validates against LocalUser,
    and returns a JWT token on success.

    In development mode (when UserManager is not configured), accepts
    any credentials and returns a mock token for testing.

    Args:
        data: Login credentials (username, password)

    Returns:
        Dict with access_token, token_type, and expires_in

    Raises:
        NotAuthorizedException: If credentials are invalid
    """
    # Get login identifier (email or username)
    login_id = data.login_id

    # Dev mode: If UserManager not configured, accept any login
    if _user_manager is None:
        # Development mode - return mock token
        import os

        if os.environ.get("FRAMEWORK_M_DEV_MODE", "true").lower() == "true":
            return {
                "access_token": "dev-token-" + login_id.replace("@", "-at-"),
                "token_type": "bearer",
                "expires_in": 86400,
                "refresh_token": None,
                "user": {
                    "id": "dev-user-1",
                    "email": login_id,
                    "name": login_id.split("@")[0].title()
                    if "@" in login_id
                    else login_id.title(),
                    "roles": ["User"],
                },
            }
        raise NotAuthorizedException(
            detail="UserManager not configured. Set FRAMEWORK_M_DEV_MODE=true for testing."
        )

    # Production mode: use configured UserManager
    try:
        credentials = PasswordCredentials(
            username=login_id,
            password=data.password,
        )
        token = await _user_manager.authenticate(credentials)
    except AuthenticationError as e:
        raise NotAuthorizedException(detail=str(e)) from e

    return {
        "access_token": token.access_token,
        "token_type": token.token_type,
        "expires_in": token.expires_in,
        "refresh_token": token.refresh_token,
    }


@post("/logout")
async def logout() -> dict[str, str]:
    """Logout current user.

    For JWT-based auth, this is primarily a client-side operation
    (discard the token). For session-based auth, this would clear
    the session.

    Returns:
        Success message
    """
    # For JWT auth, logout is client-side (discard token)
    # For session auth, we would clear the session here
    return {"message": "Logged out successfully"}


# =============================================================================
# Router
# =============================================================================


auth_routes_router = Router(
    path="/api/v1/auth",
    route_handlers=[get_current_user, login, logout],
    tags=["auth"],
)


def create_auth_router() -> Router:
    """Create the auth router.

    Returns:
        Litestar Router with auth endpoints
    """
    return auth_routes_router


__all__ = [
    "LoginRequest",
    "auth_routes_router",
    "configure_auth_routes",
    "create_auth_router",
    "get_current_user",
    "login",
    "logout",
]

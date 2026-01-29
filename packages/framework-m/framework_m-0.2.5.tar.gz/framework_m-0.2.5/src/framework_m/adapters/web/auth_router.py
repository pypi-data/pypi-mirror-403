"""Authentication API Routes.

This module provides authentication-related endpoints:
- GET /api/v1/auth/me - Get current user info

The framework is stateless - user context comes from headers set by
an upstream authentication gateway. These routes expose that context
to the frontend.

Per ARCHITECTURE.md:
- No server-side sessions
- Header-based auth (x-user-id, x-roles, x-tenants)
- Explicit UserContext parameter (no global state)
"""

from __future__ import annotations

from typing import Any

from litestar import Router, get
from litestar.connection import Request


@get("/auth/me", tags=["Auth"])
async def get_current_user(request: Request[Any, Any, Any]) -> dict[str, Any]:
    """Get current authenticated user.

    Returns the user context extracted from request headers by AuthMiddleware.
    If no user is authenticated, returns a guest user object.

    Returns:
        User info including id, email, roles, tenants
    """
    user = getattr(request.state, "user", None)

    if user is None:
        return {
            "authenticated": False,
            "id": None,
            "email": None,
            "roles": [],
            "tenants": [],
        }

    return {
        "authenticated": True,
        "id": user.id,
        "email": user.email,
        "roles": user.roles,
        "tenants": user.tenants,
    }


# Create router with /api/v1 prefix
auth_router = Router(
    path="/api/v1",
    route_handlers=[get_current_user],
    tags=["Auth"],
)


__all__ = ["auth_router", "get_current_user"]

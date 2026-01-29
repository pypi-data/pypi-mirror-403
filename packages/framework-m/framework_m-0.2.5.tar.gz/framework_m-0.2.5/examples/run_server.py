"""Run the Framework M API server for manual testing.

Usage:
    cd /Users/ansh/Desktop/CastleCraft/m/libs/framework-m
    uv run python scripts/run_server.py

Then test with:
    curl http://localhost:8000/api/v1/Todo
    OR use the test_api.py script
"""

from typing import Any, ClassVar

import uvicorn
from litestar import Litestar, Response
from litestar.status_codes import HTTP_403_FORBIDDEN
from litestar.types import ASGIApp, Receive, Scope, Send

from framework_m.adapters.web.meta_router import create_meta_router
from framework_m.adapters.web.meta_routes import meta_routes_router
from framework_m.adapters.web.rpc_routes import rpc_router
from framework_m.core.domain.base_doctype import BaseDocType, Field
from framework_m.core.exceptions import PermissionDeniedError
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocType for Manual Testing
# =============================================================================


class Todo(BaseDocType):
    """Todo DocType for testing."""

    title: str = Field(title="Title", description="Todo title")
    completed: bool = Field(default=False)

    class Meta:
        api_resource: ClassVar[bool] = True
        requires_auth: ClassVar[bool] = False  # Allow guest for easy testing
        apply_rls: ClassVar[bool] = False
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Guest", "Employee", "Manager", "Admin"],
            "write": ["Employee", "Manager", "Admin"],
            "create": ["Employee", "Manager", "Admin"],
            "delete": ["Admin"],
        }


# =============================================================================
# Auth Middleware
# =============================================================================


def create_auth_middleware(app: ASGIApp) -> ASGIApp:
    """Create middleware that parses x-user-id and x-roles headers."""

    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            user_id = headers.get(b"x-user-id", b"anonymous").decode()
            roles_str = headers.get(b"x-roles", b"Guest").decode()
            roles = [r.strip() for r in roles_str.split(",")]

            # Set both the UserContext AND the individual attributes
            # The meta_router looks for user_id, user_roles, user_teams
            scope["state"]["user"] = UserContext(
                id=user_id,
                email=f"{user_id}@example.com",
                roles=roles,
            )
            scope["state"]["user_id"] = user_id
            scope["state"]["user_roles"] = roles
            scope["state"]["user_teams"] = []
        await app(scope, receive, send)

    return middleware


def permission_denied_handler(
    request: Any, exc: PermissionDeniedError
) -> Response[dict[str, str]]:
    """Handle permission denied errors."""
    return Response(
        content={"error": "PermissionDenied", "message": str(exc)},
        status_code=HTTP_403_FORBIDDEN,
    )


# =============================================================================
# Server Setup
# =============================================================================


def create_test_app() -> Litestar:
    """Create the test application."""
    # Register DocType
    registry = MetaRegistry.get_instance()
    registry.clear()
    registry.register_doctype(Todo)

    # Create routers
    crud_router = create_meta_router()

    # Create app with middleware and exception handlers
    app = Litestar(
        route_handlers=[crud_router, rpc_router, meta_routes_router],
        middleware=[create_auth_middleware],
        exception_handlers={PermissionDeniedError: permission_denied_handler},
        debug=True,
    )

    return app


if __name__ == "__main__":
    print("Starting Framework M API server...")
    print("Server running at: http://localhost:8000")
    print("")
    print("Available endpoints:")
    print("  GET  /api/v1/Todo          - List todos")
    print("  POST /api/v1/Todo          - Create todo")
    print("  GET  /api/v1/Todo/{id}     - Get todo")
    print("  PUT  /api/v1/Todo/{id}     - Update todo")
    print("  DELETE /api/v1/Todo/{id}   - Delete todo")
    print("  GET  /api/meta/Todo        - Get Todo metadata")
    print("")
    print("Authentication headers:")
    print("  x-user-id: user123")
    print("  x-roles: Employee,Manager")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")

    app = create_test_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)

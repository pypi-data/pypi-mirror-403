"""Authentication Middleware for Framework M.

This module provides middleware that extracts user identity from request headers
and creates a UserContext object for use throughout the request lifecycle.

The framework is stateless - user context comes from headers set by an upstream
authentication gateway or proxy, not from server-side sessions.

Headers:
    x-user-id: Required user identifier
    x-user-email: User's email address
    x-roles: Comma-separated list of roles
    x-tenants: Optional comma-separated list of tenant IDs

Example:
    # Upstream gateway sets headers after authentication
    x-user-id: user-123
    x-user-email: john@example.com
    x-roles: Employee,Manager
    x-tenants: tenant-001
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.middleware.base import DefineMiddleware

from framework_m.core.interfaces.auth_context import UserContext

if TYPE_CHECKING:
    from litestar.types import ASGIApp, Receive, Scope, Send


# Default paths that bypass authentication
DEFAULT_EXCLUDED_PATHS: list[str] = [
    "/health",
    "/schema",
]


class AuthMiddleware:
    """Middleware that extracts user context from request headers.

    Reads authentication headers set by an upstream gateway and creates
    a UserContext object stored in request.state.user.

    Attributes:
        app: The wrapped ASGI application
        require_auth: If True, returns 401 when required headers are missing
        excluded_paths: List of path prefixes that bypass auth check

    Example:
        app = Litestar(
            middleware=[
                create_auth_middleware(require_auth=True)
            ]
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        require_auth: bool = True,
        excluded_paths: list[str] | None = None,
    ) -> None:
        """Initialize the authentication middleware.

        Args:
            app: The ASGI application
            require_auth: Whether to require authentication (return 401 if missing)
            excluded_paths: List of path prefixes that bypass auth check
        """
        self.app = app
        self.require_auth = require_auth
        self.excluded_paths = excluded_paths or DEFAULT_EXCLUDED_PATHS

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the request and extract user context.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Only process HTTP requests
        scope_type = scope["type"]
        if scope_type != "http":  # type: ignore[comparison-overlap]
            await self.app(scope, receive, send)
            return

        # Check if path is excluded
        path: str = scope.get("path", "")
        if self._is_excluded_path(path):
            await self.app(scope, receive, send)
            return

        # Extract headers
        headers = dict(scope.get("headers", []))
        user_id = self._get_header(headers, b"x-user-id")
        user_email = self._get_header(headers, b"x-user-email")
        roles_str = self._get_header(headers, b"x-roles")
        tenants_str = self._get_header(headers, b"x-tenants")

        # Check if authentication is required
        if self.require_auth and not user_id:
            await self._send_401_response(send)
            return

        # Create UserContext if user is authenticated
        user: UserContext | None = None
        if user_id:
            roles = self._parse_comma_separated(roles_str)
            tenants = self._parse_comma_separated(tenants_str)

            user = UserContext(
                id=user_id,
                email=user_email or "",
                roles=roles,
                tenants=tenants,
            )

        # Store user in scope state for access in request handlers
        # Litestar uses scope["state"] for request.state
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["user"] = user

        await self.app(scope, receive, send)

    async def _send_401_response(self, send: Send) -> None:
        """Send a 401 Unauthorized ASGI response.

        Args:
            send: ASGI send callable
        """
        import json

        body = json.dumps(
            {
                "error": "Unauthorized",
                "message": "Authentication required. Missing x-user-id header.",
            }
        ).encode("utf-8")

        from litestar.types import HTTPResponseBodyEvent, HTTPResponseStartEvent

        start_event: HTTPResponseStartEvent = {
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("utf-8")),
            ],
        }
        await send(start_event)

        body_event: HTTPResponseBodyEvent = {
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        }
        await send(body_event)

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path should bypass authentication.

        Args:
            path: Request path

        Returns:
            True if path starts with any excluded prefix
        """
        return any(path.startswith(excluded) for excluded in self.excluded_paths)

    def _get_header(self, headers: dict[bytes, bytes], name: bytes) -> str | None:
        """Get a header value as string.

        Args:
            headers: Dict of header name -> value (both bytes)
            name: Header name to look up

        Returns:
            Header value as string, or None if not found
        """
        value = headers.get(name)
        if value is None:
            return None
        return value.decode("utf-8")

    def _parse_comma_separated(self, value: str | None) -> list[str]:
        """Parse a comma-separated string into a list.

        Args:
            value: Comma-separated string or None

        Returns:
            List of trimmed values, empty list if input is None or empty
        """
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]


def create_auth_middleware(
    require_auth: bool = True,
    excluded_paths: list[str] | None = None,
) -> DefineMiddleware:
    """Create an authentication middleware configuration.

    This factory function creates a middleware definition that can be
    passed to Litestar's middleware list.

    Args:
        require_auth: If True, returns 401 when x-user-id header is missing
        excluded_paths: List of path prefixes to exclude from auth check.
                       Defaults to ["/health", "/schema"]

    Returns:
        DefineMiddleware instance for use in Litestar

    Example:
        app = Litestar(
            route_handlers=[...],
            middleware=[
                create_auth_middleware(require_auth=True),
            ],
        )
    """
    return DefineMiddleware(
        AuthMiddleware,
        require_auth=require_auth,
        excluded_paths=excluded_paths,
    )


__all__ = ["AuthMiddleware", "create_auth_middleware"]

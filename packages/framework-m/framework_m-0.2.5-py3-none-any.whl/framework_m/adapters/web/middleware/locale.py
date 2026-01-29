"""Locale resolution middleware for i18n support.

This module provides middleware to resolve the user's locale based on:
1. Accept-Language header
2. User preference (user.locale)
3. Tenant default (tenant.attributes.default_locale)
4. System default (DEFAULT_LOCALE setting)

The resolved locale is stored in request state and made available
via dependency injection for translating content.
"""

# mypy: disable-error-code="import-untyped"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar import Request
from litestar.middleware import DefineMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send

if TYPE_CHECKING:
    from framework_m.core.interfaces.auth_context import (
        AuthContextProtocol as AuthContext,
    )
    from framework_m.core.interfaces.tenant import TenantContext


# Default locale if no other preference found
DEFAULT_LOCALE = "en"


def parse_accept_language(header: str | None) -> str | None:
    """Parse Accept-Language header and return best match.

    Args:
        header: Accept-Language header value (e.g., "en-US,en;q=0.9,hi;q=0.8")

    Returns:
        Best matching locale code (e.g., "en", "hi") or None

    Example:
        >>> parse_accept_language("en-US,en;q=0.9,hi;q=0.8")
        'en'
        >>> parse_accept_language("hi-IN,hi;q=0.9")
        'hi'
    """
    if not header:
        return None

    # Parse header: "en-US,en;q=0.9,hi;q=0.8"
    locales = []
    for part in header.split(","):
        part = part.strip()
        if ";q=" in part:
            locale, quality = part.split(";q=")
            quality_value = float(quality)
        else:
            locale = part
            quality_value = 1.0

        # Extract base locale (en from en-US)
        base_locale = locale.split("-")[0].lower()
        locales.append((base_locale, quality_value))

    # Sort by quality value (highest first)
    locales.sort(key=lambda x: x[1], reverse=True)

    return locales[0][0] if locales else None


class LocaleResolutionMiddleware:
    """Middleware to resolve user's locale and store in request state.

    Resolution order:
    1. Accept-Language header (browser preference)
    2. User preference (user.locale from auth context)
    3. Tenant default (tenant.attributes.default_locale)
    4. System default (DEFAULT_LOCALE)

    The resolved locale is stored in request.state.locale
    and can be injected via provide_locale() dependency.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize middleware.

        Args:
            app: ASGI application to wrap
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process request and resolve locale.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Create request object to access headers and state
        request: Request[Any, Any, Any] = Request(scope)

        # Initialize locale as None
        locale: str | None = None

        # 1. Try Accept-Language header
        accept_language = request.headers.get("Accept-Language")
        if accept_language:
            locale = parse_accept_language(accept_language)

        # 2. Try user preference (if user is authenticated)
        if not locale:
            auth_ctx: AuthContext | None = getattr(request.state, "auth", None)
            if auth_ctx and hasattr(auth_ctx, "user") and auth_ctx.user:
                user_locale = getattr(auth_ctx.user, "locale", None)
                if user_locale:
                    locale = user_locale

        # 3. Try tenant default
        if not locale:
            tenant_ctx: TenantContext | None = getattr(request.state, "tenant", None)
            if tenant_ctx and tenant_ctx.attributes:
                tenant_locale = tenant_ctx.attributes.get("default_locale")
                if tenant_locale:
                    locale = tenant_locale

        # 4. Fallback to system default
        if not locale:
            locale = DEFAULT_LOCALE

        # Store resolved locale in request state
        request.state.locale = locale

        # Continue processing
        await self.app(scope, receive, send)


# Middleware factory for Litestar
def create_locale_middleware() -> DefineMiddleware:
    """Create locale resolution middleware for Litestar app.

    Returns:
        DefineMiddleware instance

    Example:
        from litestar import Litestar
        from framework_m.adapters.web.middleware.locale import create_locale_middleware

        app = Litestar(
            route_handlers=[...],
            middleware=[create_locale_middleware()],
        )
    """
    return DefineMiddleware(LocaleResolutionMiddleware)


# Dependency injection provider
def provide_locale(request: Request[Any, Any, Any]) -> str:
    """Provide resolved locale from request state.

    Args:
        request: Litestar request object

    Returns:
        Resolved locale code (e.g., "en", "hi", "ta")

    Example:
        @get("/api/greeting")
        async def get_greeting(locale: str = Dependency(provide_locale)) -> str:
            if locale == "hi":
                return "नमस्ते"
            return "Hello"
    """
    return getattr(request.state, "locale", DEFAULT_LOCALE)

"""Web Adapters - HTTP/API layer for Framework M.

This package provides the Litestar-based web application with:
- Application factory
- Authentication middleware
- Middleware discovery and registration
- Auto-CRUD router generation
- RPC routes for controller methods
- Share management routes
- Exception handlers
- OpenAPI documentation
"""

from framework_m.adapters.web.app import create_app
from framework_m.adapters.web.dtos import (
    ErrorResponse,
    PaginatedResponse,
    SuccessResponse,
)
from framework_m.adapters.web.meta_router import create_crud_routes, create_meta_router
from framework_m.adapters.web.meta_routes import meta_routes_router
from framework_m.adapters.web.middleware import (
    AuthMiddleware,
    LocaleResolutionMiddleware,
    create_auth_middleware,
    create_locale_middleware,
)
from framework_m.adapters.web.middleware_registry import (
    MiddlewareConfig,
    MiddlewareRegistry,
    create_middleware_stack,
)
from framework_m.adapters.web.rpc_routes import rpc_router
from framework_m.adapters.web.share_routes import (
    CreateShareRequest,
    ShareController,
    ShareListResponse,
    ShareResponse,
    share_router,
)

__all__ = [
    "AuthMiddleware",
    "CreateShareRequest",
    "ErrorResponse",
    "LocaleResolutionMiddleware",
    "MiddlewareConfig",
    "MiddlewareRegistry",
    "PaginatedResponse",
    "ShareController",
    "ShareListResponse",
    "ShareResponse",
    "SuccessResponse",
    "create_app",
    "create_auth_middleware",
    "create_crud_routes",
    "create_locale_middleware",
    "create_meta_router",
    "create_middleware_stack",
    "meta_routes_router",
    "rpc_router",
    "share_router",
]

"""Litestar Application Factory.

This module provides the application factory for creating the Litestar
web application with all required configuration.

Features:
- CORS configuration for development
- Exception handlers for domain exceptions
- OpenAPI documentation (Swagger/ReDoc)
- Application lifecycle management
- Dependency injection container integration

Example:
    from framework_m.adapters.web.app import create_app

    app = create_app()

    # Run with uvicorn
    # uvicorn framework_m.adapters.web.app:create_app --factory
"""

# ruff: noqa: E402 - Module imports must come after dotenv loading

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# Load environment variables from .env files (searches up the directory tree)
from dotenv import load_dotenv

# Search for .env file from current directory up to root
_cwd = Path.cwd()
for _parent in [_cwd, *_cwd.parents]:
    _env_file = _parent / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
        break

from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import RedocRenderPlugin, SwaggerRenderPlugin
from litestar.openapi.spec import Components, SecurityScheme
from litestar.response import Response
from litestar.static_files import StaticFilesConfig

from framework_m.adapters.db.connection import ConnectionFactory
from framework_m.adapters.db.session import SessionFactory
from framework_m.adapters.web.auth_routes import auth_routes_router
from framework_m.adapters.web.meta_router import create_meta_router
from framework_m.adapters.web.metadata_router import metadata_router
from framework_m.adapters.web.middleware import create_auth_middleware
from framework_m.adapters.web.socket import create_websocket_router
from framework_m.adapters.web.workflow_router import workflow_router
from framework_m.cli.config import load_config
from framework_m.core.container import Container
from framework_m.core.exceptions import (
    DocTypeNotFoundError,
    DuplicateNameError,
    EntityNotFoundError,
    FrameworkError,
    PermissionDeniedError,
    ValidationError,
)

# =============================================================================
# Exception Handlers
# =============================================================================


def validation_error_handler(
    request: Any, exc: ValidationError
) -> Response[dict[str, Any]]:
    """Handle validation errors with 400 Bad Request.

    Args:
        request: The incoming request
        exc: The validation exception

    Returns:
        JSON response with error details
    """
    return Response(
        content={
            "error": "ValidationError",
            "message": str(exc),
            "details": getattr(exc, "details", None),
        },
        status_code=400,
    )


def permission_denied_handler(
    request: Any, exc: PermissionDeniedError
) -> Response[dict[str, str]]:
    """Handle permission denied errors with 403 Forbidden.

    Args:
        request: The incoming request
        exc: The permission exception

    Returns:
        JSON response with error details
    """
    return Response(
        content={
            "error": "PermissionDenied",
            "message": str(exc),
        },
        status_code=403,
    )


def not_found_handler(
    request: Any, exc: DocTypeNotFoundError | EntityNotFoundError
) -> Response[dict[str, str]]:
    """Handle not found errors with 404 Not Found.

    Args:
        request: The incoming request
        exc: The not found exception

    Returns:
        JSON response with error details
    """
    return Response(
        content={
            "error": "NotFound",
            "message": str(exc),
        },
        status_code=404,
    )


def duplicate_name_handler(
    request: Any, exc: DuplicateNameError
) -> Response[dict[str, str]]:
    """Handle duplicate name errors with 409 Conflict.

    Args:
        request: The incoming request
        exc: The duplicate name exception

    Returns:
        JSON response with error details
    """
    return Response(
        content={
            "error": "Conflict",
            "message": str(exc),
            "doctype": exc.doctype_name,
            "name": exc.name,
        },
        status_code=409,
    )


def framework_error_handler(
    request: Any, exc: FrameworkError
) -> Response[dict[str, str]]:
    """Handle generic framework errors with 500 Internal Server Error.

    Args:
        request: The incoming request
        exc: The framework exception

    Returns:
        JSON response with error details
    """
    return Response(
        content={
            "error": "InternalError",
            "message": str(exc),
        },
        status_code=500,
    )


# =============================================================================
# Route Handlers
# =============================================================================


@get("/health", sync_to_thread=False)
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns basic health status for load balancers and monitoring.

    Returns:
        Dict with status information
    """
    return {"status": "healthy"}


# =============================================================================
# Application Lifecycle
# =============================================================================


@asynccontextmanager
async def app_lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Handles startup and shutdown tasks:
    - Startup: Initialize container, database connections, discover DocTypes
    - Shutdown: Close database connections, cleanup resources

    Args:
        app: The Litestar application instance

    Yields:
        None during the application's running state
    """
    # ==========================================================================
    # Startup
    # ==========================================================================
    container = Container()
    connection_factory = ConnectionFactory()
    session_factory = SessionFactory()

    # Configure database if DATABASE_URL is set
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        connection_factory.configure({"default": database_url})
        session_factory.configure(connection_factory)

        # Create tables for all registered DocTypes
        from sqlalchemy import MetaData

        from framework_m.adapters.db.repository_factory import RepositoryFactory
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.core.registry import MetaRegistry

        registry = MetaRegistry.get_instance()
        metadata = MetaData()
        schema_mapper = SchemaMapper()

        # Create table definitions for each registered DocType
        for doctype_name in registry.list_doctypes():
            try:
                doctype_class = registry.get_doctype(doctype_name)
                if doctype_class is not None and doctype_class.get_api_resource():
                    schema_mapper.create_tables(doctype_class, metadata)
            except Exception:
                pass  # Skip doctype if it fails

        # Create all tables in the database
        engine = connection_factory.get_engine("default")
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create RepositoryFactory with metadata and session_factory
        repo_factory = RepositoryFactory(metadata, session_factory)
        app.state.repository_factory = repo_factory
    else:
        app.state.repository_factory = None

    # Store container in app state for access in routes
    app.state.container = container

    # Note: DocTypes are registered in create_app() before route creation

    yield

    # ==========================================================================
    # Shutdown
    # ==========================================================================
    # Close database connections
    if database_url:
        await connection_factory.dispose_all()


# =============================================================================
# Application Factory
# =============================================================================


def create_app() -> Litestar:
    """Create and configure the Litestar application.

    This factory function creates a fully configured Litestar app with:
    - CORS configured for development (allows all origins)
    - Exception handlers for domain exceptions
    - OpenAPI documentation with Swagger UI
    - Health check endpoint
    - Application lifecycle management

    Returns:
        Configured Litestar application instance

    Example:
        app = create_app()

        # For production, configure via environment:
        # CORS_ORIGINS=https://example.com
    """
    # CORS Configuration (development defaults)
    cors_config = CORSConfig(
        allow_origins=["*"],  # TODO: Configure from environment for production
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    # OpenAPI Configuration
    openapi_config = OpenAPIConfig(
        title="Framework M API",
        version="0.2.0",
        description="A modern, metadata-driven business application framework",
        path="/schema",
        render_plugins=[
            SwaggerRenderPlugin(),
            RedocRenderPlugin(),
        ],
        # Security scheme for header-based authentication
        components=Components(
            security_schemes={
                "HeaderAuth": SecurityScheme(
                    type="apiKey",
                    name="x-user-id",
                    security_scheme_in="header",
                    description="User ID for authentication. Required for protected endpoints.",
                ),
                "RolesHeader": SecurityScheme(
                    type="apiKey",
                    name="x-roles",
                    security_scheme_in="header",
                    description="Comma-separated list of roles (e.g., 'Manager,Employee').",
                ),
            },
        ),
    )

    # Exception Handlers - type: ignore needed for union return types
    exception_handlers = {
        ValidationError: validation_error_handler,
        PermissionDeniedError: permission_denied_handler,
        DocTypeNotFoundError: not_found_handler,
        EntityNotFoundError: not_found_handler,
        DuplicateNameError: duplicate_name_handler,
        FrameworkError: framework_error_handler,
    }

    # Static Files Configuration
    static_files_config = _create_static_files_config()

    # Auto-discover DocTypes from installed apps via entry points
    from importlib.metadata import entry_points

    from framework_m.core.registry import MetaRegistry

    registry = MetaRegistry.get_instance()

    # First, discover framework's core DocTypes
    core_count = registry.discover_doctypes("framework_m.core.doctypes")
    if core_count > 0:
        print(f"Discovered {core_count} core DocType(s) from framework")

    # Then discover DocTypes from all installed apps registered via entry points
    eps = entry_points(group="framework_m.apps")
    for ep in eps:
        try:
            # Load the app module (returns the app dict with metadata)
            ep.load()
            # Discover DocTypes in the package that contains the app
            package_name = ep.module.rsplit(".", 1)[
                0
            ]  # Get package name without ":app"
            count = registry.discover_doctypes(package_name)
            if count > 0:
                print(f"Discovered {count} DocType(s) from app '{ep.name}'")
        except Exception as e:
            # Log but don't fail startup if an app fails to load
            print(f"Warning: Failed to load app '{ep.name}': {e}")

    # Build route handlers list
    route_handlers: list[Any] = [
        health_check,
        auth_routes_router,
        metadata_router,
        workflow_router,
    ]

    # Add auto-CRUD routes for DocTypes with api_resource=True
    try:
        crud_router = create_meta_router()
        route_handlers.append(crud_router)
    except Exception:
        # No DocTypes registered yet, skip CRUD routes
        pass

    # Add WebSocket router for real-time streaming
    websocket_router = create_websocket_router()
    route_handlers.append(websocket_router)

    # Create and return app
    app = Litestar(
        route_handlers=route_handlers,
        middleware=[
            create_auth_middleware(
                require_auth=False,  # Don't require auth by default (for development)
                excluded_paths=["/health", "/schema", "/api/meta"],
            ),
        ],
        cors_config=cors_config,
        openapi_config=openapi_config,
        exception_handlers=exception_handlers,  # type: ignore[arg-type]
        lifespan=[app_lifespan],
        static_files_config=static_files_config,
        debug=True,  # TODO: Configure from environment
    )

    return app


def _create_static_files_config() -> list[StaticFilesConfig]:
    """Create static files configuration.

    Reads from framework_config.toml to determine:
    - Static file directories
    - CDN URL prefix (optional)

    Returns:
        List of StaticFilesConfig instances
    """
    from pathlib import Path

    # Default static directories to check
    static_dirs = [
        Path.cwd() / "dist",
        Path.cwd() / "static" / "dist",
        Path.cwd() / "frontend" / "dist",
    ]

    # Find first existing directory
    static_path: Path | None = None
    for d in static_dirs:
        if d.exists() and d.is_dir():
            static_path = d
            break

    if static_path is None:
        # No static files found, return empty config
        return []

    # Determine URL path
    # CDN is handled by get_asset_url(), not here
    url_path = "/assets"

    return [
        StaticFilesConfig(
            path=url_path,
            directories=[static_path],
            html_mode=False,  # Don't serve index.html for directories
        ),
        # Also serve at /static for compatibility
        StaticFilesConfig(
            path="/static",
            directories=[static_path],
            html_mode=False,
        ),
    ]


def get_asset_url(asset_path: str) -> str:
    """Get the URL for a static asset.

    If CDN is configured, returns CDN URL. Otherwise returns local URL.
    This function can be used in templates to generate asset URLs.

    Args:
        asset_path: Path to the asset (e.g., 'js/main.js')

    Returns:
        Full URL to the asset

    Example:
        >>> get_asset_url('js/main.js')
        'https://cdn.example.com/assets/js/main.js'  # if CDN configured
        '/assets/js/main.js'  # if no CDN
    """
    config = load_config()
    frontend_config = config.get("frontend", {})
    cdn_url = frontend_config.get("cdn_url")

    if cdn_url:
        # Ensure trailing slash
        if not cdn_url.endswith("/"):
            cdn_url += "/"
        return f"{cdn_url}{asset_path.lstrip('/')}"

    return f"/assets/{asset_path.lstrip('/')}"


__all__ = ["create_app"]

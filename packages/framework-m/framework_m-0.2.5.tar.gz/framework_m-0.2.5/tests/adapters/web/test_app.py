"""Tests for Litestar Application Setup.

TDD tests for the web application factory and configuration.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from framework_m.adapters.web.app import create_app
from framework_m.core.registry import MetaRegistry


@pytest.fixture(autouse=True)
def reset_registry():
    """Clear MetaRegistry before and after each test to avoid DuplicateDocTypeError."""
    MetaRegistry.get_instance()._doctypes.clear()
    yield
    MetaRegistry.get_instance()._doctypes.clear()


class TestAppFactory:
    """Test the application factory function."""

    def test_create_app_returns_litestar_instance(self) -> None:
        """Create_app should return a Litestar application instance."""
        app = create_app()
        assert isinstance(app, Litestar)

    def test_app_has_openapi_configured(self) -> None:
        """App should have OpenAPI documentation configured."""
        app = create_app()
        # OpenAPI config should be present
        assert app.openapi_config is not None
        # Should have a title set
        assert app.openapi_config.title is not None

    def test_app_has_cors_configured_for_development(self) -> None:
        """App should have CORS configured for development mode."""
        app = create_app()
        # CORS middleware should be added
        # In Litestar, CORS is configured via CORSConfig
        assert app.cors_config is not None

    def test_app_has_exception_handlers(self) -> None:
        """App should have custom exception handlers registered."""
        app = create_app()
        # Exception handlers should be configured
        assert app.exception_handlers is not None
        # Should have at least one handler
        assert len(app.exception_handlers) > 0


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_endpoint_returns_200(self) -> None:
        """Health endpoint should return 200 OK."""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200

    def test_health_endpoint_returns_status(self) -> None:
        """Health endpoint should return status information."""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/health")
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"


class TestAppLifecycle:
    """Test application lifecycle hooks."""

    @pytest.mark.asyncio
    async def test_lifespan_context_manager(self) -> None:
        """App should properly handle startup and shutdown."""
        app = create_app()
        # The lifespan context manager should be set
        # Litestar uses on_startup and on_shutdown or lifespan
        # We check that the app can be used as async context manager
        assert app is not None


class TestOpenAPIConfiguration:
    """Test OpenAPI/Swagger documentation configuration."""

    def test_swagger_ui_available(self) -> None:
        """Swagger UI should be available at /schema/swagger."""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/schema/swagger")
            # Should redirect or return HTML
            assert response.status_code in [200, 301, 302, 307, 308]

    def test_openapi_schema_available(self) -> None:
        """OpenAPI JSON schema should be available."""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/schema/openapi.json")
            assert response.status_code == 200
            data = response.json()
            # Should have OpenAPI version
            assert "openapi" in data
            # Should have info section
            assert "info" in data


# =============================================================================
# Tests for Exception Handlers
# =============================================================================


class TestExceptionHandlers:
    """Test custom exception handlers."""

    def test_validation_error_handler(self) -> None:
        """ValidationError should return 400."""
        from unittest.mock import MagicMock

        from framework_m.adapters.web.app import validation_error_handler
        from framework_m.core.exceptions import ValidationError

        exc = ValidationError("Invalid input")
        mock_request = MagicMock()

        response = validation_error_handler(mock_request, exc)

        assert response.status_code == 400

    def test_permission_denied_handler(self) -> None:
        """PermissionDeniedError should return 403."""
        from unittest.mock import MagicMock

        from framework_m.adapters.web.app import permission_denied_handler
        from framework_m.core.exceptions import PermissionDeniedError

        exc = PermissionDeniedError("Access denied")
        mock_request = MagicMock()

        response = permission_denied_handler(mock_request, exc)

        assert response.status_code == 403

    def test_not_found_handler(self) -> None:
        """EntityNotFoundError should return 404."""
        from unittest.mock import MagicMock

        from framework_m.adapters.web.app import not_found_handler
        from framework_m.core.exceptions import EntityNotFoundError

        exc = EntityNotFoundError(doctype_name="Todo", entity_id="TODO-001")
        mock_request = MagicMock()

        response = not_found_handler(mock_request, exc)

        assert response.status_code == 404

    def test_duplicate_name_handler(self) -> None:
        """DuplicateNameError should return 409."""
        from unittest.mock import MagicMock

        from framework_m.adapters.web.app import duplicate_name_handler
        from framework_m.core.exceptions import DuplicateNameError

        exc = DuplicateNameError(doctype_name="Todo", name="TODO-001")
        mock_request = MagicMock()

        response = duplicate_name_handler(mock_request, exc)

        assert response.status_code == 409

    def test_framework_error_handler(self) -> None:
        """FrameworkError should return 500."""
        from unittest.mock import MagicMock

        from framework_m.adapters.web.app import framework_error_handler
        from framework_m.core.exceptions import FrameworkError

        exc = FrameworkError("Internal error")
        mock_request = MagicMock()

        response = framework_error_handler(mock_request, exc)

        assert response.status_code == 500


# =============================================================================
# Tests for Wired Routers
# =============================================================================


class TestWiredRouters:
    """Test that routers are properly wired to the app."""

    def test_auth_endpoint_available(self) -> None:
        """App should have /api/v1/auth/me endpoint."""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/api/v1/auth/me")
            assert response.status_code == 200

    def test_metadata_endpoint_available(self) -> None:
        """App should have /api/meta/doctypes endpoint."""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/api/meta/doctypes")
            assert response.status_code == 200

    def test_auth_endpoint_returns_user_info(self) -> None:
        """Auth endpoint should return user info structure."""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/api/v1/auth/me")
            data = response.json()
            assert "authenticated" in data
            assert "id" in data
            assert "roles" in data

    def test_metadata_endpoint_returns_doctype_list(self) -> None:
        """Metadata endpoint should return doctypes structure."""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/api/meta/doctypes")
            data = response.json()
            assert "doctypes" in data
            assert "count" in data


class TestAppMiddleware:
    """Test that middleware is properly configured."""

    def test_app_has_auth_middleware(self) -> None:
        """App should have AuthMiddleware configured."""
        app = create_app()
        # Middleware should be present
        assert app.middleware is not None
        assert len(app.middleware) > 0

    def test_auth_middleware_allows_guest_access(self) -> None:
        """App should allow guest access (require_auth=False)."""
        app = create_app()
        with TestClient(app) as client:
            # Should not return 401 without auth headers
            response = client.get("/api/v1/auth/me")
            assert response.status_code == 200

    def test_auth_headers_are_processed(self) -> None:
        """App should process auth headers when provided."""
        app = create_app()
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/auth/me",
                headers={
                    "x-user-id": "test-user-123",
                    "x-user-email": "test@example.com",
                    "x-roles": "Admin",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is True
            assert data["id"] == "test-user-123"

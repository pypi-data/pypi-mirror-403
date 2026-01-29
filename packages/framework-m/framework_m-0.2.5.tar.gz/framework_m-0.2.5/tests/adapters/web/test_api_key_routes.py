"""Tests for API Key Management Routes.

TDD: This test file is created BEFORE the implementation.

Tests cover:
- POST /api/v1/auth/api-keys - Create new API key
- DELETE /api/v1/auth/api-keys/{id} - Revoke API key
- GET /api/v1/auth/api-keys - List user's API keys
"""


# =============================================================================
# Test: API Key Routes Import
# =============================================================================


class TestApiKeyRoutesImport:
    """Tests for API Key routes import."""

    def test_import_api_key_routes_router(self) -> None:
        """api_key_routes_router should be importable."""
        from framework_m.adapters.web.api_key_routes import api_key_routes_router

        assert api_key_routes_router is not None


class TestApiKeyRoutesConfig:
    """Tests for API Key routes configuration."""

    def test_router_has_correct_path(self) -> None:
        """API Key router should be mounted at /api/v1/auth/api-keys."""
        from framework_m.adapters.web.api_key_routes import api_key_routes_router

        assert api_key_routes_router.path == "/api/v1/auth/api-keys"

    def test_router_has_auth_tag(self) -> None:
        """API Key router should have 'auth' tag."""
        from framework_m.adapters.web.api_key_routes import api_key_routes_router

        assert "auth" in api_key_routes_router.tags


# =============================================================================
# Test: Create API Key
# =============================================================================


class TestCreateApiKeyImport:
    """Tests for create_api_key handler import."""

    def test_import_create_api_key(self) -> None:
        """create_api_key handler should be importable."""
        from framework_m.adapters.web.api_key_routes import create_api_key

        assert create_api_key is not None


class TestCreateApiKeyRequest:
    """Tests for CreateApiKeyRequest model."""

    def test_import_create_api_key_request(self) -> None:
        """CreateApiKeyRequest should be importable."""
        from framework_m.adapters.web.api_key_routes import CreateApiKeyRequest

        assert CreateApiKeyRequest is not None

    def test_create_request_with_name(self) -> None:
        """CreateApiKeyRequest should accept name."""
        from framework_m.adapters.web.api_key_routes import CreateApiKeyRequest

        request = CreateApiKeyRequest(name="My API Key")
        assert request.name == "My API Key"

    def test_create_request_with_scopes(self) -> None:
        """CreateApiKeyRequest should accept optional scopes."""
        from framework_m.adapters.web.api_key_routes import CreateApiKeyRequest

        request = CreateApiKeyRequest(name="Key", scopes=["read", "write"])
        assert request.scopes == ["read", "write"]

    def test_create_request_with_expires_in_days(self) -> None:
        """CreateApiKeyRequest should accept optional expires_in_days."""
        from framework_m.adapters.web.api_key_routes import CreateApiKeyRequest

        request = CreateApiKeyRequest(name="Key", expires_in_days=30)
        assert request.expires_in_days == 30


# =============================================================================
# Test: Revoke API Key
# =============================================================================


class TestRevokeApiKeyImport:
    """Tests for revoke_api_key handler import."""

    def test_import_revoke_api_key(self) -> None:
        """revoke_api_key handler should be importable."""
        from framework_m.adapters.web.api_key_routes import revoke_api_key

        assert revoke_api_key is not None

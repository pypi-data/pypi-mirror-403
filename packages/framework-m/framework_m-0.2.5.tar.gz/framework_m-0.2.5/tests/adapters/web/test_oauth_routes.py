"""Tests for OAuth2 Routes.

TDD: This test file is created BEFORE the implementation.

Tests cover:
- GET /api/v1/auth/oauth/{provider}/start - Redirect to provider
- GET /api/v1/auth/oauth/{provider}/callback - Handle OAuth callback
- OAuth2Protocol interface
- Configuration helpers
- Route handlers
"""

from unittest.mock import patch

import pytest
from litestar import Litestar
from litestar.testing import TestClient

# =============================================================================
# Test: OAuth2Protocol Import
# =============================================================================


class TestOAuth2ProtocolImport:
    """Tests for OAuth2Protocol interface import."""

    def test_import_oauth2_protocol(self) -> None:
        """OAuth2Protocol should be importable."""
        from framework_m.core.interfaces.oauth import OAuth2Protocol

        assert OAuth2Protocol is not None


# =============================================================================
# Test: OAuth Routes Import
# =============================================================================


class TestOAuthRoutesImport:
    """Tests for OAuth routes import."""

    def test_import_oauth_routes_router(self) -> None:
        """oauth_routes_router should be importable."""
        from framework_m.adapters.web.oauth_routes import oauth_routes_router

        assert oauth_routes_router is not None

    def test_import_oauth_start(self) -> None:
        """oauth_start handler should be importable."""
        from framework_m.adapters.web.oauth_routes import oauth_start

        assert oauth_start is not None

    def test_import_oauth_callback(self) -> None:
        """oauth_callback handler should be importable."""
        from framework_m.adapters.web.oauth_routes import oauth_callback

        assert oauth_callback is not None


# =============================================================================
# Test: OAuth Provider Config
# =============================================================================


class TestOAuthProviderConfig:
    """Tests for OAuth provider configuration."""

    def test_import_get_oauth_config(self) -> None:
        """get_oauth_config should be importable."""
        from framework_m.adapters.web.oauth_routes import get_oauth_config

        assert get_oauth_config is not None

    def test_get_oauth_config_from_toml(self) -> None:
        """get_oauth_config should read from framework_config.toml."""
        from framework_m.adapters.web.oauth_routes import get_oauth_config

        config = {
            "auth": {
                "oauth": {
                    "enabled": True,
                    "providers": ["google", "github"],
                    "google": {
                        "client_id": "google-client-id",
                        "client_secret": "google-secret",
                    },
                }
            }
        }

        with patch(
            "framework_m.adapters.web.oauth_routes.load_config",
            return_value=config,
        ):
            oauth_config = get_oauth_config()

        assert oauth_config["enabled"] is True
        assert "google" in oauth_config["providers"]

    def test_get_oauth_config_disabled(self) -> None:
        """get_oauth_config should return disabled when not configured."""
        from framework_m.adapters.web.oauth_routes import get_oauth_config

        config = {"auth": {}}

        with patch(
            "framework_m.adapters.web.oauth_routes.load_config",
            return_value=config,
        ):
            oauth_config = get_oauth_config()

        assert oauth_config["enabled"] is False

    def test_get_provider_config(self) -> None:
        """get_provider_config should return provider settings."""
        from framework_m.adapters.web.oauth_routes import get_provider_config

        config = {
            "auth": {
                "oauth": {
                    "enabled": True,
                    "providers": ["google"],
                    "google": {
                        "client_id": "test-id",
                        "client_secret": "test-secret",
                    },
                }
            }
        }

        with patch(
            "framework_m.adapters.web.oauth_routes.load_config",
            return_value=config,
        ):
            provider = get_provider_config("google")

        assert provider is not None
        assert provider["client_id"] == "test-id"

    def test_get_provider_config_not_found(self) -> None:
        """get_provider_config should return None for unknown provider."""
        from framework_m.adapters.web.oauth_routes import get_provider_config

        config = {"auth": {"oauth": {"enabled": True, "providers": []}}}

        with patch(
            "framework_m.adapters.web.oauth_routes.load_config",
            return_value=config,
        ):
            provider = get_provider_config("unknown")

        assert provider is None


# =============================================================================
# Test: OAuth Router Configuration
# =============================================================================


class TestOAuthRouterConfig:
    """Tests for OAuth router configuration."""

    def test_router_has_correct_path(self) -> None:
        """OAuth router should be mounted at /api/v1/auth/oauth."""
        from framework_m.adapters.web.oauth_routes import oauth_routes_router

        assert oauth_routes_router.path == "/api/v1/auth/oauth"

    def test_router_has_auth_tag(self) -> None:
        """OAuth router should have 'auth' tag."""
        from framework_m.adapters.web.oauth_routes import oauth_routes_router

        assert "auth" in oauth_routes_router.tags


# =============================================================================
# Test: Generic OIDC Support
# =============================================================================


class TestGenericOIDCImport:
    """Tests for Generic OIDC helper functions."""

    def test_import_get_oidc_well_known(self) -> None:
        """get_oidc_well_known should be importable."""
        from framework_m.adapters.web.oauth_routes import get_oidc_well_known

        assert get_oidc_well_known is not None

    def test_import_is_generic_oidc_provider(self) -> None:
        """is_generic_oidc_provider should be importable."""
        from framework_m.adapters.web.oauth_routes import is_generic_oidc_provider

        assert is_generic_oidc_provider is not None


class TestGenericOIDCConfig:
    """Tests for Generic OIDC configuration."""

    def test_well_known_providers_not_generic(self) -> None:
        """Well-known providers should not be detected as generic OIDC."""
        from framework_m.adapters.web.oauth_routes import is_generic_oidc_provider

        assert is_generic_oidc_provider("google") is False
        assert is_generic_oidc_provider("github") is False
        assert is_generic_oidc_provider("microsoft") is False

    def test_custom_provider_is_generic(self) -> None:
        """Custom provider should be detected as generic OIDC."""
        from framework_m.adapters.web.oauth_routes import is_generic_oidc_provider

        assert is_generic_oidc_provider("keycloak") is True
        assert is_generic_oidc_provider("auth0") is True
        assert is_generic_oidc_provider("my-company-sso") is True

    def test_get_oidc_well_known_with_full_config(self) -> None:
        """get_oidc_well_known should return config when fully specified."""
        from framework_m.adapters.web.oauth_routes import get_oidc_well_known

        provider_cfg = {
            "authorization_url": "https://auth.example.com/authorize",
            "token_url": "https://auth.example.com/token",
            "userinfo_url": "https://auth.example.com/userinfo",
            "scope": "openid email custom",
        }

        result = get_oidc_well_known(provider_cfg)

        assert result is not None
        assert result["authorization_url"] == "https://auth.example.com/authorize"
        assert result["token_url"] == "https://auth.example.com/token"
        assert result["scope"] == "openid email custom"

    def test_get_oidc_well_known_with_minimal_config(self) -> None:
        """get_oidc_well_known should work with just auth and token URLs."""
        from framework_m.adapters.web.oauth_routes import get_oidc_well_known

        provider_cfg = {
            "authorization_url": "https://auth.example.com/authorize",
            "token_url": "https://auth.example.com/token",
        }

        result = get_oidc_well_known(provider_cfg)

        assert result is not None
        assert result["scope"] == "openid email profile"  # Default

    def test_get_oidc_well_known_missing_config(self) -> None:
        """get_oidc_well_known should return None for incomplete config."""
        from framework_m.adapters.web.oauth_routes import get_oidc_well_known

        # Missing token_url
        provider_cfg = {
            "authorization_url": "https://auth.example.com/authorize",
        }

        result = get_oidc_well_known(provider_cfg)

        assert result is None


# =============================================================================
# Test: OAuth Route Handler Integration Tests with TestClient
# =============================================================================


class TestOAuthRouteIntegration:
    """Integration tests for OAuth routes using Litestar TestClient."""

    @pytest.fixture
    def app(self) -> "Litestar":
        """Create test app with OAuth routes."""
        from litestar import Litestar

        from framework_m.adapters.web.oauth_routes import oauth_routes_router

        return Litestar(route_handlers=[oauth_routes_router])

    @pytest.fixture
    def client(self, app: "Litestar") -> "TestClient":
        """Create test client."""
        from litestar.testing import TestClient

        return TestClient(app)

    def test_oauth_start_google_redirects(self, client: "TestClient") -> None:
        """oauth_start should redirect to Google auth URL."""
        config = {
            "auth": {
                "oauth": {
                    "enabled": True,
                    "providers": ["google"],
                    "google": {
                        "client_id": "test-client-id",
                        "client_secret": "test-secret",
                    },
                }
            }
        }

        with patch(
            "framework_m.adapters.web.oauth_routes.load_config",
            return_value=config,
        ):
            response = client.get(
                "/api/v1/auth/oauth/google/start", follow_redirects=False
            )

        assert response.status_code in (302, 307)
        location = response.headers.get("location", "")
        assert "accounts.google.com" in location
        assert "client_id=test-client-id" in location

    def test_oauth_start_github_redirects(self, client: "TestClient") -> None:
        """oauth_start should redirect to GitHub auth URL."""
        config = {
            "auth": {
                "oauth": {
                    "enabled": True,
                    "providers": ["github"],
                    "github": {
                        "client_id": "github-client",
                        "client_secret": "github-secret",
                    },
                }
            }
        }

        with patch(
            "framework_m.adapters.web.oauth_routes.load_config",
            return_value=config,
        ):
            response = client.get(
                "/api/v1/auth/oauth/github/start", follow_redirects=False
            )

        assert response.status_code in (302, 307)
        location = response.headers.get("location", "")
        assert "github.com" in location

    def test_oauth_start_unknown_provider_returns_404(
        self, client: "TestClient"
    ) -> None:
        """oauth_start should return 404 for unknown provider."""
        config = {"auth": {"oauth": {"enabled": True, "providers": []}}}

        with patch(
            "framework_m.adapters.web.oauth_routes.load_config",
            return_value=config,
        ):
            response = client.get("/api/v1/auth/oauth/unknown/start")

        assert response.status_code == 404

    def test_oauth_start_includes_state_parameter(self, client: "TestClient") -> None:
        """oauth_start should include state parameter for CSRF protection."""
        config = {
            "auth": {
                "oauth": {
                    "enabled": True,
                    "providers": ["google"],
                    "google": {
                        "client_id": "test-client-id",
                        "client_secret": "test-secret",
                    },
                }
            }
        }

        with patch(
            "framework_m.adapters.web.oauth_routes.load_config",
            return_value=config,
        ):
            response = client.get(
                "/api/v1/auth/oauth/google/start", follow_redirects=False
            )

        location = response.headers.get("location", "")
        assert "state=" in location

    def test_oauth_callback_with_error_returns_401(self, client: "TestClient") -> None:
        """oauth_callback should return 401 when error parameter present."""
        response = client.get("/api/v1/auth/oauth/google/callback?error=access_denied")

        assert response.status_code == 401

    def test_oauth_callback_missing_code_returns_401(self, client: TestClient) -> None:
        """oauth_callback should return 401 when code is missing."""
        response = client.get(
            "/api/v1/auth/oauth/google/callback?oauth_state=some-state"
        )

        assert response.status_code == 401

    def test_oauth_start_microsoft_redirects(self, client: "TestClient") -> None:
        """oauth_start should redirect to Microsoft auth URL."""
        config = {
            "auth": {
                "oauth": {
                    "enabled": True,
                    "providers": ["microsoft"],
                    "microsoft": {
                        "client_id": "ms-client",
                        "client_secret": "ms-secret",
                    },
                }
            }
        }

        with patch(
            "framework_m.adapters.web.oauth_routes.load_config",
            return_value=config,
        ):
            response = client.get(
                "/api/v1/auth/oauth/microsoft/start", follow_redirects=False
            )

        assert response.status_code in (302, 307)
        location = response.headers.get("location", "")
        assert "login.microsoftonline.com" in location

"""Tests for Magic Link Authentication routes.

Tests cover:
- Token generation and verification
- Magic link request/response
- Security (expiry, one-time use)
- Integration tests with TestClient
"""

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from framework_m.adapters.web.magic_link_routes import (
    MagicLinkConfig,
    MagicLinkRequest,
    MagicLinkResponse,
    MagicLinkVerifyResponse,
    _pending_tokens,
    clear_expired_tokens,
    configure_magic_link,
    create_magic_link_router,
    generate_magic_token,
    verify_magic_token,
)

# =============================================================================
# Test: Imports
# =============================================================================


class TestMagicLinkImports:
    """Tests for magic link imports."""

    def test_import_router(self) -> None:
        """magic_link_router should be importable."""
        from framework_m.adapters.web.magic_link_routes import magic_link_router

        assert magic_link_router is not None

    def test_import_config(self) -> None:
        """MagicLinkConfig should be importable."""
        from framework_m.adapters.web.magic_link_routes import MagicLinkConfig

        assert MagicLinkConfig is not None

    def test_import_dtos(self) -> None:
        """DTOs should be importable."""
        from framework_m.adapters.web.magic_link_routes import (
            MagicLinkRequest,
            MagicLinkResponse,
            MagicLinkVerifyResponse,
        )

        assert MagicLinkRequest is not None
        assert MagicLinkResponse is not None
        assert MagicLinkVerifyResponse is not None


# =============================================================================
# Test: Configuration
# =============================================================================


class TestMagicLinkConfig:
    """Tests for MagicLinkConfig."""

    def test_default_config(self) -> None:
        """Config should have sensible defaults."""
        config = MagicLinkConfig(secret_key="test-secret")

        assert config.secret_key == "test-secret"
        assert config.token_expiry == 900  # 15 minutes
        assert config.link_base_url == "http://localhost:8000"

    def test_custom_config(self) -> None:
        """Config should accept custom values."""
        config = MagicLinkConfig(
            secret_key="custom-secret",
            token_expiry=1800,
            link_base_url="https://app.example.com",
        )

        assert config.token_expiry == 1800
        assert config.link_base_url == "https://app.example.com"

    def test_configure_magic_link(self) -> None:
        """configure_magic_link should set config."""
        config = MagicLinkConfig(secret_key="test")
        configure_magic_link(config)
        # Should not raise


# =============================================================================
# Test: Token Generation
# =============================================================================


class TestTokenGeneration:
    """Tests for token generation."""

    def test_generate_token(self) -> None:
        """generate_magic_token should create token."""
        import time

        expiry = int(time.time()) + 900
        token = generate_magic_token("user@example.com", expiry)

        assert token is not None
        assert "." in token  # Has signature separator
        assert len(token) > 64  # Reasonable length

    def test_tokens_are_unique(self) -> None:
        """Each generated token should be unique."""
        import time

        expiry = int(time.time()) + 900
        token1 = generate_magic_token("user@example.com", expiry)
        token2 = generate_magic_token("user@example.com", expiry)

        assert token1 != token2


# =============================================================================
# Test: Token Verification
# =============================================================================


class TestTokenVerification:
    """Tests for token verification."""

    def test_verify_valid_token(self) -> None:
        """verify_magic_token should accept valid token."""
        import time

        expiry = int(time.time()) + 900
        token = generate_magic_token("user@example.com", expiry)

        stored_data = {
            "email": "user@example.com",
            "expiry": expiry,
        }

        result = verify_magic_token(token, stored_data)
        assert result is True

    def test_verify_expired_token(self) -> None:
        """verify_magic_token should reject expired token."""
        import time

        expiry = int(time.time()) - 100  # Expired
        token = generate_magic_token("user@example.com", expiry)

        stored_data = {
            "email": "user@example.com",
            "expiry": expiry,
        }

        result = verify_magic_token(token, stored_data)
        assert result is False

    def test_verify_tampered_token(self) -> None:
        """verify_magic_token should reject tampered token."""
        import time

        expiry = int(time.time()) + 900
        token = generate_magic_token("user@example.com", expiry)

        stored_data = {
            "email": "user@example.com",
            "expiry": expiry,
        }

        # Tamper with token
        tampered = token[:-5] + "xxxxx"

        result = verify_magic_token(tampered, stored_data)
        assert result is False

    def test_verify_wrong_email(self) -> None:
        """verify_magic_token should reject token for wrong email."""
        import time

        expiry = int(time.time()) + 900
        token = generate_magic_token("user@example.com", expiry)

        stored_data = {
            "email": "other@example.com",  # Different email
            "expiry": expiry,
        }

        result = verify_magic_token(token, stored_data)
        assert result is False


# =============================================================================
# Test: DTOs
# =============================================================================


class TestDTOs:
    """Tests for request/response DTOs."""

    def test_magic_link_request(self) -> None:
        """MagicLinkRequest should validate email."""
        request = MagicLinkRequest(email="user@example.com")
        assert request.email == "user@example.com"
        assert request.redirect_url is None

    def test_magic_link_request_with_redirect(self) -> None:
        """MagicLinkRequest should accept redirect URL."""
        request = MagicLinkRequest(
            email="user@example.com",
            redirect_url="/dashboard",
        )
        assert request.redirect_url == "/dashboard"

    def test_magic_link_response(self) -> None:
        """MagicLinkResponse should contain message."""
        response = MagicLinkResponse(
            message="Link sent",
            expires_in=900,
        )
        assert response.expires_in == 900

    def test_magic_link_verify_response(self) -> None:
        """MagicLinkVerifyResponse should contain tokens."""
        response = MagicLinkVerifyResponse(
            access_token="abc123",
            token_type="bearer",
            expires_in=86400,
        )
        assert response.access_token == "abc123"
        assert response.token_type == "bearer"


# =============================================================================
# Test: Router
# =============================================================================


class TestRouter:
    """Tests for router creation."""

    def test_create_router(self) -> None:
        """create_magic_link_router should return Router."""
        from litestar import Router

        router = create_magic_link_router()
        assert isinstance(router, Router)
        assert router.path == "/api/v1/auth"


# =============================================================================
# Test: Token Cleanup
# =============================================================================


class TestTokenCleanup:
    """Tests for token cleanup."""

    def test_clear_expired_tokens(self) -> None:
        """clear_expired_tokens should remove expired tokens."""
        import time

        # Clear any existing tokens
        _pending_tokens.clear()

        # Add expired token
        _pending_tokens["expired-token"] = {
            "email": "user@example.com",
            "expiry": int(time.time()) - 100,
        }

        # Add valid token
        _pending_tokens["valid-token"] = {
            "email": "user2@example.com",
            "expiry": int(time.time()) + 900,
        }

        cleared = clear_expired_tokens()

        assert cleared == 1
        assert "expired-token" not in _pending_tokens
        assert "valid-token" in _pending_tokens

        # Cleanup
        _pending_tokens.clear()


# =============================================================================
# Test: MagicLinkCredentials
# =============================================================================


class TestMagicLinkCredentials:
    """Tests for MagicLinkCredentials."""

    def test_import(self) -> None:
        """MagicLinkCredentials should be importable."""
        from framework_m.core.interfaces.identity import MagicLinkCredentials

        assert MagicLinkCredentials is not None

    def test_create(self) -> None:
        """MagicLinkCredentials should work with email and token."""
        from framework_m.core.interfaces.identity import MagicLinkCredentials

        creds = MagicLinkCredentials(
            email="user@example.com",
            token="abc123",
        )

        assert creds.email == "user@example.com"
        assert creds.token == "abc123"

    def test_is_credentials_subclass(self) -> None:
        """MagicLinkCredentials should inherit from Credentials."""
        from framework_m.core.interfaces.identity import (
            Credentials,
            MagicLinkCredentials,
        )

        assert issubclass(MagicLinkCredentials, Credentials)


# =============================================================================
# Test: Integration Tests with TestClient
# =============================================================================


class TestMagicLinkIntegration:
    """Integration tests for magic link routes using TestClient."""

    @pytest.fixture(autouse=True)
    def reset_tokens(self) -> None:
        """Reset pending tokens before each test."""
        _pending_tokens.clear()

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Configure magic link before tests."""
        config = MagicLinkConfig(
            secret_key="test-secret-key",
            token_expiry=900,
        )
        configure_magic_link(config)

    @pytest.fixture
    def app(self) -> "Litestar":
        """Create test app with magic link routes."""
        from litestar import Litestar

        from framework_m.adapters.web.magic_link_routes import magic_link_router

        return Litestar(route_handlers=[magic_link_router])

    @pytest.fixture
    def client(self, app: "Litestar") -> "TestClient":
        """Create test client."""
        from litestar.testing import TestClient

        return TestClient(app)

    def test_request_magic_link_returns_202(self, client: "TestClient") -> None:
        """POST /magic-link should return 202 Accepted."""
        response = client.post(
            "/api/v1/auth/magic-link",
            json={"email": "user@example.com"},
        )

        assert response.status_code == 202
        data = response.json()
        assert "message" in data
        assert data["expires_in"] == 900

    def test_request_magic_link_creates_token(self, client: "TestClient") -> None:
        """POST /magic-link should create pending token."""
        client.post(
            "/api/v1/auth/magic-link",
            json={"email": "test@example.com"},
        )

        # Should have created a token
        assert len(_pending_tokens) == 1

    def test_verify_magic_link_success(self, client: "TestClient") -> None:
        """GET /magic-link/{token} should verify valid token."""
        import time

        # Create a valid token
        expiry = int(time.time()) + 900
        token = generate_magic_token("user@example.com", expiry)
        _pending_tokens[token] = {
            "email": "user@example.com",
            "expiry": expiry,
        }

        response = client.get(f"/api/v1/auth/magic-link/{token}")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_verify_magic_link_not_found(self, client: "TestClient") -> None:
        """GET /magic-link/{token} should return 404 for unknown token."""
        response = client.get("/api/v1/auth/magic-link/unknown-token")

        assert response.status_code == 404

    def test_verify_magic_link_expired(self, client: "TestClient") -> None:
        """GET /magic-link/{token} should return 401 for expired token."""
        import time

        # Create an expired token
        expiry = int(time.time()) - 100  # Already expired
        token = generate_magic_token("user@example.com", expiry)
        _pending_tokens[token] = {
            "email": "user@example.com",
            "expiry": expiry,
        }

        response = client.get(f"/api/v1/auth/magic-link/{token}")

        assert response.status_code == 401

    def test_verify_magic_link_removes_token(self, client: "TestClient") -> None:
        """Verifying a token should remove it (one-time use)."""
        import time

        expiry = int(time.time()) + 900
        token = generate_magic_token("user@example.com", expiry)
        _pending_tokens[token] = {
            "email": "user@example.com",
            "expiry": expiry,
        }

        client.get(f"/api/v1/auth/magic-link/{token}")

        # Token should be removed
        assert token not in _pending_tokens

    def test_request_magic_link_with_redirect(self, client: "TestClient") -> None:
        """POST /magic-link should accept redirect_url."""
        response = client.post(
            "/api/v1/auth/magic-link",
            json={"email": "user@example.com", "redirect_url": "/dashboard"},
        )

        assert response.status_code == 202

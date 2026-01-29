"""Tests for Authentication Strategies.

TDD: This test file is created BEFORE the implementation.

Tests cover:
- AuthenticationProtocol interface
- BearerTokenAuth strategy
- ApiKeyAuth strategy
- AuthChainMiddleware (strategy chain)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from framework_m.core.interfaces.auth_context import UserContext

# =============================================================================
# Test: AuthenticationProtocol Import
# =============================================================================


class TestAuthenticationProtocolImport:
    """Tests for AuthenticationProtocol interface import."""

    def test_import_authentication_protocol(self) -> None:
        """AuthenticationProtocol should be importable."""
        from framework_m.core.interfaces.authentication import (
            AuthenticationProtocol,
        )

        assert AuthenticationProtocol is not None

    def test_protocol_has_supports_method(self) -> None:
        """AuthenticationProtocol should define supports method."""
        import inspect

        from framework_m.core.interfaces.authentication import (
            AuthenticationProtocol,
        )

        # Get method signatures from protocol
        methods = dict(inspect.getmembers(AuthenticationProtocol))
        assert "supports" in methods

    def test_protocol_has_authenticate_method(self) -> None:
        """AuthenticationProtocol should define authenticate method."""
        import inspect

        from framework_m.core.interfaces.authentication import (
            AuthenticationProtocol,
        )

        methods = dict(inspect.getmembers(AuthenticationProtocol))
        assert "authenticate" in methods


# =============================================================================
# Test: BearerTokenAuth Strategy
# =============================================================================


class TestBearerTokenAuthImport:
    """Tests for BearerTokenAuth strategy import."""

    def test_import_bearer_token_auth(self) -> None:
        """BearerTokenAuth should be importable."""
        from framework_m.adapters.auth.strategies import BearerTokenAuth

        assert BearerTokenAuth is not None


class TestBearerTokenAuthSupports:
    """Tests for BearerTokenAuth.supports method."""

    def test_supports_authorization_bearer(self) -> None:
        """supports() should return True for Authorization: Bearer header."""
        from framework_m.adapters.auth.strategies import BearerTokenAuth

        strategy = BearerTokenAuth(jwt_secret="test-secret")

        mock_headers = {
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
        assert strategy.supports(mock_headers) is True

    def test_not_supports_missing_header(self) -> None:
        """supports() should return False when no Authorization header."""
        from framework_m.adapters.auth.strategies import BearerTokenAuth

        strategy = BearerTokenAuth(jwt_secret="test-secret")

        mock_headers: dict[str, str] = {}
        assert strategy.supports(mock_headers) is False

    def test_not_supports_basic_auth(self) -> None:
        """supports() should return False for Basic auth."""
        from framework_m.adapters.auth.strategies import BearerTokenAuth

        strategy = BearerTokenAuth(jwt_secret="test-secret")

        mock_headers = {"authorization": "Basic dXNlcjpwYXNz"}
        assert strategy.supports(mock_headers) is False


class TestBearerTokenAuthAuthenticate:
    """Tests for BearerTokenAuth.authenticate method."""

    @pytest.mark.asyncio
    async def test_authenticate_valid_token(self) -> None:
        """authenticate() should return UserContext for valid JWT."""
        from datetime import UTC, datetime, timedelta

        import jwt

        from framework_m.adapters.auth.strategies import BearerTokenAuth

        secret = "test-secret"
        strategy = BearerTokenAuth(jwt_secret=secret)

        # Create valid token
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        mock_headers = {"authorization": f"Bearer {token}"}
        result = await strategy.authenticate(mock_headers)

        assert result is not None
        assert result.id == "user-123"
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_token(self) -> None:
        """authenticate() should return None for invalid JWT."""
        from framework_m.adapters.auth.strategies import BearerTokenAuth

        strategy = BearerTokenAuth(jwt_secret="test-secret")

        mock_headers = {"authorization": "Bearer invalid.token.here"}
        result = await strategy.authenticate(mock_headers)

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_expired_token(self) -> None:
        """authenticate() should return None for expired JWT."""
        from datetime import UTC, datetime, timedelta

        import jwt

        from framework_m.adapters.auth.strategies import BearerTokenAuth

        secret = "test-secret"
        strategy = BearerTokenAuth(jwt_secret=secret)

        # Create expired token
        payload = {
            "sub": "user-123",
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        mock_headers = {"authorization": f"Bearer {token}"}
        result = await strategy.authenticate(mock_headers)

        assert result is None


# =============================================================================
# Test: ApiKeyAuth Strategy
# =============================================================================


class TestApiKeyAuthImport:
    """Tests for ApiKeyAuth strategy import."""

    def test_import_api_key_auth(self) -> None:
        """ApiKeyAuth should be importable."""
        from framework_m.adapters.auth.strategies import ApiKeyAuth

        assert ApiKeyAuth is not None


class TestApiKeyAuthSupports:
    """Tests for ApiKeyAuth.supports method."""

    def test_supports_x_api_key_header(self) -> None:
        """supports() should return True for X-API-Key header."""
        from framework_m.adapters.auth.strategies import ApiKeyAuth

        mock_lookup = AsyncMock()
        strategy = ApiKeyAuth(api_key_lookup=mock_lookup)

        mock_headers = {"x-api-key": "sk_live_abc123"}
        assert strategy.supports(mock_headers) is True

    def test_not_supports_missing_header(self) -> None:
        """supports() should return False when no X-API-Key header."""
        from framework_m.adapters.auth.strategies import ApiKeyAuth

        mock_lookup = AsyncMock()
        strategy = ApiKeyAuth(api_key_lookup=mock_lookup)

        mock_headers: dict[str, str] = {}
        assert strategy.supports(mock_headers) is False


class TestApiKeyAuthAuthenticate:
    """Tests for ApiKeyAuth.authenticate method."""

    @pytest.mark.asyncio
    async def test_authenticate_valid_key(self) -> None:
        """authenticate() should return UserContext for valid API key."""
        from framework_m.adapters.auth.strategies import ApiKeyAuth

        mock_lookup = AsyncMock()
        mock_lookup.return_value = UserContext(
            id="user-123",
            email="api@example.com",
            roles=["API"],
        )
        strategy = ApiKeyAuth(api_key_lookup=mock_lookup)

        mock_headers = {"x-api-key": "sk_live_valid"}
        result = await strategy.authenticate(mock_headers)

        assert result is not None
        assert result.id == "user-123"
        mock_lookup.assert_called_once_with("sk_live_valid")

    @pytest.mark.asyncio
    async def test_authenticate_invalid_key(self) -> None:
        """authenticate() should return None for invalid API key."""
        from framework_m.adapters.auth.strategies import ApiKeyAuth

        mock_lookup = AsyncMock()
        mock_lookup.return_value = None
        strategy = ApiKeyAuth(api_key_lookup=mock_lookup)

        mock_headers = {"x-api-key": "sk_live_invalid"}
        result = await strategy.authenticate(mock_headers)

        assert result is None


# =============================================================================
# Test: HeaderAuth Strategy (Federated Mode)
# =============================================================================


class TestHeaderAuthImport:
    """Tests for HeaderAuth strategy import."""

    def test_import_header_auth(self) -> None:
        """HeaderAuth should be importable."""
        from framework_m.adapters.auth.strategies import HeaderAuth

        assert HeaderAuth is not None


class TestHeaderAuthSupports:
    """Tests for HeaderAuth.supports method."""

    def test_supports_x_user_id_header(self) -> None:
        """supports() should return True for X-User-ID header."""
        from framework_m.adapters.auth.strategies import HeaderAuth

        strategy = HeaderAuth()

        mock_headers = {"x-user-id": "user-123", "x-email": "user@example.com"}
        assert strategy.supports(mock_headers) is True

    def test_not_supports_missing_header(self) -> None:
        """supports() should return False when no X-User-ID header."""
        from framework_m.adapters.auth.strategies import HeaderAuth

        strategy = HeaderAuth()

        mock_headers: dict[str, str] = {}
        assert strategy.supports(mock_headers) is False


# =============================================================================
# Test: BasicAuth Strategy
# =============================================================================


class TestBasicAuthImport:
    """Tests for BasicAuth import."""

    def test_import_basic_auth(self) -> None:
        """BasicAuth should be importable."""
        from framework_m.adapters.auth.strategies import BasicAuth

        assert BasicAuth is not None


class TestBasicAuthSupports:
    """Tests for BasicAuth.supports method."""

    def test_supports_basic_header(self) -> None:
        """supports() should return True for Basic auth header."""
        from framework_m.adapters.auth.strategies import BasicAuth

        mock_authenticate = AsyncMock()
        strategy = BasicAuth(authenticate_fn=mock_authenticate)

        mock_headers = {"authorization": "Basic dXNlcjpwYXNz"}  # user:pass
        assert strategy.supports(mock_headers) is True

    def test_not_supports_bearer(self) -> None:
        """supports() should return False for Bearer token."""
        from framework_m.adapters.auth.strategies import BasicAuth

        mock_authenticate = AsyncMock()
        strategy = BasicAuth(authenticate_fn=mock_authenticate)

        mock_headers = {"authorization": "Bearer token123"}
        assert strategy.supports(mock_headers) is False

    def test_not_supports_missing_header(self) -> None:
        """supports() should return False when no Authorization header."""
        from framework_m.adapters.auth.strategies import BasicAuth

        mock_authenticate = AsyncMock()
        strategy = BasicAuth(authenticate_fn=mock_authenticate)

        mock_headers: dict[str, str] = {}
        assert strategy.supports(mock_headers) is False


class TestBasicAuthAuthenticate:
    """Tests for BasicAuth.authenticate method."""

    @pytest.mark.asyncio
    async def test_authenticate_valid_credentials(self) -> None:
        """authenticate() should return UserContext for valid credentials."""
        import base64

        from framework_m.adapters.auth.strategies import BasicAuth

        mock_authenticate = AsyncMock()
        mock_authenticate.return_value = UserContext(
            id="user-001",
            email="user@example.com",
        )

        strategy = BasicAuth(authenticate_fn=mock_authenticate)

        # "user:password" in base64
        creds = base64.b64encode(b"user:password").decode()
        mock_headers = {"authorization": f"Basic {creds}"}
        result = await strategy.authenticate(mock_headers)

        assert result is not None
        assert result.id == "user-001"
        mock_authenticate.assert_called_once_with("user", "password")

    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(self) -> None:
        """authenticate() should return None for invalid credentials."""
        import base64

        from framework_m.adapters.auth.strategies import BasicAuth

        mock_authenticate = AsyncMock(return_value=None)
        strategy = BasicAuth(authenticate_fn=mock_authenticate)

        creds = base64.b64encode(b"user:wrongpass").decode()
        mock_headers = {"authorization": f"Basic {creds}"}
        result = await strategy.authenticate(mock_headers)

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_malformed_base64(self) -> None:
        """authenticate() should return None for malformed base64."""
        from framework_m.adapters.auth.strategies import BasicAuth

        mock_authenticate = AsyncMock()
        strategy = BasicAuth(authenticate_fn=mock_authenticate)

        mock_headers = {"authorization": "Basic not-valid-base64!!!"}
        result = await strategy.authenticate(mock_headers)

        assert result is None
        mock_authenticate.assert_not_called()


# =============================================================================
# Test: Strategy Chain
# =============================================================================


class TestAuthChainImport:
    """Tests for AuthChain import."""

    def test_import_auth_chain(self) -> None:
        """AuthChain should be importable."""
        from framework_m.adapters.auth.strategies import AuthChain

        assert AuthChain is not None


class TestAuthChainAuthenticate:
    """Tests for AuthChain authentication."""

    @pytest.mark.asyncio
    async def test_first_matching_strategy_wins(self) -> None:
        """AuthChain should use first strategy that supports the request."""
        from framework_m.adapters.auth.strategies import AuthChain

        strategy1 = MagicMock()
        strategy1.supports = MagicMock(return_value=False)
        strategy1.authenticate = AsyncMock()

        strategy2 = MagicMock()
        strategy2.supports = MagicMock(return_value=True)
        strategy2.authenticate = AsyncMock(
            return_value=UserContext(id="user-123", email="test@example.com")
        )

        chain = AuthChain(strategies=[strategy1, strategy2])

        mock_headers: dict[str, str] = {"some": "header"}
        result = await chain.authenticate(mock_headers)

        assert result is not None
        assert result.id == "user-123"
        strategy1.supports.assert_called_once()
        strategy1.authenticate.assert_not_called()
        strategy2.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_no_strategy_matches(self) -> None:
        """AuthChain should return None when no strategy matches."""
        from framework_m.adapters.auth.strategies import AuthChain

        strategy1 = MagicMock()
        strategy1.supports = MagicMock(return_value=False)

        chain = AuthChain(strategies=[strategy1])

        mock_headers: dict[str, str] = {}
        result = await chain.authenticate(mock_headers)

        assert result is None


# =============================================================================
# Test: SessionCookieAuth Strategy
# =============================================================================


class TestSessionCookieAuthImport:
    """Tests for SessionCookieAuth import."""

    def test_import_session_cookie_auth(self) -> None:
        """SessionCookieAuth should be importable."""
        from framework_m.adapters.auth.strategies import SessionCookieAuth

        assert SessionCookieAuth is not None


class TestSessionCookieAuthSupports:
    """Tests for SessionCookieAuth.supports method."""

    def test_supports_session_cookie(self) -> None:
        """supports() should return True when session cookie present."""
        from framework_m.adapters.auth.strategies import SessionCookieAuth

        mock_session_store = AsyncMock()
        strategy = SessionCookieAuth(
            session_store=mock_session_store,
            cookie_name="session_id",
        )

        mock_headers = {"cookie": "session_id=sess_abc123; other=value"}
        assert strategy.supports(mock_headers) is True

    def test_not_supports_without_cookie(self) -> None:
        """supports() should return False when no session cookie."""
        from framework_m.adapters.auth.strategies import SessionCookieAuth

        mock_session_store = AsyncMock()
        strategy = SessionCookieAuth(
            session_store=mock_session_store,
            cookie_name="session_id",
        )

        mock_headers: dict[str, str] = {}
        assert strategy.supports(mock_headers) is False

    def test_not_supports_different_cookie(self) -> None:
        """supports() should return False for different cookie name."""
        from framework_m.adapters.auth.strategies import SessionCookieAuth

        mock_session_store = AsyncMock()
        strategy = SessionCookieAuth(
            session_store=mock_session_store,
            cookie_name="session_id",
        )

        mock_headers = {"cookie": "other_cookie=value"}
        assert strategy.supports(mock_headers) is False


class TestSessionCookieAuthAuthenticate:
    """Tests for SessionCookieAuth.authenticate method."""

    @pytest.mark.asyncio
    async def test_authenticate_valid_session(self) -> None:
        """authenticate() should return UserContext for valid session."""
        from datetime import UTC, datetime, timedelta

        from framework_m.adapters.auth.strategies import SessionCookieAuth
        from framework_m.core.interfaces.session import SessionData

        mock_session_store = AsyncMock()
        mock_session_store.get.return_value = SessionData(
            session_id="sess_abc123",
            user_id="user-001",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        strategy = SessionCookieAuth(
            session_store=mock_session_store,
            cookie_name="session_id",
        )

        mock_headers = {"cookie": "session_id=sess_abc123"}
        result = await strategy.authenticate(mock_headers)

        assert result is not None
        assert result.id == "user-001"
        mock_session_store.get.assert_called_once_with("sess_abc123")

    @pytest.mark.asyncio
    async def test_authenticate_invalid_session(self) -> None:
        """authenticate() should return None for invalid session."""
        from framework_m.adapters.auth.strategies import SessionCookieAuth

        mock_session_store = AsyncMock()
        mock_session_store.get.return_value = None

        strategy = SessionCookieAuth(
            session_store=mock_session_store,
            cookie_name="session_id",
        )

        mock_headers = {"cookie": "session_id=sess_invalid"}
        result = await strategy.authenticate(mock_headers)

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_with_user_lookup(self) -> None:
        """authenticate() should use user_lookup for full details."""
        from datetime import UTC, datetime, timedelta

        from framework_m.adapters.auth.strategies import SessionCookieAuth
        from framework_m.core.interfaces.session import SessionData

        mock_session_store = AsyncMock()
        mock_session_store.get.return_value = SessionData(
            session_id="sess_abc123",
            user_id="user-001",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        mock_user = MagicMock()
        mock_user.id = "user-001"
        mock_user.email = "user@example.com"
        mock_user.full_name = "Test User"
        mock_user.roles = ["User"]

        mock_user_lookup = AsyncMock(return_value=mock_user)

        strategy = SessionCookieAuth(
            session_store=mock_session_store,
            cookie_name="session_id",
            user_lookup=mock_user_lookup,
        )

        mock_headers = {"cookie": "session_id=sess_abc123"}
        result = await strategy.authenticate(mock_headers)

        assert result is not None
        assert result.id == "user-001"
        assert result.email == "user@example.com"
        mock_user_lookup.assert_called_once_with("user-001")

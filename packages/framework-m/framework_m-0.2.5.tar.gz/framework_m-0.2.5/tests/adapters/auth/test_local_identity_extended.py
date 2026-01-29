"""Extended tests for local_identity.py to increase coverage.

These tests cover previously untested code paths and edge cases.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import jwt
import pytest

from framework_m.core.doctypes.user import LocalUser
from framework_m.core.exceptions import AuthenticationError
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.identity import PasswordCredentials, Token

# =============================================================================
# Tests for get_user_by_email
# =============================================================================


class TestLocalIdentityAdapterGetUserByEmail:
    """Tests for LocalIdentityAdapter.get_user_by_email method."""

    @pytest.mark.asyncio
    async def test_get_user_by_email_returns_user_context(self) -> None:
        """get_user_by_email should return UserContext for valid email."""
        from framework_m.adapters.auth.local_identity import (
            LocalIdentityAdapter,
            hash_password,
        )

        mock_repo = AsyncMock()
        password_hash = hash_password("secret123")
        mock_user = LocalUser(
            email="test@example.com",
            password_hash=password_hash,
            full_name="Test User",
        )
        mock_repo.get_by_email.return_value = mock_user

        adapter = LocalIdentityAdapter(user_repository=mock_repo)
        result = await adapter.get_user_by_email("test@example.com")

        assert result is not None
        assert isinstance(result, UserContext)
        assert result.email == "test@example.com"
        assert result.name == "Test User"

    @pytest.mark.asyncio
    async def test_get_user_by_email_returns_none_for_missing_user(self) -> None:
        """get_user_by_email should return None for non-existent email."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = None

        adapter = LocalIdentityAdapter(user_repository=mock_repo)
        result = await adapter.get_user_by_email("nonexistent@example.com")

        assert result is None


# =============================================================================
# Tests for get_attributes
# =============================================================================


class TestLocalIdentityAdapterGetAttributes:
    """Tests for LocalIdentityAdapter.get_attributes method."""

    @pytest.mark.asyncio
    async def test_get_attributes_returns_user_attributes(self) -> None:
        """get_attributes should return user attributes dict."""
        from framework_m.adapters.auth.local_identity import (
            LocalIdentityAdapter,
            hash_password,
        )

        mock_repo = AsyncMock()
        password_hash = hash_password("secret123")
        mock_user = LocalUser(
            email="test@example.com",
            password_hash=password_hash,
            full_name="Test User",
            is_active=True,
        )
        mock_repo.get.return_value = mock_user

        adapter = LocalIdentityAdapter(user_repository=mock_repo)
        result = await adapter.get_attributes(str(mock_user.id))

        assert result["email"] == "test@example.com"
        assert result["full_name"] == "Test User"
        assert result["is_active"] is True
        assert "roles" in result
        assert "teams" in result
        assert "tenants" in result

    @pytest.mark.asyncio
    async def test_get_attributes_returns_empty_for_missing_user(self) -> None:
        """get_attributes should return empty dict for non-existent user."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None

        adapter = LocalIdentityAdapter(user_repository=mock_repo)
        result = await adapter.get_attributes("non-existent-id")

        assert result == {}


# =============================================================================
# Tests for validate_token
# =============================================================================


class TestLocalIdentityAdapterValidateToken:
    """Tests for LocalIdentityAdapter.validate_token method."""

    @pytest.mark.asyncio
    async def test_validate_token_returns_user_context_for_valid_token(self) -> None:
        """validate_token should return UserContext for valid JWT."""
        from framework_m.adapters.auth.local_identity import (
            LocalIdentityAdapter,
            hash_password,
        )

        mock_repo = AsyncMock()
        password_hash = hash_password("secret123")
        mock_user = LocalUser(
            email="test@example.com",
            password_hash=password_hash,
            full_name="Test User",
        )
        mock_repo.get.return_value = mock_user
        mock_repo.get_by_email.return_value = mock_user

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
        )

        # Authenticate to get a valid token
        credentials = PasswordCredentials(
            username="test@example.com",
            password="secret123",
        )
        token = await adapter.authenticate(credentials)

        # Validate the token
        result = await adapter.validate_token(token.access_token)

        assert result is not None
        assert isinstance(result, UserContext)
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_validate_token_returns_none_for_invalid_token(self) -> None:
        """validate_token should return None for invalid JWT."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        mock_repo = AsyncMock()

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
        )

        result = await adapter.validate_token("invalid.jwt.token")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_token_returns_none_for_expired_token(self) -> None:
        """validate_token should return None for expired JWT."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        mock_repo = AsyncMock()

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
        )

        # Create an expired token
        past_time = datetime.now(UTC) - timedelta(hours=25)
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "iat": past_time,
            "exp": past_time + timedelta(hours=1),  # Expired 24 hours ago
        }
        expired_token = jwt.encode(payload, "test-secret", algorithm="HS256")

        result = await adapter.validate_token(expired_token)

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_token_returns_none_for_token_without_sub(self) -> None:
        """validate_token should return None if token has no 'sub' claim."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        mock_repo = AsyncMock()

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
        )

        # Create a token without 'sub' claim
        now = datetime.now(UTC)
        payload = {
            "email": "test@example.com",
            "iat": now,
            "exp": now + timedelta(hours=24),
        }
        token_without_sub = jwt.encode(payload, "test-secret", algorithm="HS256")

        result = await adapter.validate_token(token_without_sub)

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_token_returns_none_if_user_not_found(self) -> None:
        """validate_token should return None if user no longer exists."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None  # User deleted

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
        )

        # Create a valid token
        now = datetime.now(UTC)
        payload = {
            "sub": "deleted-user-id",
            "email": "test@example.com",
            "iat": now,
            "exp": now + timedelta(hours=24),
        }
        valid_token = jwt.encode(payload, "test-secret", algorithm="HS256")

        result = await adapter.validate_token(valid_token)

        assert result is None


# =============================================================================
# Tests for authenticate with inactive user
# =============================================================================


class TestLocalIdentityAdapterAuthenticateInactive:
    """Tests for authenticating inactive users."""

    @pytest.mark.asyncio
    async def test_authenticate_raises_for_inactive_user(self) -> None:
        """authenticate should raise AuthenticationError for inactive user."""
        from framework_m.adapters.auth.local_identity import (
            LocalIdentityAdapter,
            hash_password,
        )

        mock_repo = AsyncMock()
        password_hash = hash_password("secret123")
        mock_user = LocalUser(
            email="test@example.com",
            password_hash=password_hash,
            full_name="Test User",
            is_active=False,  # Inactive user
        )
        mock_repo.get_by_email.return_value = mock_user

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
        )

        credentials = PasswordCredentials(
            username="test@example.com",
            password="secret123",
        )

        with pytest.raises(AuthenticationError) as exc_info:
            await adapter.authenticate(credentials)

        assert "disabled" in str(exc_info.value).lower()


# =============================================================================
# Tests for authenticate with unsupported credentials
# =============================================================================


class TestLocalIdentityAdapterAuthenticateUnsupported:
    """Tests for authenticating with unsupported credential types."""

    @pytest.mark.asyncio
    async def test_authenticate_raises_for_unsupported_credentials(self) -> None:
        """authenticate should raise for unsupported credential type."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter
        from framework_m.core.interfaces.identity import Credentials

        class UnsupportedCredentials(Credentials):
            """Mock unsupported credentials."""

            api_key: str

        mock_repo = AsyncMock()

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
        )

        credentials = UnsupportedCredentials(api_key="test-key")

        with pytest.raises(AuthenticationError) as exc_info:
            await adapter.authenticate(credentials)

        assert "unsupported" in str(exc_info.value).lower()


# =============================================================================
# Tests for _to_user_context
# =============================================================================


class TestLocalIdentityAdapterToUserContext:
    """Tests for _to_user_context helper method."""

    def test_to_user_context_converts_local_user(self) -> None:
        """_to_user_context should convert LocalUser to UserContext."""
        from framework_m.adapters.auth.local_identity import (
            LocalIdentityAdapter,
            hash_password,
        )

        mock_repo = AsyncMock()
        password_hash = hash_password("secret123")
        mock_user = LocalUser(
            email="test@example.com",
            password_hash=password_hash,
            full_name="Test User",
        )

        adapter = LocalIdentityAdapter(user_repository=mock_repo)
        result = adapter._to_user_context(mock_user)

        assert isinstance(result, UserContext)
        assert result.id == str(mock_user.id)
        assert result.email == "test@example.com"
        assert result.name == "Test User"
        assert result.roles == []
        assert result.tenants == []


# =============================================================================
# Tests for _generate_token
# =============================================================================


class TestLocalIdentityAdapterGenerateToken:
    """Tests for _generate_token helper method."""

    def test_generate_token_creates_valid_jwt(self) -> None:
        """_generate_token should create valid JWT token."""
        from framework_m.adapters.auth.local_identity import (
            LocalIdentityAdapter,
            hash_password,
        )

        mock_repo = AsyncMock()
        password_hash = hash_password("secret123")
        mock_user = LocalUser(
            email="test@example.com",
            password_hash=password_hash,
            full_name="Test User",
        )

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
            token_expiry_hours=24,
        )
        token = adapter._generate_token(mock_user)

        assert isinstance(token, Token)
        assert token.token_type == "Bearer"
        assert token.expires_in == 24 * 3600
        assert token.access_token is not None

        # Decode token to verify contents
        decoded = jwt.decode(
            token.access_token,
            "test-secret",
            algorithms=["HS256"],
        )
        assert decoded["sub"] == str(mock_user.id)
        assert decoded["email"] == "test@example.com"

    def test_generate_token_with_custom_expiry(self) -> None:
        """_generate_token should use custom expiry hours."""
        from framework_m.adapters.auth.local_identity import (
            LocalIdentityAdapter,
            hash_password,
        )

        mock_repo = AsyncMock()
        password_hash = hash_password("secret123")
        mock_user = LocalUser(
            email="test@example.com",
            password_hash=password_hash,
        )

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
            token_expiry_hours=48,  # Custom expiry
        )
        token = adapter._generate_token(mock_user)

        assert token.expires_in == 48 * 3600


# =============================================================================
# Tests for custom JWT algorithm
# =============================================================================


class TestLocalIdentityAdapterCustomAlgorithm:
    """Tests for custom JWT algorithm support."""

    @pytest.mark.asyncio
    async def test_adapter_with_custom_algorithm(self) -> None:
        """LocalIdentityAdapter should support custom JWT algorithm."""
        from framework_m.adapters.auth.local_identity import (
            LocalIdentityAdapter,
            hash_password,
        )

        mock_repo = AsyncMock()
        password_hash = hash_password("secret123")
        mock_user = LocalUser(
            email="test@example.com",
            password_hash=password_hash,
        )
        mock_repo.get_by_email.return_value = mock_user

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
            jwt_algorithm="HS512",  # Different algorithm
        )

        credentials = PasswordCredentials(
            username="test@example.com",
            password="secret123",
        )
        token = await adapter.authenticate(credentials)

        # Verify token can be decoded with the custom algorithm
        decoded = jwt.decode(
            token.access_token,
            "test-secret",
            algorithms=["HS512"],
        )
        assert decoded["email"] == "test@example.com"


# =============================================================================
# Tests for initialization parameters
# =============================================================================


class TestLocalIdentityAdapterInitialization:
    """Tests for LocalIdentityAdapter initialization."""

    def test_adapter_with_default_parameters(self) -> None:
        """LocalIdentityAdapter should work with default parameters."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        mock_repo = AsyncMock()

        adapter = LocalIdentityAdapter(user_repository=mock_repo)

        assert adapter._jwt_secret == "change-me-in-production"
        assert adapter._jwt_algorithm == "HS256"
        assert adapter._token_expiry_hours == 24

    def test_adapter_with_custom_parameters(self) -> None:
        """LocalIdentityAdapter should accept custom parameters."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        mock_repo = AsyncMock()

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="custom-secret",
            jwt_algorithm="HS512",
            token_expiry_hours=48,
        )

        assert adapter._jwt_secret == "custom-secret"
        assert adapter._jwt_algorithm == "HS512"
        assert adapter._token_expiry_hours == 48

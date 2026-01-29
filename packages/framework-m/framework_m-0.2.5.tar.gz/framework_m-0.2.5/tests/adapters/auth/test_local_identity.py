"""Tests for LocalIdentityAdapter.

TDD: This test file is created BEFORE the implementation.

Tests cover:
- IdentityProtocol implementation
- Password hashing with argon2
- Token generation
- User retrieval
"""

from unittest.mock import AsyncMock

import pytest

from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.identity import (
    PasswordCredentials,
    Token,
)

# =============================================================================
# Test: LocalIdentityAdapter Import
# =============================================================================


class TestLocalIdentityAdapterImport:
    """Tests for LocalIdentityAdapter import."""

    def test_import_local_identity_adapter(self) -> None:
        """LocalIdentityAdapter should be importable."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        assert LocalIdentityAdapter is not None

    def test_local_identity_adapter_in_auth_exports(self) -> None:
        """LocalIdentityAdapter should be in auth __all__."""
        from framework_m.adapters import auth

        assert "LocalIdentityAdapter" in auth.__all__


# =============================================================================
# Test: Password Hashing Utilities
# =============================================================================


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_import_hash_password(self) -> None:
        """hash_password should be importable."""
        from framework_m.adapters.auth.local_identity import hash_password

        assert hash_password is not None

    def test_import_verify_password(self) -> None:
        """verify_password should be importable."""
        from framework_m.adapters.auth.local_identity import verify_password

        assert verify_password is not None

    def test_hash_password_returns_string(self) -> None:
        """hash_password should return a string."""
        from framework_m.adapters.auth.local_identity import hash_password

        result = hash_password("secret123")
        assert isinstance(result, str)

    def test_hash_password_starts_with_argon2(self) -> None:
        """hash_password should return argon2 format."""
        from framework_m.adapters.auth.local_identity import hash_password

        result = hash_password("secret123")
        assert result.startswith("$argon2")

    def test_verify_password_correct(self) -> None:
        """verify_password should return True for correct password."""
        from framework_m.adapters.auth.local_identity import (
            hash_password,
            verify_password,
        )

        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """verify_password should return False for wrong password."""
        from framework_m.adapters.auth.local_identity import (
            hash_password,
            verify_password,
        )

        hashed = hash_password("secret123")
        assert verify_password("wrongpassword", hashed) is False


# =============================================================================
# Test: LocalIdentityAdapter Protocol Compliance
# =============================================================================


class TestLocalIdentityAdapterProtocol:
    """Tests for IdentityProtocol compliance."""

    def test_has_get_user_method(self) -> None:
        """LocalIdentityAdapter should have get_user method."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        assert hasattr(LocalIdentityAdapter, "get_user")

    def test_has_get_user_by_email_method(self) -> None:
        """LocalIdentityAdapter should have get_user_by_email method."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        assert hasattr(LocalIdentityAdapter, "get_user_by_email")

    def test_has_authenticate_method(self) -> None:
        """LocalIdentityAdapter should have authenticate method."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        assert hasattr(LocalIdentityAdapter, "authenticate")

    def test_has_get_attributes_method(self) -> None:
        """LocalIdentityAdapter should have get_attributes method."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        assert hasattr(LocalIdentityAdapter, "get_attributes")

    def test_has_validate_token_method(self) -> None:
        """LocalIdentityAdapter should have validate_token method."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        assert hasattr(LocalIdentityAdapter, "validate_token")


# =============================================================================
# Test: LocalIdentityAdapter.get_user
# =============================================================================


class TestLocalIdentityAdapterGetUser:
    """Tests for LocalIdentityAdapter.get_user method."""

    @pytest.mark.asyncio
    async def test_get_user_returns_user_context(self) -> None:
        """get_user should return UserContext for valid user."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter
        from framework_m.core.doctypes.user import LocalUser

        # Create mock repository
        mock_repo = AsyncMock()
        mock_user = LocalUser(
            email="test@example.com",
            password_hash="$argon2id$...",
            full_name="Test User",
        )
        mock_repo.get.return_value = mock_user

        adapter = LocalIdentityAdapter(user_repository=mock_repo)
        result = await adapter.get_user(str(mock_user.id))

        assert result is not None
        assert isinstance(result, UserContext)
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_returns_none_for_missing_user(self) -> None:
        """get_user should return None for non-existent user."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None

        adapter = LocalIdentityAdapter(user_repository=mock_repo)
        result = await adapter.get_user("non-existent-id")

        assert result is None


# =============================================================================
# Test: LocalIdentityAdapter.authenticate
# =============================================================================


class TestLocalIdentityAdapterAuthenticate:
    """Tests for LocalIdentityAdapter.authenticate method."""

    @pytest.mark.asyncio
    async def test_authenticate_returns_token(self) -> None:
        """authenticate should return Token for valid credentials."""
        from framework_m.adapters.auth.local_identity import (
            LocalIdentityAdapter,
            hash_password,
        )
        from framework_m.core.doctypes.user import LocalUser

        mock_repo = AsyncMock()
        password_hash = hash_password("secret123")
        mock_user = LocalUser(
            email="test@example.com",
            password_hash=password_hash,
            full_name="Test User",
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
        result = await adapter.authenticate(credentials)

        assert isinstance(result, Token)
        assert result.access_token is not None
        assert result.token_type == "Bearer"

    @pytest.mark.asyncio
    async def test_authenticate_raises_for_invalid_password(self) -> None:
        """authenticate should raise for wrong password."""
        from framework_m.adapters.auth.local_identity import (
            LocalIdentityAdapter,
            hash_password,
        )
        from framework_m.core.doctypes.user import LocalUser
        from framework_m.core.exceptions import AuthenticationError

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
        )

        credentials = PasswordCredentials(
            username="test@example.com",
            password="wrongpassword",
        )

        with pytest.raises(AuthenticationError):
            await adapter.authenticate(credentials)

    @pytest.mark.asyncio
    async def test_authenticate_raises_for_unknown_user(self) -> None:
        """authenticate should raise for non-existent user."""
        from framework_m.adapters.auth.local_identity import LocalIdentityAdapter
        from framework_m.core.exceptions import AuthenticationError

        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = None

        adapter = LocalIdentityAdapter(
            user_repository=mock_repo,
            jwt_secret="test-secret",
        )

        credentials = PasswordCredentials(
            username="unknown@example.com",
            password="secret123",
        )

        with pytest.raises(AuthenticationError):
            await adapter.authenticate(credentials)

"""Tests for UserManager service.

TDD: This test file is created BEFORE the implementation.

UserManager provides a high-level abstraction for user operations,
delegating to the configured IdentityProtocol implementation.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.identity import PasswordCredentials, Token

# =============================================================================
# Test: UserManager Import
# =============================================================================


class TestUserManagerImport:
    """Tests for UserManager import."""

    def test_import_user_manager(self) -> None:
        """UserManager should be importable."""
        from framework_m.core.services.user_manager import UserManager

        assert UserManager is not None

    def test_user_manager_in_services_exports(self) -> None:
        """UserManager should be in services __all__."""
        from framework_m.core.services import user_manager

        assert "UserManager" in user_manager.__all__


# =============================================================================
# Test: UserManager Initialization
# =============================================================================


class TestUserManagerInit:
    """Tests for UserManager initialization."""

    def test_create_user_manager_with_identity_provider(self) -> None:
        """UserManager should accept IdentityProtocol instance."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = MagicMock()
        manager = UserManager(identity_provider=mock_identity)

        assert manager._identity_provider is mock_identity

    def test_create_user_manager_with_optional_user_repo(self) -> None:
        """UserManager can optionally accept a user repository."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = MagicMock()
        mock_repo = MagicMock()
        manager = UserManager(
            identity_provider=mock_identity,
            user_repository=mock_repo,
        )

        assert manager._user_repository is mock_repo


# =============================================================================
# Test: UserManager.get
# =============================================================================


class TestUserManagerGet:
    """Tests for UserManager.get method."""

    @pytest.mark.asyncio
    async def test_get_delegates_to_identity_provider(self) -> None:
        """get() should delegate to identity_provider.get_user()."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = AsyncMock()
        mock_user = UserContext(id="user-123", email="test@example.com")
        mock_identity.get_user.return_value = mock_user

        manager = UserManager(identity_provider=mock_identity)
        result = await manager.get("user-123")

        mock_identity.get_user.assert_called_once_with("user-123")
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_user(self) -> None:
        """get() should return None for non-existent user."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = AsyncMock()
        mock_identity.get_user.return_value = None

        manager = UserManager(identity_provider=mock_identity)
        result = await manager.get("non-existent")

        assert result is None


# =============================================================================
# Test: UserManager.get_by_email
# =============================================================================


class TestUserManagerGetByEmail:
    """Tests for UserManager.get_by_email method."""

    @pytest.mark.asyncio
    async def test_get_by_email_delegates_to_identity_provider(self) -> None:
        """get_by_email() should delegate to identity_provider."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = AsyncMock()
        mock_user = UserContext(id="user-123", email="test@example.com")
        mock_identity.get_user_by_email.return_value = mock_user

        manager = UserManager(identity_provider=mock_identity)
        result = await manager.get_by_email("test@example.com")

        mock_identity.get_user_by_email.assert_called_once_with("test@example.com")
        assert result == mock_user


# =============================================================================
# Test: UserManager.authenticate
# =============================================================================


class TestUserManagerAuthenticate:
    """Tests for UserManager.authenticate method."""

    @pytest.mark.asyncio
    async def test_authenticate_delegates_to_identity_provider(self) -> None:
        """authenticate() should delegate to identity_provider."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = AsyncMock()
        mock_token = Token(access_token="test-token")
        mock_identity.authenticate.return_value = mock_token

        manager = UserManager(identity_provider=mock_identity)
        credentials = PasswordCredentials(
            username="user@example.com", password="secret"
        )
        result = await manager.authenticate(credentials)

        mock_identity.authenticate.assert_called_once_with(credentials)
        assert result == mock_token

    @pytest.mark.asyncio
    async def test_authenticate_raises_for_invalid_credentials(self) -> None:
        """authenticate() should propagate AuthenticationError."""
        from framework_m.core.exceptions import AuthenticationError
        from framework_m.core.services.user_manager import UserManager

        mock_identity = AsyncMock()
        mock_identity.authenticate.side_effect = AuthenticationError("Invalid")

        manager = UserManager(identity_provider=mock_identity)
        credentials = PasswordCredentials(username="user@example.com", password="wrong")

        with pytest.raises(AuthenticationError):
            await manager.authenticate(credentials)


# =============================================================================
# Test: UserManager.get_attributes
# =============================================================================


class TestUserManagerGetAttributes:
    """Tests for UserManager.get_attributes method."""

    @pytest.mark.asyncio
    async def test_get_attributes_delegates_to_identity_provider(self) -> None:
        """get_attributes() should delegate to identity_provider."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = AsyncMock()
        mock_attrs = {"roles": ["Admin"], "teams": ["Engineering"]}
        mock_identity.get_attributes.return_value = mock_attrs

        manager = UserManager(identity_provider=mock_identity)
        result = await manager.get_attributes("user-123")

        mock_identity.get_attributes.assert_called_once_with("user-123")
        assert result == mock_attrs


# =============================================================================
# Test: UserManager.validate_token
# =============================================================================


class TestUserManagerValidateToken:
    """Tests for UserManager.validate_token method."""

    @pytest.mark.asyncio
    async def test_validate_token_delegates_to_identity_provider(self) -> None:
        """validate_token() should delegate to identity_provider."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = AsyncMock()
        mock_user = UserContext(id="user-123", email="test@example.com")
        mock_identity.validate_token.return_value = mock_user

        manager = UserManager(identity_provider=mock_identity)
        result = await manager.validate_token("some-jwt-token")

        mock_identity.validate_token.assert_called_once_with("some-jwt-token")
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_validate_token_returns_none_for_invalid(self) -> None:
        """validate_token() should return None for invalid token."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = AsyncMock()
        mock_identity.validate_token.return_value = None

        manager = UserManager(identity_provider=mock_identity)
        result = await manager.validate_token("invalid-token")

        assert result is None


# =============================================================================
# Test: UserManager.create (Indie Mode)
# =============================================================================


class TestUserManagerCreate:
    """Tests for UserManager.create method (Indie mode only)."""

    @pytest.mark.asyncio
    async def test_create_requires_user_repository(self) -> None:
        """create() should raise if no user_repository configured."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = AsyncMock()
        manager = UserManager(identity_provider=mock_identity)

        with pytest.raises(RuntimeError, match="user_repository"):
            await manager.create(email="new@example.com", password="secret")

    @pytest.mark.asyncio
    async def test_create_hashes_password_and_saves(self) -> None:
        """create() should hash password and save via repository."""
        from framework_m.core.services.user_manager import UserManager

        mock_identity = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.save.return_value = MagicMock(
            id="new-user-id",
            email="new@example.com",
        )

        manager = UserManager(
            identity_provider=mock_identity,
            user_repository=mock_repo,
        )

        await manager.create(
            email="new@example.com",
            password="secret123",
            full_name="New User",
        )

        # Verify save was called
        mock_repo.save.assert_called_once()
        saved_user = mock_repo.save.call_args[0][0]
        assert saved_user.email == "new@example.com"
        assert saved_user.full_name == "New User"
        # Password should be hashed
        assert saved_user.password_hash.startswith("$argon2")

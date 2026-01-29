"""Tests for User DocTypes (LocalUser).

TDD: This test file is created BEFORE the implementation.

Tests cover:
- LocalUser model creation and validation
- Password hash exclusion from serialization
- Meta configuration (api_resource=False, apply_rls=False)
- Field validation
"""

import pytest
from pydantic import ValidationError

# =============================================================================
# Test: LocalUser Import
# =============================================================================


class TestLocalUserImport:
    """Tests for LocalUser DocType import."""

    def test_import_local_user(self) -> None:
        """LocalUser should be importable from doctypes."""
        from framework_m.core.doctypes.user import LocalUser

        assert LocalUser is not None

    def test_local_user_in_all_exports(self) -> None:
        """LocalUser should be in __all__."""
        from framework_m.core.doctypes import user

        assert "LocalUser" in user.__all__


# =============================================================================
# Test: LocalUser Creation
# =============================================================================


class TestLocalUserCreation:
    """Tests for LocalUser DocType creation."""

    def test_create_local_user_with_required_fields(self) -> None:
        """LocalUser should be creatable with required fields."""
        from framework_m.core.doctypes.user import LocalUser

        user = LocalUser(
            email="test@example.com",
            password_hash="$argon2id$...",
        )

        assert user.email == "test@example.com"
        assert user.password_hash == "$argon2id$..."

    def test_local_user_with_full_name(self) -> None:
        """LocalUser should accept full_name."""
        from framework_m.core.doctypes.user import LocalUser

        user = LocalUser(
            email="test@example.com",
            password_hash="$argon2id$...",
            full_name="John Doe",
        )

        assert user.full_name == "John Doe"

    def test_local_user_default_is_active_true(self) -> None:
        """LocalUser.is_active should default to True."""
        from framework_m.core.doctypes.user import LocalUser

        user = LocalUser(
            email="test@example.com",
            password_hash="$argon2id$...",
        )

        assert user.is_active is True

    def test_local_user_inherits_from_base_doctype(self) -> None:
        """LocalUser should inherit from BaseDocType."""
        from framework_m.core.doctypes.user import LocalUser
        from framework_m.core.domain.base_doctype import BaseDocType

        assert issubclass(LocalUser, BaseDocType)

    def test_local_user_has_uuid_id(self) -> None:
        """LocalUser should have auto-generated UUID id."""
        from uuid import UUID

        from framework_m.core.doctypes.user import LocalUser

        user = LocalUser(
            email="test@example.com",
            password_hash="$argon2id$...",
        )

        assert isinstance(user.id, UUID)


# =============================================================================
# Test: LocalUser Validation
# =============================================================================


class TestLocalUserValidation:
    """Tests for LocalUser field validation."""

    def test_local_user_requires_email(self) -> None:
        """LocalUser must have email."""
        from framework_m.core.doctypes.user import LocalUser

        with pytest.raises(ValidationError):
            LocalUser(password_hash="$argon2id$...")  # type: ignore[call-arg]

    def test_local_user_requires_password_hash(self) -> None:
        """LocalUser must have password_hash."""
        from framework_m.core.doctypes.user import LocalUser

        with pytest.raises(ValidationError):
            LocalUser(email="test@example.com")  # type: ignore[call-arg]


# =============================================================================
# Test: LocalUser Serialization (Security)
# =============================================================================


class TestLocalUserSerialization:
    """Tests for LocalUser serialization security."""

    def test_password_hash_excluded_from_model_dump(self) -> None:
        """password_hash should be excluded from model_dump()."""
        from framework_m.core.doctypes.user import LocalUser

        user = LocalUser(
            email="test@example.com",
            password_hash="$argon2id$secret",
            full_name="John Doe",
        )

        data = user.model_dump()

        assert "password_hash" not in data
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "John Doe"

    def test_password_hash_excluded_from_model_dump_json(self) -> None:
        """password_hash should be excluded from model_dump_json()."""
        from framework_m.core.doctypes.user import LocalUser

        user = LocalUser(
            email="test@example.com",
            password_hash="$argon2id$secret",
        )

        json_str = user.model_dump_json()

        assert "password_hash" not in json_str
        assert "$argon2id$secret" not in json_str


# =============================================================================
# Test: LocalUser Meta Configuration
# =============================================================================


class TestLocalUserMeta:
    """Tests for LocalUser Meta configuration."""

    def test_local_user_api_resource_false(self) -> None:
        """LocalUser should have api_resource=False (auth API handles users)."""
        from framework_m.core.doctypes.user import LocalUser

        assert LocalUser.get_api_resource() is False

    def test_local_user_apply_rls_false(self) -> None:
        """LocalUser should have apply_rls=False (users are system-wide)."""
        from framework_m.core.doctypes.user import LocalUser

        assert LocalUser.get_apply_rls() is False

    def test_local_user_requires_auth_true(self) -> None:
        """LocalUser should require auth by default."""
        from framework_m.core.doctypes.user import LocalUser

        assert LocalUser.get_requires_auth() is True


# =============================================================================
# Test: UserPreferences DocType
# =============================================================================


class TestUserPreferencesImport:
    """Tests for UserPreferences DocType import."""

    def test_import_user_preferences(self) -> None:
        """UserPreferences should be importable from doctypes."""
        from framework_m.core.doctypes.user import UserPreferences

        assert UserPreferences is not None

    def test_user_preferences_in_all_exports(self) -> None:
        """UserPreferences should be in __all__."""
        from framework_m.core.doctypes import user

        assert "UserPreferences" in user.__all__


class TestUserPreferencesCreation:
    """Tests for UserPreferences DocType creation."""

    def test_create_user_preferences(self) -> None:
        """UserPreferences should be creatable with user_id."""
        from framework_m.core.doctypes.user import UserPreferences

        prefs = UserPreferences(user_id="user-123")

        assert prefs.user_id == "user-123"

    def test_user_preferences_default_settings(self) -> None:
        """UserPreferences should have default settings dict."""
        from framework_m.core.doctypes.user import UserPreferences

        prefs = UserPreferences(user_id="user-123")

        assert prefs.settings == {}

    def test_user_preferences_with_custom_settings(self) -> None:
        """UserPreferences should accept custom settings."""
        from framework_m.core.doctypes.user import UserPreferences

        prefs = UserPreferences(
            user_id="user-123",
            settings={"theme": "dark", "language": "en"},
        )

        assert prefs.settings["theme"] == "dark"
        assert prefs.settings["language"] == "en"

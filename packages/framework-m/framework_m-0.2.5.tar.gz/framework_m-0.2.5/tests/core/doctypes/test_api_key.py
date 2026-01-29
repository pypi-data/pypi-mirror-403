"""Tests for ApiKey DocType.

TDD: This test file is created BEFORE the implementation.
"""


# =============================================================================
# Test: ApiKey Import
# =============================================================================


class TestApiKeyImport:
    """Tests for ApiKey DocType import."""

    def test_import_api_key(self) -> None:
        """ApiKey should be importable from doctypes."""
        from framework_m.core.doctypes.api_key import ApiKey

        assert ApiKey is not None

    def test_api_key_in_all_exports(self) -> None:
        """ApiKey should be in __all__."""
        from framework_m.core.doctypes import api_key

        assert "ApiKey" in api_key.__all__


# =============================================================================
# Test: ApiKey Creation
# =============================================================================


class TestApiKeyCreation:
    """Tests for ApiKey DocType creation."""

    def test_create_api_key_with_required_fields(self) -> None:
        """ApiKey should be creatable with required fields."""
        from framework_m.core.doctypes.api_key import ApiKey

        key = ApiKey(
            key_hash="$argon2id$...",
            user_id="user-123",
            name="Production API Key",
        )

        assert key.key_hash == "$argon2id$..."
        assert key.user_id == "user-123"
        assert key.name == "Production API Key"

    def test_api_key_inherits_from_base_doctype(self) -> None:
        """ApiKey should inherit from BaseDocType."""
        from framework_m.core.doctypes.api_key import ApiKey
        from framework_m.core.domain.base_doctype import BaseDocType

        assert issubclass(ApiKey, BaseDocType)


# =============================================================================
# Test: ApiKey Fields
# =============================================================================


class TestApiKeyFields:
    """Tests for ApiKey field defaults and validation."""

    def test_scopes_default_empty(self) -> None:
        """scopes should default to empty list."""
        from framework_m.core.doctypes.api_key import ApiKey

        key = ApiKey(
            key_hash="$argon2id$...",
            user_id="user-123",
            name="Test Key",
        )

        assert key.scopes == []

    def test_expires_at_optional(self) -> None:
        """expires_at should be optional."""
        from framework_m.core.doctypes.api_key import ApiKey

        key = ApiKey(
            key_hash="$argon2id$...",
            user_id="user-123",
            name="Test Key",
        )

        assert key.expires_at is None

    def test_last_used_at_optional(self) -> None:
        """last_used_at should be optional."""
        from framework_m.core.doctypes.api_key import ApiKey

        key = ApiKey(
            key_hash="$argon2id$...",
            user_id="user-123",
            name="Test Key",
        )

        assert key.last_used_at is None


# =============================================================================
# Test: ApiKey Serialization
# =============================================================================


class TestApiKeySerialization:
    """Tests for ApiKey serialization security."""

    def test_key_hash_excluded_from_model_dump(self) -> None:
        """key_hash should be excluded from model_dump()."""
        from framework_m.core.doctypes.api_key import ApiKey

        key = ApiKey(
            key_hash="$argon2id$secret",
            user_id="user-123",
            name="Test Key",
        )

        data = key.model_dump()

        assert "key_hash" not in data
        assert data["name"] == "Test Key"

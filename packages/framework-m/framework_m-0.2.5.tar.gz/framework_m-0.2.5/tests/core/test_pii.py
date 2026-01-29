"""Tests for PII Handling.

Tests cover:
- AuthMode enum and configuration
- PII field detection
- Deletion mode configuration
"""

from unittest.mock import patch

# =============================================================================
# Test: AuthMode Import
# =============================================================================


class TestAuthModeImport:
    """Tests for AuthMode import."""

    def test_import_auth_mode(self) -> None:
        """AuthMode should be importable."""
        from framework_m.core.pii import AuthMode

        assert AuthMode is not None

    def test_import_get_auth_mode(self) -> None:
        """get_auth_mode should be importable."""
        from framework_m.core.pii import get_auth_mode

        assert get_auth_mode is not None


class TestAuthModeEnum:
    """Tests for AuthMode enum values."""

    def test_auth_mode_values(self) -> None:
        """AuthMode should have expected values."""
        from framework_m.core.pii import AuthMode

        assert AuthMode.SOCIAL_ONLY.value == "social_only"
        assert AuthMode.PASSWORDLESS.value == "passwordless"
        assert AuthMode.LOCAL.value == "local"
        assert AuthMode.FEDERATED.value == "federated"


class TestGetAuthMode:
    """Tests for get_auth_mode function."""

    def test_default_auth_mode(self) -> None:
        """get_auth_mode should default to social_only."""
        from framework_m.core.pii import AuthMode, get_auth_mode

        with patch("framework_m.core.pii.load_config", return_value={}):
            mode = get_auth_mode()

        assert mode == AuthMode.SOCIAL_ONLY

    def test_auth_mode_from_config(self) -> None:
        """get_auth_mode should read from config."""
        from framework_m.core.pii import AuthMode, get_auth_mode

        config = {"auth": {"mode": "local"}}
        with patch("framework_m.core.pii.load_config", return_value=config):
            mode = get_auth_mode()

        assert mode == AuthMode.LOCAL

    def test_invalid_auth_mode_defaults_safely(self) -> None:
        """get_auth_mode should default to social_only for invalid values."""
        from framework_m.core.pii import AuthMode, get_auth_mode

        config = {"auth": {"mode": "invalid_mode"}}
        with patch("framework_m.core.pii.load_config", return_value=config):
            mode = get_auth_mode()

        assert mode == AuthMode.SOCIAL_ONLY


# =============================================================================
# Test: Password and PII Requirements
# =============================================================================


class TestPasswordRequirement:
    """Tests for requires_password function."""

    def test_import_requires_password(self) -> None:
        """requires_password should be importable."""
        from framework_m.core.pii import requires_password

        assert requires_password is not None

    def test_local_mode_requires_password(self) -> None:
        """LOCAL mode should require password."""
        from framework_m.core.pii import requires_password

        config = {"auth": {"mode": "local"}}
        with patch("framework_m.core.pii.load_config", return_value=config):
            assert requires_password() is True

    def test_social_only_no_password(self) -> None:
        """SOCIAL_ONLY mode should not require password."""
        from framework_m.core.pii import requires_password

        config = {"auth": {"mode": "social_only"}}
        with patch("framework_m.core.pii.load_config", return_value=config):
            assert requires_password() is False


class TestStoresLocalPii:
    """Tests for stores_local_pii function."""

    def test_import_stores_local_pii(self) -> None:
        """stores_local_pii should be importable."""
        from framework_m.core.pii import stores_local_pii

        assert stores_local_pii is not None

    def test_federated_no_local_pii(self) -> None:
        """FEDERATED mode should not store local PII."""
        from framework_m.core.pii import stores_local_pii

        config = {"auth": {"mode": "federated"}}
        with patch("framework_m.core.pii.load_config", return_value=config):
            assert stores_local_pii() is False


# =============================================================================
# Test: Sensitive PII Detection
# =============================================================================


class TestSensitivePiiDetection:
    """Tests for PII field detection."""

    def test_import_is_sensitive_pii(self) -> None:
        """is_sensitive_pii should be importable."""
        from framework_m.core.pii import is_sensitive_pii

        assert is_sensitive_pii is not None

    def test_phone_number_is_sensitive(self) -> None:
        """phone_number should be detected as sensitive."""
        from framework_m.core.pii import is_sensitive_pii

        assert is_sensitive_pii("phone_number") is True

    def test_date_of_birth_is_sensitive(self) -> None:
        """date_of_birth should be detected as sensitive."""
        from framework_m.core.pii import is_sensitive_pii

        assert is_sensitive_pii("date_of_birth") is True

    def test_email_is_not_sensitive(self) -> None:
        """email should NOT be detected as sensitive (minimal PII)."""
        from framework_m.core.pii import is_sensitive_pii

        assert is_sensitive_pii("email") is False


# =============================================================================
# Test: Deletion Mode
# =============================================================================


class TestDeletionMode:
    """Tests for DeletionMode configuration."""

    def test_import_deletion_mode(self) -> None:
        """DeletionMode should be importable."""
        from framework_m.core.pii import DeletionMode

        assert DeletionMode is not None

    def test_import_get_deletion_mode(self) -> None:
        """get_deletion_mode should be importable."""
        from framework_m.core.pii import get_deletion_mode

        assert get_deletion_mode is not None

    def test_default_deletion_mode(self) -> None:
        """Default deletion mode should be hard_delete."""
        from framework_m.core.pii import DeletionMode, get_deletion_mode

        with patch("framework_m.core.pii.load_config", return_value={}):
            mode = get_deletion_mode()

        assert mode == DeletionMode.HARD_DELETE

    def test_anonymize_mode_from_config(self) -> None:
        """get_deletion_mode should read anonymize from config."""
        from framework_m.core.pii import DeletionMode, get_deletion_mode

        config = {"auth": {"deletion": {"mode": "anonymize"}}}
        with patch("framework_m.core.pii.load_config", return_value=config):
            mode = get_deletion_mode()

        assert mode == DeletionMode.ANONYMIZE

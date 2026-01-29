"""Tests for SystemSettings DocType.

Tests cover:
- SystemSettings model creation
- Field validation
- Meta configuration
"""

import pytest

from framework_m.core.doctypes.system_settings import SystemSettings

# =============================================================================
# Test: Import
# =============================================================================


class TestSystemSettingsImport:
    """Tests for SystemSettings import."""

    def test_import_system_settings(self) -> None:
        """SystemSettings should be importable."""
        from framework_m.core.doctypes.system_settings import SystemSettings

        assert SystemSettings is not None


# =============================================================================
# Test: Model Creation
# =============================================================================


class TestSystemSettingsCreation:
    """Tests for SystemSettings model creation."""

    def test_create_with_defaults(self) -> None:
        """SystemSettings should work with all defaults."""
        settings = SystemSettings()

        assert settings.name == "System Settings"
        assert settings.app_name == "Framework M"
        assert settings.timezone == "UTC"
        assert settings.language == "en"

    def test_create_with_custom_values(self) -> None:
        """SystemSettings should accept custom values."""
        settings = SystemSettings(
            app_name="My App",
            timezone="America/New_York",
            language="es",
        )

        assert settings.app_name == "My App"
        assert settings.timezone == "America/New_York"
        assert settings.language == "es"

    def test_default_formats(self) -> None:
        """SystemSettings should have default date/time formats."""
        settings = SystemSettings()

        assert settings.date_format == "YYYY-MM-DD"
        assert settings.time_format == "HH:mm:ss"

    def test_default_feature_flags(self) -> None:
        """SystemSettings should have default feature flags."""
        settings = SystemSettings()

        assert settings.enable_signup is True
        assert settings.maintenance_mode is False

    def test_default_session_expiry(self) -> None:
        """SystemSettings should default to 24h session expiry."""
        settings = SystemSettings()

        assert settings.session_expiry == 1440  # 24 hours


# =============================================================================
# Test: Validation
# =============================================================================


class TestSystemSettingsValidation:
    """Tests for field validation."""

    def test_language_min_length(self) -> None:
        """language should have min length 2."""
        with pytest.raises(ValueError):
            SystemSettings(language="e")

    def test_language_max_length(self) -> None:
        """language should have max length 10."""
        with pytest.raises(ValueError):
            SystemSettings(language="x" * 15)

    def test_session_expiry_min(self) -> None:
        """session_expiry should be at least 1."""
        with pytest.raises(ValueError):
            SystemSettings(session_expiry=0)

    def test_session_expiry_max(self) -> None:
        """session_expiry should be at most 1 year."""
        with pytest.raises(ValueError):
            SystemSettings(session_expiry=1000000)


# =============================================================================
# Test: Meta Configuration
# =============================================================================


class TestSystemSettingsMeta:
    """Tests for Meta class configuration."""

    def test_meta_table_name(self) -> None:
        """Meta should have correct table_name."""
        assert SystemSettings.Meta.table_name == "system_settings"

    def test_meta_requires_auth(self) -> None:
        """Meta should require authentication."""
        assert SystemSettings.Meta.requires_auth is True

    def test_meta_no_rls(self) -> None:
        """Meta should not apply RLS (singleton)."""
        assert SystemSettings.Meta.apply_rls is False

    def test_meta_is_singleton(self) -> None:
        """Meta should mark as singleton."""
        assert SystemSettings.Meta.is_singleton is True

    def test_meta_all_can_read(self) -> None:
        """Meta should allow all to read."""
        assert "All" in SystemSettings.Meta.permissions["read"]

    def test_meta_admin_only_write(self) -> None:
        """Meta should allow only admins to write."""
        assert "System Manager" in SystemSettings.Meta.permissions["write"]

    def test_meta_no_delete(self) -> None:
        """Meta should not allow deletion."""
        assert SystemSettings.Meta.permissions["delete"] == []

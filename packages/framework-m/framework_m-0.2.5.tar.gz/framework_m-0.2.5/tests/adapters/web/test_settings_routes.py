"""Tests for Settings API Routes.

Tests cover:
- SettingsController endpoint presence
- SettingsResponse model
- Cache functions
"""

from framework_m.adapters.web.settings_routes import (
    SettingsController,
    SettingsResponse,
    invalidate_settings_cache,
    set_settings_cache,
)
from framework_m.core.doctypes.system_settings import SystemSettings

# =============================================================================
# Test: Import
# =============================================================================


class TestSettingsRoutesImport:
    """Tests for Settings routes import."""

    def test_import_settings_controller(self) -> None:
        """SettingsController should be importable."""
        from framework_m.adapters.web.settings_routes import SettingsController

        assert SettingsController is not None

    def test_import_settings_response(self) -> None:
        """SettingsResponse should be importable."""
        from framework_m.adapters.web.settings_routes import SettingsResponse

        assert SettingsResponse is not None


# =============================================================================
# Test: SettingsController
# =============================================================================


class TestSettingsController:
    """Tests for SettingsController."""

    def test_controller_path(self) -> None:
        """Controller should have correct path."""
        assert SettingsController.path == "/api/v1/settings"

    def test_controller_tags(self) -> None:
        """Controller should have Settings tag."""
        assert "Settings" in SettingsController.tags

    def test_controller_has_get_settings(self) -> None:
        """Controller should have get_settings method."""
        assert hasattr(SettingsController, "get_settings")


# =============================================================================
# Test: SettingsResponse
# =============================================================================


class TestSettingsResponse:
    """Tests for SettingsResponse model."""

    def test_create_from_settings(self) -> None:
        """from_settings should convert SystemSettings."""
        settings = SystemSettings(
            app_name="Test App",
            timezone="America/New_York",
            language="es",
        )

        response = SettingsResponse.from_settings(settings)

        assert response.app_name == "Test App"
        assert response.timezone == "America/New_York"
        assert response.language == "es"

    def test_includes_expected_fields(self) -> None:
        """Response should include all expected fields."""
        settings = SystemSettings()
        response = SettingsResponse.from_settings(settings)

        assert hasattr(response, "app_name")
        assert hasattr(response, "timezone")
        assert hasattr(response, "date_format")
        assert hasattr(response, "time_format")
        assert hasattr(response, "language")
        assert hasattr(response, "enable_signup")
        assert hasattr(response, "maintenance_mode")


# =============================================================================
# Test: Cache Functions
# =============================================================================


class TestCacheFunctions:
    """Tests for cache utility functions."""

    def test_invalidate_cache(self) -> None:
        """invalidate_settings_cache should be callable."""
        # Should not raise
        invalidate_settings_cache()

    def test_set_cache(self) -> None:
        """set_settings_cache should accept SystemSettings."""
        settings = SystemSettings()
        # Should not raise
        set_settings_cache(settings)

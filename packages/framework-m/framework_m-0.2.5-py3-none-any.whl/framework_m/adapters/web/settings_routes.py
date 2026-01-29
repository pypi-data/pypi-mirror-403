"""Settings API Routes - System settings endpoint.

This module provides REST API endpoints for accessing system settings:
- GET /api/v1/settings - Return system settings (cached)

Settings are read-only via API. Use Admin UI or CLI for modifications.

Example:
    GET /api/v1/settings
    {
        "app_name": "Framework M",
        "timezone": "UTC",
        "language": "en",
        ...
    }
"""

from __future__ import annotations

from typing import Any

from litestar import Controller, Response, get
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel, Field

from framework_m.core.doctypes.system_settings import SystemSettings

# =============================================================================
# Response Models
# =============================================================================


class SettingsResponse(BaseModel):
    """System settings response.

    Contains all publicly accessible system settings.
    Sensitive settings are excluded.
    """

    app_name: str = Field(description="Application display name")
    timezone: str = Field(description="Default timezone")
    date_format: str = Field(description="Date format string")
    time_format: str = Field(description="Time format string")
    language: str = Field(description="Default language code")
    enable_signup: bool = Field(description="User registration enabled")
    maintenance_mode: bool = Field(description="Application in maintenance mode")

    @classmethod
    def from_settings(cls, settings: SystemSettings) -> SettingsResponse:
        """Create from SystemSettings DocType."""
        return cls(
            app_name=settings.app_name,
            timezone=settings.timezone,
            date_format=settings.date_format,
            time_format=settings.time_format,
            language=settings.language,
            enable_signup=settings.enable_signup,
            maintenance_mode=settings.maintenance_mode,
        )


# =============================================================================
# Settings Controller
# =============================================================================


# Module-level cache for settings
_settings_cache: SystemSettings | None = None


class SettingsController(Controller):
    """Settings API controller.

    Provides endpoints for accessing system settings.
    Settings are cached aggressively to minimize database queries.

    Attributes:
        path: Base path for all endpoints
        tags: OpenAPI tags for documentation
    """

    path = "/api/v1/settings"
    tags = ["Settings"]  # noqa: RUF012

    @get("/")
    async def get_settings(self) -> Response[Any]:
        """Get system settings.

        Returns the current system settings. Settings are cached
        and refreshed periodically or on updates.

        Returns:
            SettingsResponse with current settings
        """
        global _settings_cache

        # TODO: Load from repository with caching
        # For now, return defaults or cached value
        if _settings_cache is None:
            _settings_cache = SystemSettings()

        response = SettingsResponse.from_settings(_settings_cache)

        return Response(
            content=response.model_dump_json(),
            status_code=HTTP_200_OK,
            media_type="application/json",
            headers={
                "Cache-Control": "public, max-age=300",  # Cache for 5 minutes
            },
        )


def invalidate_settings_cache() -> None:
    """Invalidate the settings cache.

    Call this after updating settings to force a refresh.
    """
    global _settings_cache
    _settings_cache = None


def set_settings_cache(settings: SystemSettings) -> None:
    """Set the settings cache.

    Used by the settings update flow to avoid refetch.
    """
    global _settings_cache
    _settings_cache = settings


__all__ = [
    "SettingsController",
    "SettingsResponse",
    "invalidate_settings_cache",
    "set_settings_cache",
]

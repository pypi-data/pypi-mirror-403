"""SystemSettings DocType - Application configuration singleton.

This module defines the SystemSettings DocType for Framework M.

SystemSettings is a singleton pattern - only one record exists for the
entire application, always named "System Settings". It stores global
configuration that affects the entire application.

Security:
- Only admins can modify settings
- All authenticated users can read settings
- Settings are cached aggressively

Example:
    settings = await repository.get("SystemSettings", "System Settings")
    print(settings.timezone)  # "UTC"
"""

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class SystemSettings(BaseDocType):
    """System settings singleton DocType.

    Stores global application configuration. Only one instance exists.

    Attributes:
        name: Always "System Settings"
        app_name: Application display name
        timezone: Default timezone (e.g., "UTC", "America/New_York")
        date_format: Date format string (e.g., "YYYY-MM-DD")
        time_format: Time format string (e.g., "HH:mm:ss")
        language: Default language code (e.g., "en")
        enable_signup: Allow new user registration
        session_expiry: Session timeout in minutes
        maintenance_mode: If True, only admins can access

    Example:
        settings = SystemSettings(
            app_name="My App",
            timezone="America/New_York",
        )
    """

    # Name is always "System Settings"
    name: str = Field(
        default="System Settings",
        description="Always 'System Settings'",
        frozen=True,  # Cannot be changed
    )

    # Application identity
    app_name: str = Field(
        default="Framework M",
        description="Application display name",
        max_length=255,
    )

    # Locale settings
    timezone: str = Field(
        default="UTC",
        description="Default timezone (e.g., UTC, America/New_York)",
    )

    date_format: str = Field(
        default="YYYY-MM-DD",
        description="Date format (e.g., YYYY-MM-DD, DD/MM/YYYY)",
    )

    time_format: str = Field(
        default="HH:mm:ss",
        description="Time format (e.g., HH:mm:ss, hh:mm A)",
    )

    language: str = Field(
        default="en",
        description="Default language code (e.g., en, es, fr)",
        min_length=2,
        max_length=10,
    )

    # Feature flags
    enable_signup: bool = Field(
        default=True,
        description="Allow new user registration",
    )

    session_expiry: int = Field(
        default=1440,  # 24 hours in minutes
        description="Session timeout in minutes",
        ge=1,
        le=525600,  # 1 year max
    )

    maintenance_mode: bool = Field(
        default=False,
        description="If True, only admins can access the application",
    )

    class Meta:
        """DocType metadata."""

        table_name = "system_settings"
        requires_auth = True
        apply_rls = False  # Singleton, no RLS needed
        is_singleton = True  # Only one record allowed

        # Permissions - admins manage, all authenticated can read
        permissions = {  # noqa: RUF012
            "read": ["All"],
            "write": ["System Manager"],
            "create": ["System Manager"],
            "delete": [],  # Cannot delete system settings
        }


__all__ = ["SystemSettings"]

"""PII Handling - Auth modes and data privacy utilities.

This module provides PII (Personally Identifiable Information) handling
utilities for Framework M, following GDPR best practices.

Auth Modes:
- social_only: OAuth only, no local passwords (minimal PII)
- passwordless: Magic link email only
- local: Traditional username/password
- federated: External IdP, zero local PII

Configuration in framework_config.toml:
    [auth]
    mode = "social_only"  # or "passwordless", "local", "federated"

Example:
    from framework_m.core.pii import get_auth_mode, PIIExporter

    mode = get_auth_mode()  # Returns "social_only", "local", etc.
    exporter = PIIExporter(user_id="user-001")
    data = await exporter.export_all()  # GDPR data export
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from framework_m.cli.config import load_config

# =============================================================================
# Auth Mode Enum
# =============================================================================


class AuthMode(str, Enum):
    """Available authentication modes.

    Attributes:
        SOCIAL_ONLY: OAuth only, no local passwords (minimal PII)
        PASSWORDLESS: Email magic links only
        LOCAL: Traditional username/password
        FEDERATED: External IdP, zero local PII
    """

    SOCIAL_ONLY = "social_only"
    PASSWORDLESS = "passwordless"
    LOCAL = "local"
    FEDERATED = "federated"


def get_auth_mode() -> AuthMode:
    """Get the configured authentication mode.

    Reads from framework_config.toml:
        [auth]
        mode = "social_only"

    Returns:
        AuthMode enum value (defaults to SOCIAL_ONLY for minimal PII)
    """
    config = load_config()
    auth_config = config.get("auth", {})
    mode_str = auth_config.get("mode", "social_only")

    try:
        return AuthMode(mode_str)
    except ValueError:
        # Invalid mode, default to safest option
        return AuthMode.SOCIAL_ONLY


def requires_password() -> bool:
    """Check if current auth mode requires password storage.

    Returns:
        True only if mode is LOCAL
    """
    return get_auth_mode() == AuthMode.LOCAL


def stores_local_pii() -> bool:
    """Check if current auth mode stores PII locally.

    Returns:
        True for LOCAL and PASSWORDLESS modes
        False for SOCIAL_ONLY and FEDERATED (minimal/zero PII)
    """
    mode = get_auth_mode()
    return mode in (AuthMode.LOCAL, AuthMode.PASSWORDLESS)


# =============================================================================
# PII Field Configuration
# =============================================================================


# Fields that should NOT be stored by default (GDPR best practice)
PII_SENSITIVE_FIELDS = frozenset(
    [
        "full_legal_name",
        "phone_number",
        "address",
        "street_address",
        "city",
        "postal_code",
        "country",
        "date_of_birth",
        "national_id",
        "social_security_number",
        "passport_number",
        "drivers_license",
    ]
)

# Minimal PII fields (acceptable to store)
PII_MINIMAL_FIELDS = frozenset(
    [
        "email",
        "display_name",
        "avatar_url",
    ]
)


def is_sensitive_pii(field_name: str) -> bool:
    """Check if a field name is considered sensitive PII.

    Args:
        field_name: Field name to check

    Returns:
        True if field is sensitive PII that should not be stored by default
    """
    return field_name.lower() in PII_SENSITIVE_FIELDS


# =============================================================================
# Data Deletion Configuration
# =============================================================================


class DeletionMode(str, Enum):
    """How to handle user data on account deletion.

    Attributes:
        HARD_DELETE: Permanently remove all data
        ANONYMIZE: Replace PII with anonymous values, keep records
    """

    HARD_DELETE = "hard_delete"
    ANONYMIZE = "anonymize"


def get_deletion_mode() -> DeletionMode:
    """Get the configured data deletion mode.

    Reads from framework_config.toml:
        [auth.deletion]
        mode = "hard_delete"  # or "anonymize"

    Returns:
        DeletionMode enum value (defaults to HARD_DELETE for GDPR compliance)
    """
    config = load_config()
    auth_config = config.get("auth", {})
    deletion_config = auth_config.get("deletion", {})
    mode_str = deletion_config.get("mode", "hard_delete")

    try:
        return DeletionMode(mode_str)
    except ValueError:
        return DeletionMode.HARD_DELETE


# =============================================================================
# PII Export Model (GDPR Data Portability)
# =============================================================================


class PIIExportData(BaseModel):
    """Data structure for GDPR data export.

    Contains all user data in portable format.

    Attributes:
        user: Core user information
        preferences: User preferences/settings
        sessions: Active sessions
        api_keys: API key metadata (not secrets)
        social_accounts: Linked social accounts
    """

    user: dict[str, Any] = Field(description="Core user data")
    preferences: dict[str, Any] = Field(default_factory=dict)
    sessions: list[dict[str, Any]] = Field(default_factory=list)
    api_keys: list[dict[str, Any]] = Field(default_factory=list)
    social_accounts: list[dict[str, Any]] = Field(default_factory=list)
    exported_at: str = Field(description="ISO timestamp of export")


__all__ = [
    "PII_MINIMAL_FIELDS",
    "PII_SENSITIVE_FIELDS",
    "AuthMode",
    "DeletionMode",
    "PIIExportData",
    "get_auth_mode",
    "get_deletion_mode",
    "is_sensitive_pii",
    "requires_password",
    "stores_local_pii",
]

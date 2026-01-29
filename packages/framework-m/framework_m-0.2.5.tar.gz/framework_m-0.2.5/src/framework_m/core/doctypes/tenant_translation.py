"""TenantTranslation DocType - Per-tenant translation overrides.

This module defines the TenantTranslation DocType which allows tenants
to override system translations with their own custom translations.

Use cases:
- Tenant-specific terminology (e.g., "Customer" vs "Client")
- Industry-specific language (e.g., medical vs retail)
- Brand-specific wording (e.g., company name in greetings)

Translation priority:
1. TenantTranslation (tenant-specific override)
2. Translation (system-wide translation)
3. Source text (fallback)

Example:
    # System translation
    Translation(
        source_text="Customer",
        translated_text="ग्राहक",
        locale="hi",
        context="field_label"
    )

    # Tenant override (uses "Client" instead)
    TenantTranslation(
        tenant_id="acme-corp",
        source_text="Customer",
        translated_text="क्लाइंट",
        locale="hi",
        context="field_label"
    )
"""

from typing import ClassVar

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class TenantTranslation(BaseDocType):
    """Tenant-specific translation overrides.

    Allows tenants to customize translations to match their terminology,
    industry, or brand voice. Overrides system translations when present.

    Attributes:
        tenant_id: Tenant identifier (from TenantContext)
        source_text: Original text to translate (1-1000 characters)
        translated_text: Translated text in target locale (1-1000 characters)
        locale: Locale code (e.g., "en", "hi", "ta", "es_MX")
        context: Optional context for disambiguation (e.g., "button", "field_label")

    Constraints:
        - Unique combination of (tenant_id, source_text, locale, context)
        - locale must match pattern: 2 lowercase letters, optionally followed by
          underscore and 2 uppercase letters (e.g., "en", "en_US", "pt_BR")

    Example:
        # Healthcare tenant uses "Patient" instead of "Customer"
        TenantTranslation(
            tenant_id="healthcare-corp",
            source_text="Customer",
            translated_text="Patient",
            locale="en",
            context="field_label"
        )

        # Retail tenant uses "Client" in French
        TenantTranslation(
            tenant_id="retail-corp",
            source_text="Customer",
            translated_text="Client",
            locale="fr",
            context="field_label"
        )
    """

    tenant_id: str = Field(
        description="Tenant identifier from TenantContext",
        min_length=1,
        max_length=100,
    )

    source_text: str = Field(
        description="Original text to translate",
        min_length=1,
        max_length=1000,
    )

    translated_text: str = Field(
        description="Translated text in target locale",
        min_length=1,
        max_length=1000,
    )

    locale: str = Field(
        description="Locale code (e.g., 'en', 'hi', 'ta', 'es_MX')",
        min_length=2,
        max_length=10,
        pattern=r"^[a-z]{2}(_[A-Z]{2})?$",
    )

    context: str | None = Field(
        default=None,
        description="Optional context for disambiguation (e.g., 'button', 'field_label')",
        max_length=100,
    )

    class Meta:
        """Metadata configuration."""

        # Unique constraint: one translation per tenant + source + locale + context
        unique_constraints: ClassVar[list[tuple[str, ...]]] = [
            ("tenant_id", "source_text", "locale", "context"),
        ]

        # Expose as API resource for tenant admins to manage translations
        api_resource: ClassVar[bool] = True

        # Hide from Desk UI sidebar (internal system DocType)
        show_in_desk: ClassVar[bool] = False

        # Apply RLS to ensure tenants only see/modify their own translations
        apply_rls: ClassVar[bool] = True
        rls_field: ClassVar[str] = "tenant_id"

        # Require authentication
        requires_auth: ClassVar[bool] = True

        # Optional: Define label for UI
        label: ClassVar[str] = "Tenant Translation"

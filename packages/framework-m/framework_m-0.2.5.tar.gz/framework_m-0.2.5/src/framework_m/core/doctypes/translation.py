"""Translation DocType - Multilingual text translations.

This module defines the Translation DocType for storing text translations
across multiple locales. Used by DefaultI18nAdapter for DB-backed i18n.

Features:
- Supports context-aware translations (e.g., "Save" button vs "Save" menu)
- Unique constraint on (source_text, locale, context) prevents duplicates
- Fallback chain: specific locale → default locale → source text

Example:
    # Creating a translation
    translation = Translation(
        source_text="Hello, {name}!",
        translated_text="Bonjour, {name}!",
        locale="fr",
        context="greeting",
    )

    # Using in adapter
    adapter = DefaultI18nAdapter()
    text = await adapter.translate(
        "Hello, {name}!",
        locale="fr",
        context={"name": "Jean"}
    )
    # Returns: "Bonjour, Jean!"
"""

from typing import ClassVar

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class Translation(BaseDocType):
    """Translation for multilingual text.

    Attributes:
        source_text: Original text in default language (usually English)
        translated_text: Translated text in target locale
        locale: Target locale code (e.g., "fr", "es", "hi", "ta")
        context: Optional context for disambiguation (e.g., "button", "label", "error")

    Constraints:
        Unique: (source_text, locale, context) - prevents duplicate translations

    Example:
        # Simple translation
        t1 = Translation(
            source_text="Save",
            translated_text="Enregistrer",
            locale="fr",
        )

        # Context-aware translation
        t2 = Translation(
            source_text="Save",
            translated_text="Sauvegarder",
            locale="fr",
            context="button",
        )
    """

    source_text: str = Field(
        description="Original text in default language",
        min_length=1,
        max_length=1000,
    )
    translated_text: str = Field(
        description="Translated text in target locale",
        min_length=1,
        max_length=1000,
    )
    locale: str = Field(
        description="Target locale code (e.g., 'fr', 'es', 'hi')",
        min_length=2,
        max_length=10,
        pattern=r"^[a-z]{2}(_[A-Z]{2})?$",  # e.g., "en", "en_US", "zh_CN"
    )
    context: str | None = Field(
        default=None,
        description="Optional context for disambiguation",
        max_length=100,
    )

    class Meta:
        """DocType metadata."""

        # Unique constraint on source_text + locale + context
        # This is enforced at the database level via migration
        unique_constraints: ClassVar[list[tuple[str, ...]]] = [
            ("source_text", "locale", "context"),
        ]

        # Enable API access
        api_resource: ClassVar[bool] = True

        # Hide from Desk UI sidebar (internal system DocType)
        show_in_desk: ClassVar[bool] = False

        # Naming rule
        naming_rule: ClassVar[str] = "autoincrement"


__all__ = ["Translation"]

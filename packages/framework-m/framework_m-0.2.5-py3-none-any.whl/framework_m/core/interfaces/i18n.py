"""I18n Protocol - Core interface for internationalization.

This module defines the I18nProtocol for translation and
locale management.

Supports various backends: gettext, database, JSON files, etc.
"""

from typing import Protocol


class I18nProtocol(Protocol):
    """Protocol defining the contract for internationalization.

    This is the primary port for i18n in the hexagonal architecture.
    Handles text translation and locale management.

    Implementations include:
    - GettextAdapter: GNU gettext .po/.mo files
    - JsonI18nAdapter: JSON translation files
    - DatabaseI18nAdapter: Translations stored in database

    Example usage:
        i18n: I18nProtocol = container.get(I18nProtocol)

        # Get current locale
        locale = await i18n.get_locale()  # "en"

        # Translate text
        text = await i18n.translate("Hello, World!", locale="es")
        # Returns: "¡Hola, Mundo!"

        # With context
        text = await i18n.translate(
            "Welcome, {name}!",
            locale="fr",
            context={"name": "Jean"}
        )
    """

    async def translate(
        self,
        text: str,
        locale: str | None = None,
        *,
        context: dict[str, str] | None = None,
        default: str | None = None,
    ) -> str:
        """Translate text to the specified locale.

        Args:
            text: Source text to translate
            locale: Target locale (e.g., "en", "fr", "es"). Uses current if None.
            context: Variables for string interpolation
            default: Default value if translation not found

        Returns:
            Translated text (or original if no translation found)
        """
        ...

    async def get_locale(self) -> str:
        """Get the current locale for the request context.

        Returns:
            Current locale code (e.g., "en", "fr")
        """
        ...

    async def set_locale(self, locale: str) -> None:
        """Set the locale for the current request context.

        Args:
            locale: Locale code to set
        """
        ...

    async def get_available_locales(self) -> list[str]:
        """Get list of available locales.

        Returns:
            List of locale codes with translations available
        """
        ...


__all__ = [
    "I18nProtocol",
]

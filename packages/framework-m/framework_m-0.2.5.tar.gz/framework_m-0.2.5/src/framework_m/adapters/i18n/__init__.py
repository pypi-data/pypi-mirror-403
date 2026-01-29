"""I18n adapters for Framework M.

Implements I18nProtocol with various backends:
- InMemoryI18nAdapter: Dict-based for testing
- DefaultI18nAdapter: DB-backed with caching
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from framework_m.core.interfaces.repository import RepositoryProtocol


class InMemoryI18nAdapter:
    """In-memory implementation of I18nProtocol.

    Uses a simple dict to store translations.
    Suitable for testing and single-process development.

    Example:
        i18n = InMemoryI18nAdapter()
        i18n.add_translation("es", "Hello", "Hola")
        text = await i18n.translate("Hello", locale="es")
        # Returns: "Hola"
    """

    def __init__(self, default_locale: str = "en") -> None:
        """Initialize with default locale."""
        self._translations: dict[str, dict[str, str]] = {}
        self._current_locale = default_locale
        self._available_locales: list[str] = [default_locale]

    def add_translation(self, locale: str, source: str, translation: str) -> None:
        """Add a translation for a locale (sync helper for testing)."""
        if locale not in self._translations:
            self._translations[locale] = {}
            if locale not in self._available_locales:
                self._available_locales.append(locale)
        self._translations[locale][source] = translation

    async def translate(
        self,
        text: str,
        locale: str | None = None,
        *,
        context: dict[str, str] | None = None,
        default: str | None = None,
    ) -> str:
        """Translate text to the specified locale."""
        target_locale = locale or self._current_locale

        if target_locale in self._translations:
            translation = self._translations[target_locale].get(text)
            if translation:
                # Apply context interpolation
                if context:
                    for key, value in context.items():
                        translation = translation.replace(f"{{{key}}}", value)
                return translation

        return default if default else text

    async def get_locale(self) -> str:
        """Get the current locale."""
        return self._current_locale

    async def set_locale(self, locale: str) -> None:
        """Set the current locale."""
        self._current_locale = locale
        if locale not in self._available_locales:
            self._available_locales.append(locale)

    async def get_available_locales(self) -> list[str]:
        """Get list of available locales."""
        return self._available_locales.copy()


class DefaultI18nAdapter:
    """Database-backed i18n adapter with caching and tenant override support.

    Loads translations from Translation and TenantTranslation DocTypes,
    caching them in memory for fast lookups.

    Translation priority:
    1. TenantTranslation (tenant-specific override)
    2. Translation (system-wide translation)
    3. Default locale fallback
    4. Source text

    Features:
    - Lazy loading: Translations loaded on first access per locale
    - In-memory cache: Fast lookups after initial load
    - Context-aware: Supports disambiguation contexts
    - Tenant overrides: Tenants can customize translations
    - Fallback chain: Graceful degradation if translation missing

    Example:
        async with uow_factory() as uow:
            adapter = DefaultI18nAdapter(
                translation_repo=translation_repo,
                tenant_translation_repo=tenant_translation_repo,
                default_locale="en"
            )
            # First call loads from DB
            text = await adapter.translate(
                "Hello, {name}!",
                locale="fr",
                session=uow.session,
                tenant_id="acme-corp",  # Check tenant overrides
                context={"name": "Jean"}
            )
            # Subsequent calls use cache
            text2 = await adapter.translate(
                "Hello",
                locale="fr",
                session=uow.session,
                tenant_id="acme-corp"
            )
    """

    def __init__(
        self,
        translation_repo: RepositoryProtocol[Any],
        default_locale: str = "en",
        tenant_translation_repo: RepositoryProtocol[Any] | None = None,
    ) -> None:
        """Initialize with translation repositories.

        Args:
            translation_repo: Repository for Translation DocType
            default_locale: Fallback locale (default: "en")
            tenant_translation_repo: Optional repository for TenantTranslation DocType
        """
        self._repo = translation_repo
        self._tenant_repo = tenant_translation_repo
        self._default_locale = default_locale
        self._current_locale = default_locale
        # Cache: {locale: {source_text: {context: translated_text}}}
        self._cache: dict[str, dict[str, dict[str | None, str]]] = {}
        # Tenant cache: {tenant_id: {locale: {source_text: {context: translated_text}}}}
        self._tenant_cache: dict[str, dict[str, dict[str, dict[str | None, str]]]] = {}
        # Track which locales have been loaded
        self._loaded_locales: set[str] = set()
        # Track which tenant+locale combinations have been loaded
        self._loaded_tenant_locales: set[tuple[str, str]] = set()

    async def _load_locale(self, session: AsyncSession, locale: str) -> None:
        """Load all translations for a locale into cache.

        Args:
            session: Database session
            locale: Locale to load
        """
        if locale in self._loaded_locales:
            return

        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        # Query all translations for this locale
        filters = [FilterSpec(field="locale", operator=FilterOperator.EQ, value=locale)]
        result = await self._repo.list(session, filters=filters, limit=10000)  # type: ignore[arg-type, misc]

        # Build cache structure
        if locale not in self._cache:
            self._cache[locale] = {}

        for translation in result.items:
            source = translation.source_text
            context = translation.context
            translated = translation.translated_text

            if source not in self._cache[locale]:
                self._cache[locale][source] = {}

            self._cache[locale][source][context] = translated

        self._loaded_locales.add(locale)

    async def _load_tenant_locale(
        self,
        session: AsyncSession,
        tenant_id: str,
        locale: str,
    ) -> None:
        """Load tenant-specific translations for a locale into cache.

        Args:
            session: Database session
            tenant_id: Tenant identifier
            locale: Locale to load
        """
        if not self._tenant_repo:
            return

        cache_key = (tenant_id, locale)
        if cache_key in self._loaded_tenant_locales:
            return

        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        # Query tenant-specific translations
        filters = [
            FilterSpec(field="tenant_id", operator=FilterOperator.EQ, value=tenant_id),
            FilterSpec(field="locale", operator=FilterOperator.EQ, value=locale),
        ]
        result = await self._tenant_repo.list(session, filters=filters, limit=10000)  # type: ignore[arg-type, misc]

        # Build tenant cache structure
        if tenant_id not in self._tenant_cache:
            self._tenant_cache[tenant_id] = {}
        if locale not in self._tenant_cache[tenant_id]:
            self._tenant_cache[tenant_id][locale] = {}

        for translation in result.items:
            source = translation.source_text
            context = translation.context
            translated = translation.translated_text

            if source not in self._tenant_cache[tenant_id][locale]:
                self._tenant_cache[tenant_id][locale][source] = {}

            self._tenant_cache[tenant_id][locale][source][context] = translated

        self._loaded_tenant_locales.add(cache_key)

    async def translate(
        self,
        text: str,
        locale: str | None = None,
        *,
        session: AsyncSession,
        context: dict[str, str] | None = None,
        default: str | None = None,
        translation_context: str | None = None,
        tenant_id: str | None = None,
    ) -> str:
        """Translate text to the specified locale with tenant override support.

        Args:
            text: Source text to translate
            locale: Target locale (uses current if None)
            session: Database session for loading translations
            context: Variables for string interpolation (e.g., {"name": "John"})
            default: Default value if translation not found
            translation_context: Context key for disambiguation (e.g., "button", "label")
            tenant_id: Optional tenant ID for tenant-specific overrides

        Returns:
            Translated text with context interpolation applied
        """
        target_locale = locale or self._current_locale

        # Load system translations
        await self._load_locale(session, target_locale)

        # Load tenant translations if tenant_id provided
        if tenant_id and self._tenant_repo:
            await self._load_tenant_locale(session, tenant_id, target_locale)

        # Try to find translation with priority:
        # 1. Tenant-specific translation
        # 2. System-wide translation
        translation = None

        # Check tenant override first
        if (
            tenant_id
            and tenant_id in self._tenant_cache
            and (
                target_locale in self._tenant_cache[tenant_id]
                and text in self._tenant_cache[tenant_id][target_locale]
            )
        ):
            # Try context-specific translation first
            if (
                translation_context
                in self._tenant_cache[tenant_id][target_locale][text]
            ):
                translation = self._tenant_cache[tenant_id][target_locale][text][
                    translation_context
                ]
            # Fall back to no-context translation
            elif None in self._tenant_cache[tenant_id][target_locale][text]:
                translation = self._tenant_cache[tenant_id][target_locale][text][None]

        # Fall back to system translation if no tenant override
        if (
            not translation
            and target_locale in self._cache
            and text in self._cache[target_locale]
        ):
            # Try context-specific translation first
            if translation_context in self._cache[target_locale][text]:
                translation = self._cache[target_locale][text][translation_context]
            # Fall back to no-context translation
            elif None in self._cache[target_locale][text]:
                translation = self._cache[target_locale][text][None]

        # Fallback to default locale if not found
        if not translation and target_locale != self._default_locale:
            await self._load_locale(session, self._default_locale)
            if (
                self._default_locale in self._cache
                and text in self._cache[self._default_locale]
            ):
                if translation_context in self._cache[self._default_locale][text]:
                    translation = self._cache[self._default_locale][text][
                        translation_context
                    ]
                elif None in self._cache[self._default_locale][text]:
                    translation = self._cache[self._default_locale][text][None]

        # Use translation or fallback
        result = translation or default or text

        # Apply context interpolation
        if context:
            for key, value in context.items():
                result = result.replace(f"{{{key}}}", str(value))

        return result

    async def get_locale(self) -> str:
        """Get the current locale."""
        return self._current_locale

    async def set_locale(self, locale: str) -> None:
        """Set the current locale."""
        self._current_locale = locale

    async def get_available_locales(self) -> list[str]:
        """Get list of loaded locales.

        Returns:
            List of locale codes that have been loaded
        """
        return list(self._loaded_locales)


__all__ = ["DefaultI18nAdapter", "InMemoryI18nAdapter"]

"""Tests for I18nProtocol interface compliance."""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from framework_m.adapters.i18n import DefaultI18nAdapter, InMemoryI18nAdapter
from framework_m.core.interfaces.i18n import I18nProtocol


class TestI18nProtocol:
    """Tests for I18nProtocol interface."""

    def test_protocol_has_translate_method(self) -> None:
        """I18nProtocol should define translate method."""
        assert hasattr(I18nProtocol, "translate")

    def test_protocol_has_get_locale_method(self) -> None:
        """I18nProtocol should define get_locale method."""
        assert hasattr(I18nProtocol, "get_locale")

    def test_protocol_has_set_locale_method(self) -> None:
        """I18nProtocol should define set_locale method."""
        assert hasattr(I18nProtocol, "set_locale")

    def test_protocol_has_get_available_locales_method(self) -> None:
        """I18nProtocol should define get_available_locales method."""
        assert hasattr(I18nProtocol, "get_available_locales")


# =============================================================================
# Tests for InMemoryI18nAdapter
# =============================================================================


class TestInMemoryI18nAdapter:
    """Tests for InMemoryI18nAdapter."""

    @pytest.fixture
    def i18n(self) -> InMemoryI18nAdapter:
        """Create an i18n adapter instance."""
        return InMemoryI18nAdapter()

    @pytest.mark.asyncio
    async def test_default_locale(self, i18n: InMemoryI18nAdapter) -> None:
        """Default locale should be 'en'."""
        locale = await i18n.get_locale()
        assert locale == "en"

    @pytest.mark.asyncio
    async def test_set_locale(self, i18n: InMemoryI18nAdapter) -> None:
        """set_locale() should change current locale."""
        await i18n.set_locale("fr")
        locale = await i18n.get_locale()
        assert locale == "fr"

    @pytest.mark.asyncio
    async def test_get_available_locales_default(
        self, i18n: InMemoryI18nAdapter
    ) -> None:
        """get_available_locales() should return default locale."""
        locales = await i18n.get_available_locales()
        assert "en" in locales

    @pytest.mark.asyncio
    async def test_translate_no_translation(self, i18n: InMemoryI18nAdapter) -> None:
        """translate() should return original text if no translation."""
        result = await i18n.translate("Hello")
        assert result == "Hello"

    @pytest.mark.asyncio
    async def test_translate_with_translation(self, i18n: InMemoryI18nAdapter) -> None:
        """translate() should return translated text."""
        i18n.add_translation("es", "Hello", "Hola")
        result = await i18n.translate("Hello", locale="es")
        assert result == "Hola"

    @pytest.mark.asyncio
    async def test_translate_with_context(self, i18n: InMemoryI18nAdapter) -> None:
        """translate() should interpolate context variables."""
        i18n.add_translation("fr", "Hello, {name}!", "Bonjour, {name}!")
        result = await i18n.translate(
            "Hello, {name}!", locale="fr", context={"name": "Jean"}
        )
        assert result == "Bonjour, Jean!"

    @pytest.mark.asyncio
    async def test_translate_with_default(self, i18n: InMemoryI18nAdapter) -> None:
        """translate() should return default if translation not found."""
        result = await i18n.translate("Unknown", default="Fallback")
        assert result == "Fallback"

    @pytest.mark.asyncio
    async def test_set_locale_adds_to_available(
        self, i18n: InMemoryI18nAdapter
    ) -> None:
        """set_locale() should add new locale to available locales."""
        await i18n.set_locale("de")
        locales = await i18n.get_available_locales()
        assert "de" in locales


# =============================================================================
# Tests for DefaultI18nAdapter
# =============================================================================


class MockTranslation:
    """Mock Translation entity."""

    def __init__(
        self,
        source_text: str,
        translated_text: str,
        locale: str,
        context: str | None = None,
    ) -> None:
        self.source_text = source_text
        self.translated_text = translated_text
        self.locale = locale
        self.context = context


class MockTenantTranslation:
    """Mock TenantTranslation entity."""

    def __init__(
        self,
        source_text: str,
        translated_text: str,
        locale: str,
        tenant_id: str,
        context: str | None = None,
    ) -> None:
        self.source_text = source_text
        self.translated_text = translated_text
        self.locale = locale
        self.tenant_id = tenant_id
        self.context = context


class MockPaginatedResult:
    """Mock paginated result."""

    def __init__(self, items: list[Any]) -> None:
        self.items = items


class TestDefaultI18nAdapter:
    """Comprehensive tests for DefaultI18nAdapter."""

    @pytest.fixture
    def mock_repo(self) -> Mock:
        """Create a mock translation repository."""
        repo = Mock()
        repo.list = AsyncMock()
        return repo

    @pytest.fixture
    def mock_tenant_repo(self) -> Mock:
        """Create a mock tenant translation repository."""
        repo = Mock()
        repo.list = AsyncMock()
        return repo

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def adapter(self, mock_repo: Mock) -> DefaultI18nAdapter:
        """Create DefaultI18nAdapter instance."""
        return DefaultI18nAdapter(
            translation_repo=mock_repo,
            default_locale="en",
        )

    @pytest.fixture
    def adapter_with_tenant(
        self, mock_repo: Mock, mock_tenant_repo: Mock
    ) -> DefaultI18nAdapter:
        """Create DefaultI18nAdapter instance with tenant support."""
        return DefaultI18nAdapter(
            translation_repo=mock_repo,
            tenant_translation_repo=mock_tenant_repo,
            default_locale="en",
        )

    @pytest.mark.asyncio
    async def test_initialization(self, adapter: DefaultI18nAdapter) -> None:
        """Should initialize with correct default values."""
        assert adapter._default_locale == "en"
        assert adapter._current_locale == "en"
        assert adapter._cache == {}
        assert adapter._tenant_cache == {}
        assert adapter._loaded_locales == set()
        assert adapter._loaded_tenant_locales == set()

    @pytest.mark.asyncio
    async def test_get_locale(self, adapter: DefaultI18nAdapter) -> None:
        """Should return current locale."""
        locale = await adapter.get_locale()
        assert locale == "en"

    @pytest.mark.asyncio
    async def test_set_locale(self, adapter: DefaultI18nAdapter) -> None:
        """Should set current locale."""
        await adapter.set_locale("fr")
        locale = await adapter.get_locale()
        assert locale == "fr"

    @pytest.mark.asyncio
    async def test_get_available_locales_empty(
        self, adapter: DefaultI18nAdapter
    ) -> None:
        """Should return empty list initially."""
        locales = await adapter.get_available_locales()
        assert locales == []

    @pytest.mark.asyncio
    async def test_load_locale_basic(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should load translations from repository."""
        # Setup mock data
        translations = [
            MockTranslation("Hello", "Hola", "es", None),
            MockTranslation("Goodbye", "Adiós", "es", None),
        ]
        mock_repo.list.return_value = MockPaginatedResult(translations)

        # Load locale
        await adapter._load_locale(mock_session, "es")

        # Verify repository was called correctly
        mock_repo.list.assert_called_once()
        call_args = mock_repo.list.call_args
        assert call_args[0][0] == mock_session

        # Verify cache was populated
        assert "es" in adapter._cache
        assert "Hello" in adapter._cache["es"]
        assert adapter._cache["es"]["Hello"][None] == "Hola"
        assert "Goodbye" in adapter._cache["es"]
        assert adapter._cache["es"]["Goodbye"][None] == "Adiós"

        # Verify locale was marked as loaded
        assert "es" in adapter._loaded_locales

    @pytest.mark.asyncio
    async def test_load_locale_with_context(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should load translations with context keys."""
        translations = [
            MockTranslation("Submit", "Enviar", "es", "button"),
            MockTranslation("Submit", "Presentar", "es", "form"),
            MockTranslation("Submit", "Enviar", "es", None),
        ]
        mock_repo.list.return_value = MockPaginatedResult(translations)

        await adapter._load_locale(mock_session, "es")

        # Verify context-specific translations
        assert adapter._cache["es"]["Submit"]["button"] == "Enviar"
        assert adapter._cache["es"]["Submit"]["form"] == "Presentar"
        assert adapter._cache["es"]["Submit"][None] == "Enviar"

    @pytest.mark.asyncio
    async def test_load_locale_idempotent(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should not reload if locale already loaded."""
        translations = [MockTranslation("Hello", "Hola", "es", None)]
        mock_repo.list.return_value = MockPaginatedResult(translations)

        # Load once
        await adapter._load_locale(mock_session, "es")
        assert mock_repo.list.call_count == 1

        # Try to load again
        await adapter._load_locale(mock_session, "es")
        assert mock_repo.list.call_count == 1  # Should not call again

    @pytest.mark.asyncio
    async def test_load_tenant_locale_basic(
        self,
        adapter_with_tenant: DefaultI18nAdapter,
        mock_tenant_repo: Mock,
        mock_session: Mock,
    ) -> None:
        """Should load tenant-specific translations."""
        tenant_translations = [
            MockTenantTranslation("Hello", "Tenant Hello", "es", "acme", None),
        ]
        mock_tenant_repo.list.return_value = MockPaginatedResult(tenant_translations)

        await adapter_with_tenant._load_tenant_locale(mock_session, "acme", "es")

        # Verify tenant cache was populated
        assert "acme" in adapter_with_tenant._tenant_cache
        assert "es" in adapter_with_tenant._tenant_cache["acme"]
        assert "Hello" in adapter_with_tenant._tenant_cache["acme"]["es"]
        assert (
            adapter_with_tenant._tenant_cache["acme"]["es"]["Hello"][None]
            == "Tenant Hello"
        )

        # Verify loaded tracking
        assert ("acme", "es") in adapter_with_tenant._loaded_tenant_locales

    @pytest.mark.asyncio
    async def test_load_tenant_locale_no_tenant_repo(
        self, adapter: DefaultI18nAdapter, mock_session: Mock
    ) -> None:
        """Should handle missing tenant repo gracefully."""
        # Should not raise error
        await adapter._load_tenant_locale(mock_session, "acme", "es")

        # Should not add to tenant cache
        assert adapter._tenant_cache == {}

    @pytest.mark.asyncio
    async def test_load_tenant_locale_idempotent(
        self,
        adapter_with_tenant: DefaultI18nAdapter,
        mock_tenant_repo: Mock,
        mock_session: Mock,
    ) -> None:
        """Should not reload tenant locale if already loaded."""
        tenant_translations = [
            MockTenantTranslation("Hello", "Tenant Hello", "es", "acme", None),
        ]
        mock_tenant_repo.list.return_value = MockPaginatedResult(tenant_translations)

        # Load once
        await adapter_with_tenant._load_tenant_locale(mock_session, "acme", "es")
        assert mock_tenant_repo.list.call_count == 1

        # Try to load again
        await adapter_with_tenant._load_tenant_locale(mock_session, "acme", "es")
        assert mock_tenant_repo.list.call_count == 1  # Should not call again

    @pytest.mark.asyncio
    async def test_translate_basic(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should translate text using loaded translations."""
        translations = [MockTranslation("Hello", "Hola", "es", None)]
        mock_repo.list.return_value = MockPaginatedResult(translations)

        result = await adapter.translate("Hello", "es", session=mock_session)

        assert result == "Hola"
        assert "es" in adapter._loaded_locales

    @pytest.mark.asyncio
    async def test_translate_no_translation_returns_original(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should return original text if no translation found."""
        mock_repo.list.return_value = MockPaginatedResult([])

        result = await adapter.translate("Unknown", "es", session=mock_session)

        assert result == "Unknown"

    @pytest.mark.asyncio
    async def test_translate_with_default(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should return default value if provided and no translation."""
        mock_repo.list.return_value = MockPaginatedResult([])

        result = await adapter.translate(
            "Unknown", "es", session=mock_session, default="Fallback"
        )

        assert result == "Fallback"

    @pytest.mark.asyncio
    async def test_translate_uses_current_locale_if_none(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should use current locale if none specified."""
        await adapter.set_locale("fr")
        translations = [MockTranslation("Hello", "Bonjour", "fr", None)]
        mock_repo.list.return_value = MockPaginatedResult(translations)

        result = await adapter.translate("Hello", session=mock_session)

        assert result == "Bonjour"

    @pytest.mark.asyncio
    async def test_translate_with_context_interpolation(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should interpolate context variables."""
        translations = [MockTranslation("Hello, {name}!", "Hola, {name}!", "es", None)]
        mock_repo.list.return_value = MockPaginatedResult(translations)

        result = await adapter.translate(
            "Hello, {name}!", "es", session=mock_session, context={"name": "Juan"}
        )

        assert result == "Hola, Juan!"

    @pytest.mark.asyncio
    async def test_translate_with_translation_context(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should use translation context for disambiguation."""
        translations = [
            MockTranslation("Submit", "Enviar", "es", "button"),
            MockTranslation("Submit", "Presentar", "es", "form"),
        ]
        mock_repo.list.return_value = MockPaginatedResult(translations)

        result_button = await adapter.translate(
            "Submit", "es", session=mock_session, translation_context="button"
        )
        result_form = await adapter.translate(
            "Submit", "es", session=mock_session, translation_context="form"
        )

        assert result_button == "Enviar"
        assert result_form == "Presentar"

    @pytest.mark.asyncio
    async def test_translate_context_fallback_to_none(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should fall back to no-context translation if context not found."""
        translations = [MockTranslation("Submit", "Enviar", "es", None)]
        mock_repo.list.return_value = MockPaginatedResult(translations)

        result = await adapter.translate(
            "Submit", "es", session=mock_session, translation_context="button"
        )

        assert result == "Enviar"

    @pytest.mark.asyncio
    async def test_translate_with_tenant_override(
        self,
        adapter_with_tenant: DefaultI18nAdapter,
        mock_repo: Mock,
        mock_tenant_repo: Mock,
        mock_session: Mock,
    ) -> None:
        """Should use tenant translation over system translation."""
        # System translation
        system_translations = [MockTranslation("Hello", "Hola", "es", None)]
        mock_repo.list.return_value = MockPaginatedResult(system_translations)

        # Tenant override
        tenant_translations = [
            MockTenantTranslation("Hello", "Tenant Hola", "es", "acme", None)
        ]
        mock_tenant_repo.list.return_value = MockPaginatedResult(tenant_translations)

        result = await adapter_with_tenant.translate(
            "Hello", "es", session=mock_session, tenant_id="acme"
        )

        assert result == "Tenant Hola"

    @pytest.mark.asyncio
    async def test_translate_tenant_with_context(
        self,
        adapter_with_tenant: DefaultI18nAdapter,
        mock_repo: Mock,
        mock_tenant_repo: Mock,
        mock_session: Mock,
    ) -> None:
        """Should use tenant translation context over system."""
        system_translations = [MockTranslation("Submit", "Enviar", "es", "button")]
        mock_repo.list.return_value = MockPaginatedResult(system_translations)

        tenant_translations = [
            MockTenantTranslation("Submit", "Tenant Submit", "es", "acme", "button")
        ]
        mock_tenant_repo.list.return_value = MockPaginatedResult(tenant_translations)

        result = await adapter_with_tenant.translate(
            "Submit",
            "es",
            session=mock_session,
            tenant_id="acme",
            translation_context="button",
        )

        assert result == "Tenant Submit"

    @pytest.mark.asyncio
    async def test_translate_tenant_fallback_to_none_context(
        self,
        adapter_with_tenant: DefaultI18nAdapter,
        mock_repo: Mock,
        mock_tenant_repo: Mock,
        mock_session: Mock,
    ) -> None:
        """Should fall back to tenant no-context if context not found."""
        mock_repo.list.return_value = MockPaginatedResult([])

        tenant_translations = [
            MockTenantTranslation("Submit", "Tenant Submit", "es", "acme", None)
        ]
        mock_tenant_repo.list.return_value = MockPaginatedResult(tenant_translations)

        result = await adapter_with_tenant.translate(
            "Submit",
            "es",
            session=mock_session,
            tenant_id="acme",
            translation_context="button",
        )

        assert result == "Tenant Submit"

    @pytest.mark.asyncio
    async def test_translate_fallback_to_default_locale(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should fall back to default locale if translation not found."""

        async def mock_list_side_effect(*args: Any, **kwargs: Any) -> Any:
            filters = kwargs.get("filters", [])
            if not filters:
                return MockPaginatedResult([])

            locale_filter = filters[0]
            if locale_filter.value == "fr":
                # No French translation
                return MockPaginatedResult([])
            elif locale_filter.value == "en":
                # English (default) translation exists
                return MockPaginatedResult(
                    [MockTranslation("Hello", "Hello (EN)", "en", None)]
                )
            return MockPaginatedResult([])

        mock_repo.list.side_effect = mock_list_side_effect

        result = await adapter.translate("Hello", "fr", session=mock_session)

        assert result == "Hello (EN)"
        assert "fr" in adapter._loaded_locales
        assert "en" in adapter._loaded_locales

    @pytest.mark.asyncio
    async def test_translate_default_locale_with_context(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should use context when falling back to default locale."""

        async def mock_list_side_effect(*args: Any, **kwargs: Any) -> Any:
            filters = kwargs.get("filters", [])
            if not filters:
                return MockPaginatedResult([])

            locale_filter = filters[0]
            if locale_filter.value == "fr":
                return MockPaginatedResult([])
            elif locale_filter.value == "en":
                return MockPaginatedResult(
                    [MockTranslation("Submit", "Submit (EN)", "en", "button")]
                )
            return MockPaginatedResult([])

        mock_repo.list.side_effect = mock_list_side_effect

        result = await adapter.translate(
            "Submit", "fr", session=mock_session, translation_context="button"
        )

        assert result == "Submit (EN)"

    @pytest.mark.asyncio
    async def test_translate_default_locale_fallback_to_none_context(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should fall back to no-context in default locale."""

        async def mock_list_side_effect(*args: Any, **kwargs: Any) -> Any:
            filters = kwargs.get("filters", [])
            if not filters:
                return MockPaginatedResult([])

            locale_filter = filters[0]
            if locale_filter.value == "fr":
                return MockPaginatedResult([])
            elif locale_filter.value == "en":
                return MockPaginatedResult(
                    [MockTranslation("Submit", "Submit (EN)", "en", None)]
                )
            return MockPaginatedResult([])

        mock_repo.list.side_effect = mock_list_side_effect

        result = await adapter.translate(
            "Submit", "fr", session=mock_session, translation_context="button"
        )

        assert result == "Submit (EN)"

    @pytest.mark.asyncio
    async def test_translate_no_fallback_if_already_default(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should not try to fallback if already using default locale."""
        mock_repo.list.return_value = MockPaginatedResult([])

        result = await adapter.translate("Unknown", "en", session=mock_session)

        # Should only call once (for "en"), not twice
        assert mock_repo.list.call_count == 1
        assert result == "Unknown"

    @pytest.mark.asyncio
    async def test_get_available_locales_after_loading(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should return list of loaded locales."""
        mock_repo.list.return_value = MockPaginatedResult(
            [MockTranslation("Hello", "Hola", "es", None)]
        )

        await adapter.translate("Hello", "es", session=mock_session)

        locales = await adapter.get_available_locales()
        assert "es" in locales

    @pytest.mark.asyncio
    async def test_translate_multiple_interpolations(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should interpolate multiple context variables."""
        translations = [
            MockTranslation(
                "{greeting}, {name}! You have {count} messages.",
                "{greeting}, {name}! Tienes {count} mensajes.",
                "es",
                None,
            )
        ]
        mock_repo.list.return_value = MockPaginatedResult(translations)

        result = await adapter.translate(
            "{greeting}, {name}! You have {count} messages.",
            "es",
            session=mock_session,
            context={"greeting": "Hola", "name": "Juan", "count": "5"},
        )

        assert result == "Hola, Juan! Tienes 5 mensajes."

    @pytest.mark.asyncio
    async def test_load_locale_empty_result(
        self, adapter: DefaultI18nAdapter, mock_repo: Mock, mock_session: Mock
    ) -> None:
        """Should handle empty translation result gracefully."""
        mock_repo.list.return_value = MockPaginatedResult([])

        await adapter._load_locale(mock_session, "es")

        assert "es" in adapter._loaded_locales
        assert adapter._cache.get("es", {}) == {}

    @pytest.mark.asyncio
    async def test_load_tenant_locale_empty_result(
        self,
        adapter_with_tenant: DefaultI18nAdapter,
        mock_tenant_repo: Mock,
        mock_session: Mock,
    ) -> None:
        """Should handle empty tenant translation result gracefully."""
        mock_tenant_repo.list.return_value = MockPaginatedResult([])

        await adapter_with_tenant._load_tenant_locale(mock_session, "acme", "es")

        assert ("acme", "es") in adapter_with_tenant._loaded_tenant_locales
        assert adapter_with_tenant._tenant_cache.get("acme", {}).get("es", {}) == {}

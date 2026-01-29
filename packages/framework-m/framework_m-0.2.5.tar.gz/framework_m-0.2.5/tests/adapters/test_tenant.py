"""Tests for Tenant Adapters.

Tests cover:
- ImplicitTenantAdapter (Mode A: Single Tenant)
- HeaderTenantAdapter (Mode B: Multi-Tenant)
- Factory function
"""

from unittest.mock import patch

# =============================================================================
# Test: ImplicitTenantAdapter Import
# =============================================================================


class TestImplicitTenantAdapterImport:
    """Tests for ImplicitTenantAdapter import."""

    def test_import_implicit_tenant_adapter(self) -> None:
        """ImplicitTenantAdapter should be importable."""
        from framework_m.adapters.tenant import ImplicitTenantAdapter

        assert ImplicitTenantAdapter is not None


class TestImplicitTenantAdapterInit:
    """Tests for ImplicitTenantAdapter initialization."""

    def test_init_with_defaults(self) -> None:
        """ImplicitTenantAdapter should use default tenant from config."""
        from framework_m.adapters.tenant import ImplicitTenantAdapter

        with patch(
            "framework_m.adapters.tenant.get_default_tenant_id",
            return_value="default",
        ):
            adapter = ImplicitTenantAdapter()

        assert adapter._tenant_id == "default"
        assert adapter._attributes == {"plan": "unlimited", "features": "*"}

    def test_init_with_custom_tenant(self) -> None:
        """ImplicitTenantAdapter should accept custom tenant ID."""
        from framework_m.adapters.tenant import ImplicitTenantAdapter

        adapter = ImplicitTenantAdapter(tenant_id="custom")
        assert adapter._tenant_id == "custom"

    def test_init_with_custom_attributes(self) -> None:
        """ImplicitTenantAdapter should accept custom attributes."""
        from framework_m.adapters.tenant import ImplicitTenantAdapter

        adapter = ImplicitTenantAdapter(attributes={"plan": "pro"})
        assert adapter._attributes == {"plan": "pro"}


class TestImplicitTenantAdapterMethods:
    """Tests for ImplicitTenantAdapter methods."""

    def test_get_current_tenant(self) -> None:
        """get_current_tenant should return configured tenant ID."""
        from framework_m.adapters.tenant import ImplicitTenantAdapter

        adapter = ImplicitTenantAdapter(tenant_id="my-tenant")
        assert adapter.get_current_tenant() == "my-tenant"

    def test_get_tenant_attributes(self) -> None:
        """get_tenant_attributes should return configured attributes."""
        from framework_m.adapters.tenant import ImplicitTenantAdapter

        adapter = ImplicitTenantAdapter(attributes={"plan": "enterprise"})
        attrs = adapter.get_tenant_attributes("any-id")
        assert attrs["plan"] == "enterprise"

    def test_get_context(self) -> None:
        """get_context should return TenantContext."""
        from framework_m.adapters.tenant import ImplicitTenantAdapter
        from framework_m.core.interfaces.tenant import TenantContext

        adapter = ImplicitTenantAdapter(tenant_id="test")
        ctx = adapter.get_context()

        assert isinstance(ctx, TenantContext)
        assert ctx.tenant_id == "test"
        assert ctx.is_default is True


# =============================================================================
# Test: HeaderTenantAdapter Import
# =============================================================================


class TestHeaderTenantAdapterImport:
    """Tests for HeaderTenantAdapter import."""

    def test_import_header_tenant_adapter(self) -> None:
        """HeaderTenantAdapter should be importable."""
        from framework_m.adapters.tenant import HeaderTenantAdapter

        assert HeaderTenantAdapter is not None


class TestHeaderTenantAdapterGetTenant:
    """Tests for HeaderTenantAdapter.get_current_tenant."""

    def test_get_tenant_from_header(self) -> None:
        """get_current_tenant should extract from X-Tenant-ID header."""
        from framework_m.adapters.tenant import HeaderTenantAdapter

        headers = {"x-tenant-id": "acme-corp"}
        adapter = HeaderTenantAdapter(headers=headers)

        assert adapter.get_current_tenant() == "acme-corp"

    def test_get_tenant_default_when_missing(self) -> None:
        """get_current_tenant should return default when header missing."""
        from framework_m.adapters.tenant import HeaderTenantAdapter

        headers: dict[str, str] = {}
        adapter = HeaderTenantAdapter(headers=headers)

        assert adapter.get_current_tenant() == "default"


class TestHeaderTenantAdapterGetAttributes:
    """Tests for HeaderTenantAdapter.get_tenant_attributes."""

    def test_get_attributes_from_json_header(self) -> None:
        """get_tenant_attributes should parse JSON from header."""
        from framework_m.adapters.tenant import HeaderTenantAdapter

        headers = {
            "x-tenant-id": "acme",
            "x-tenant-attributes": '{"plan": "enterprise", "features": ["reports"]}',
        }
        adapter = HeaderTenantAdapter(headers=headers)

        attrs = adapter.get_tenant_attributes("acme")
        assert attrs["plan"] == "enterprise"
        assert "reports" in attrs["features"]

    def test_get_attributes_empty_when_missing(self) -> None:
        """get_tenant_attributes should return {} when header missing."""
        from framework_m.adapters.tenant import HeaderTenantAdapter

        headers = {"x-tenant-id": "acme"}
        adapter = HeaderTenantAdapter(headers=headers)

        assert adapter.get_tenant_attributes("acme") == {}

    def test_get_attributes_empty_on_invalid_json(self) -> None:
        """get_tenant_attributes should return {} for invalid JSON."""
        from framework_m.adapters.tenant import HeaderTenantAdapter

        headers = {
            "x-tenant-id": "acme",
            "x-tenant-attributes": "not valid json",
        }
        adapter = HeaderTenantAdapter(headers=headers)

        assert adapter.get_tenant_attributes("acme") == {}


class TestHeaderTenantAdapterGetContext:
    """Tests for HeaderTenantAdapter.get_context."""

    def test_get_context(self) -> None:
        """get_context should return TenantContext from headers."""
        from framework_m.adapters.tenant import HeaderTenantAdapter
        from framework_m.core.interfaces.tenant import TenantContext

        headers = {
            "x-tenant-id": "acme",
            "x-tenant-attributes": '{"plan": "pro"}',
        }
        adapter = HeaderTenantAdapter(headers=headers)
        ctx = adapter.get_context()

        assert isinstance(ctx, TenantContext)
        assert ctx.tenant_id == "acme"
        assert ctx.attributes["plan"] == "pro"
        assert ctx.is_default is False


# =============================================================================
# Test: Factory Function
# =============================================================================


class TestTenantAdapterFactory:
    """Tests for create_tenant_adapter_from_headers factory."""

    def test_import_factory(self) -> None:
        """create_tenant_adapter_from_headers should be importable."""
        from framework_m.adapters.tenant import create_tenant_adapter_from_headers

        assert create_tenant_adapter_from_headers is not None

    def test_single_tenant_mode_returns_implicit(self) -> None:
        """Factory should return ImplicitTenantAdapter in single-tenant mode."""
        from framework_m.adapters.tenant import (
            ImplicitTenantAdapter,
            create_tenant_adapter_from_headers,
        )

        with patch(
            "framework_m.core.interfaces.tenant.is_multi_tenant", return_value=False
        ):
            adapter = create_tenant_adapter_from_headers()

        assert isinstance(adapter, ImplicitTenantAdapter)

    def test_multi_tenant_with_headers_returns_header(self) -> None:
        """Factory should return HeaderTenantAdapter in multi-tenant mode."""
        from framework_m.adapters.tenant import (
            HeaderTenantAdapter,
            create_tenant_adapter_from_headers,
        )

        with patch(
            "framework_m.core.interfaces.tenant.is_multi_tenant", return_value=True
        ):
            headers = {"x-tenant-id": "acme"}
            adapter = create_tenant_adapter_from_headers(headers=headers)

        assert isinstance(adapter, HeaderTenantAdapter)

    def test_multi_tenant_without_headers_returns_implicit(self) -> None:
        """Factory should return ImplicitTenantAdapter if no headers."""
        from framework_m.adapters.tenant import (
            ImplicitTenantAdapter,
            create_tenant_adapter_from_headers,
        )

        with patch(
            "framework_m.core.interfaces.tenant.is_multi_tenant", return_value=True
        ):
            adapter = create_tenant_adapter_from_headers(headers=None)

        assert isinstance(adapter, ImplicitTenantAdapter)

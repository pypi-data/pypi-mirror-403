"""Tests for Tenant Protocol.

Tests cover:
- TenantProtocol interface
- TenantContext model
- Tenancy configuration
"""

from typing import Any
from unittest.mock import patch

# =============================================================================
# Test: TenantProtocol Import
# =============================================================================


class TestTenantProtocolImport:
    """Tests for TenantProtocol import."""

    def test_import_tenant_protocol(self) -> None:
        """TenantProtocol should be importable."""
        from framework_m.core.interfaces.tenant import TenantProtocol

        assert TenantProtocol is not None

    def test_import_tenant_context(self) -> None:
        """TenantContext should be importable."""
        from framework_m.core.interfaces.tenant import TenantContext

        assert TenantContext is not None


# =============================================================================
# Test: TenantContext Model
# =============================================================================


class TestTenantContext:
    """Tests for TenantContext model."""

    def test_create_tenant_context(self) -> None:
        """TenantContext should accept tenant_id and attributes."""
        from framework_m.core.interfaces.tenant import TenantContext

        ctx = TenantContext(
            tenant_id="acme-corp",
            attributes={"plan": "enterprise"},
        )

        assert ctx.tenant_id == "acme-corp"
        assert ctx.attributes["plan"] == "enterprise"

    def test_default_tenant_context(self) -> None:
        """TenantContext should work with minimal fields."""
        from framework_m.core.interfaces.tenant import TenantContext

        ctx = TenantContext(tenant_id="default")

        assert ctx.tenant_id == "default"
        assert ctx.attributes == {}
        assert ctx.is_default is False

    def test_default_tenant_flag(self) -> None:
        """TenantContext should support is_default flag."""
        from framework_m.core.interfaces.tenant import TenantContext

        ctx = TenantContext(tenant_id="default", is_default=True)

        assert ctx.is_default is True


# =============================================================================
# Test: TenantProtocol Interface
# =============================================================================


class TestTenantProtocolInterface:
    """Tests for TenantProtocol interface compliance."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """TenantProtocol should be runtime checkable."""
        from framework_m.core.interfaces.tenant import TenantProtocol

        class MockAdapter:
            def get_current_tenant(self) -> str:
                return "test"

            def get_tenant_attributes(self, tenant_id: str) -> dict[str, Any]:
                return {}

        adapter = MockAdapter()
        assert isinstance(adapter, TenantProtocol)

    def test_non_compliant_class_fails_check(self) -> None:
        """Non-compliant class should fail protocol check."""
        from framework_m.core.interfaces.tenant import TenantProtocol

        class NotAnAdapter:
            pass

        adapter = NotAnAdapter()
        assert not isinstance(adapter, TenantProtocol)


# =============================================================================
# Test: Tenancy Configuration
# =============================================================================


class TestTenancyConfig:
    """Tests for tenancy configuration."""

    def test_import_get_tenancy_config(self) -> None:
        """get_tenancy_config should be importable."""
        from framework_m.core.interfaces.tenant import get_tenancy_config

        assert get_tenancy_config is not None

    def test_default_config(self) -> None:
        """get_tenancy_config should return defaults when not configured."""
        from framework_m.core.interfaces.tenant import get_tenancy_config

        with patch("framework_m.core.interfaces.tenant.load_config", return_value={}):
            config = get_tenancy_config()

        assert config["mode"] == "single"
        assert config["default_tenant_id"] == "default"

    def test_multi_tenant_mode_from_config(self) -> None:
        """get_tenancy_config should read multi-tenant mode."""
        from framework_m.core.interfaces.tenant import get_tenancy_config

        mock_config = {"tenancy": {"mode": "multi", "default_tenant_id": "acme"}}
        with patch(
            "framework_m.core.interfaces.tenant.load_config", return_value=mock_config
        ):
            config = get_tenancy_config()

        assert config["mode"] == "multi"
        assert config["default_tenant_id"] == "acme"


class TestTenancyHelpers:
    """Tests for tenancy helper functions."""

    def test_import_is_multi_tenant(self) -> None:
        """is_multi_tenant should be importable."""
        from framework_m.core.interfaces.tenant import is_multi_tenant

        assert is_multi_tenant is not None

    def test_single_tenant_mode(self) -> None:
        """is_multi_tenant should return False for single mode."""
        from framework_m.core.interfaces.tenant import is_multi_tenant

        with patch("framework_m.core.interfaces.tenant.load_config", return_value={}):
            assert is_multi_tenant() is False

    def test_multi_tenant_mode(self) -> None:
        """is_multi_tenant should return True for multi mode."""
        from framework_m.core.interfaces.tenant import is_multi_tenant

        mock_config = {"tenancy": {"mode": "multi"}}
        with patch(
            "framework_m.core.interfaces.tenant.load_config", return_value=mock_config
        ):
            assert is_multi_tenant() is True

    def test_get_default_tenant_id(self) -> None:
        """get_default_tenant_id should return configured default."""
        from framework_m.core.interfaces.tenant import get_default_tenant_id

        mock_config = {"tenancy": {"default_tenant_id": "my-tenant"}}
        with patch(
            "framework_m.core.interfaces.tenant.load_config", return_value=mock_config
        ):
            assert get_default_tenant_id() == "my-tenant"

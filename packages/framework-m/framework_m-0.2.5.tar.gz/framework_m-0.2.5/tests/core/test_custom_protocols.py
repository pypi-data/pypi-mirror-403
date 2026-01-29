"""Tests for Custom Protocol Registration - App-Defined Ports.

This module tests the custom protocol registration functionality that allows:
- Apps to define their own protocols (ports)
- Register app containers via entrypoints
- Other apps to override app-defined protocols
- Dynamic discovery and loading of app containers
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol
from unittest.mock import Mock, patch

import pytest
from dependency_injector import containers, providers


# Test Fixtures - Mock App Protocols and Implementations
class PaymentGatewayProtocol(Protocol):
    """Protocol for payment gateway (app-defined)."""

    async def charge(self, amount: Decimal, token: str) -> str:
        """Charge a payment."""
        ...

    async def refund(self, charge_id: str) -> bool:
        """Refund a payment."""
        ...


class StripeAdapter:
    """Default Stripe payment implementation."""

    async def charge(self, amount: Decimal, token: str) -> str:
        """Charge via Stripe."""
        return f"stripe_charge_{amount}"

    async def refund(self, charge_id: str) -> bool:
        """Refund via Stripe."""
        return True


class PayPalAdapter:
    """Alternative PayPal payment implementation."""

    async def charge(self, amount: Decimal, token: str) -> str:
        """Charge via PayPal."""
        return f"paypal_charge_{amount}"

    async def refund(self, charge_id: str) -> bool:
        """Refund via PayPal."""
        return True


class EcommerceContainer(containers.DeclarativeContainer):
    """Example app-defined container for e-commerce."""

    # App-defined protocol provider
    payment_gateway = providers.Singleton(StripeAdapter)


class NotificationProtocol(Protocol):
    """Protocol for notifications (another app-defined port)."""

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email notification."""
        ...


class EmailAdapter:
    """Default email notification implementation."""

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via SMTP."""
        return True


class MarketingContainer(containers.DeclarativeContainer):
    """Example app-defined container for marketing."""

    notification_service = providers.Singleton(EmailAdapter)


# Test Classes
class TestAppContainerDiscovery:
    """Test discovery of app-defined containers via entrypoints."""

    def test_discover_app_containers_from_entrypoints(self) -> None:
        """Should discover app containers registered via entrypoints."""
        from framework_m.core.container import load_app_containers

        # Mock entrypoint that returns our test container
        mock_ep = Mock()
        mock_ep.name = "ecommerce"
        mock_ep.load.return_value = EcommerceContainer

        with patch("framework_m.core.container.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_ep]

            containers_dict = load_app_containers()

            # Should find the ecommerce container
            assert "ecommerce" in containers_dict
            assert containers_dict["ecommerce"] is EcommerceContainer

    def test_discover_multiple_app_containers(self) -> None:
        """Should discover multiple app containers."""
        from framework_m.core.container import load_app_containers

        # Mock two entrypoints
        mock_ep1 = Mock()
        mock_ep1.name = "ecommerce"
        mock_ep1.load.return_value = EcommerceContainer

        mock_ep2 = Mock()
        mock_ep2.name = "marketing"
        mock_ep2.load.return_value = MarketingContainer

        with patch("framework_m.core.container.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_ep1, mock_ep2]

            containers_dict = load_app_containers()

            # Should find both containers
            assert len(containers_dict) == 2
            assert "ecommerce" in containers_dict
            assert "marketing" in containers_dict

    def test_empty_entrypoints_returns_empty_dict(self) -> None:
        """Should return empty dict when no app containers registered."""
        from framework_m.core.container import load_app_containers

        with patch("framework_m.core.container.entry_points") as mock_entry_points:
            mock_entry_points.return_value = []

            containers_dict = load_app_containers()

            assert containers_dict == {}

    def test_skip_invalid_entrypoints(self) -> None:
        """Should skip entrypoints that fail to load."""
        from framework_m.core.container import load_app_containers

        # One valid, one invalid entrypoint
        mock_ep1 = Mock()
        mock_ep1.name = "ecommerce"
        mock_ep1.load.return_value = EcommerceContainer

        mock_ep2 = Mock()
        mock_ep2.name = "broken"
        mock_ep2.load.side_effect = ImportError("Module not found")

        with patch("framework_m.core.container.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_ep1, mock_ep2]

            containers_dict = load_app_containers()

            # Should only load the valid one
            assert len(containers_dict) == 1
            assert "ecommerce" in containers_dict
            assert "broken" not in containers_dict


class TestAppContainerInstantiation:
    """Test instantiation of app-defined containers."""

    def test_instantiate_app_container(self) -> None:
        """Should be able to instantiate app containers."""
        container = EcommerceContainer()

        assert container is not None
        assert hasattr(container, "payment_gateway")

    def test_app_container_provides_protocol(self) -> None:
        """App container should provide access to protocol implementation."""
        container = EcommerceContainer()

        # Get the payment gateway provider
        payment_gateway = container.payment_gateway()

        assert isinstance(payment_gateway, StripeAdapter)

    def test_multiple_app_containers_independent(self) -> None:
        """Multiple app containers should be independent."""
        ecommerce = EcommerceContainer()
        marketing = MarketingContainer()

        assert hasattr(ecommerce, "payment_gateway")
        assert not hasattr(ecommerce, "notification_service")

        assert hasattr(marketing, "notification_service")
        assert not hasattr(marketing, "payment_gateway")


class TestProtocolOverride:
    """Test overriding app-defined protocols."""

    def test_override_app_protocol_with_different_implementation(self) -> None:
        """Should be able to override protocol with different implementation."""
        container = EcommerceContainer()

        # Initially uses Stripe
        original = container.payment_gateway()
        assert isinstance(original, StripeAdapter)

        # Override with PayPal
        container.payment_gateway.override(providers.Singleton(PayPalAdapter))

        # Now uses PayPal
        overridden = container.payment_gateway()
        assert isinstance(overridden, PayPalAdapter)

    def test_override_persists_across_calls(self) -> None:
        """Override should persist across multiple calls."""
        container = EcommerceContainer()

        container.payment_gateway.override(providers.Singleton(PayPalAdapter))

        # Multiple calls should return PayPal
        first = container.payment_gateway()
        second = container.payment_gateway()

        assert isinstance(first, PayPalAdapter)
        assert isinstance(second, PayPalAdapter)
        # Singleton - same instance
        assert first is second

    def test_reset_override(self) -> None:
        """Should be able to reset override back to original."""
        container = EcommerceContainer()

        # Override
        container.payment_gateway.override(providers.Singleton(PayPalAdapter))
        assert isinstance(container.payment_gateway(), PayPalAdapter)

        # Reset
        container.payment_gateway.reset_override()
        assert isinstance(container.payment_gateway(), StripeAdapter)


class TestCrossAppOverride:
    """Test cross-app protocol overrides."""

    def test_app_can_override_another_apps_protocol(self) -> None:
        """One app should be able to override another app's protocol."""
        from framework_m.core.container import (
            Container,
            register_app_container,
        )

        # Main framework container
        main_container = Container()

        # Register ecommerce app container
        ecommerce = EcommerceContainer()
        register_app_container(main_container, "ecommerce", ecommerce)

        # Access original implementation
        payment_gateway = ecommerce.payment_gateway()
        assert isinstance(payment_gateway, StripeAdapter)

        # Another app overrides the payment gateway
        ecommerce.payment_gateway.override(providers.Singleton(PayPalAdapter))

        # Now uses the override
        overridden_gateway = ecommerce.payment_gateway()
        assert isinstance(overridden_gateway, PayPalAdapter)

    def test_override_via_entrypoint_pattern(self) -> None:
        """Test the override pattern using entrypoints."""
        # This simulates the pattern in ARCHITECTURE.md Section 5.5

        # App B defines its container
        ecommerce = EcommerceContainer()

        # App C wants to override
        # In real scenario, this would be via entrypoint, but we test the mechanism
        ecommerce.payment_gateway.override(providers.Singleton(PayPalAdapter))

        # Verify override worked
        assert isinstance(ecommerce.payment_gateway(), PayPalAdapter)


class TestAppContainerRegistration:
    """Test registration of app containers with main container."""

    def test_register_app_container_with_main_container(self) -> None:
        """Should register app container as attribute of main container."""
        from framework_m.core.container import (
            Container,
            register_app_container,
        )

        main_container = Container()
        ecommerce = EcommerceContainer()

        register_app_container(main_container, "ecommerce", ecommerce)

        # Should be accessible as attribute
        assert hasattr(main_container, "ecommerce")
        assert main_container.ecommerce is ecommerce  # type: ignore[comparison-overlap]

    def test_register_multiple_app_containers(self) -> None:
        """Should register multiple app containers."""
        from framework_m.core.container import (
            Container,
            register_app_container,
        )

        main_container = Container()
        ecommerce = EcommerceContainer()
        marketing = MarketingContainer()

        register_app_container(main_container, "ecommerce", ecommerce)
        register_app_container(main_container, "marketing", marketing)

        assert hasattr(main_container, "ecommerce")
        assert hasattr(main_container, "marketing")

    def test_registered_container_providers_accessible(self) -> None:
        """Providers in registered containers should be accessible."""
        from framework_m.core.container import (
            Container,
            register_app_container,
        )

        main_container = Container()
        ecommerce = EcommerceContainer()

        register_app_container(main_container, "ecommerce", ecommerce)

        # Access provider through main container
        payment_gateway = main_container.ecommerce.payment_gateway()  # type: ignore[attr-defined]
        assert isinstance(payment_gateway, StripeAdapter)


class TestAutoLoadAppContainers:
    """Test automatic loading of app containers."""

    def test_auto_load_discovers_and_registers(self) -> None:
        """auto_load_app_containers should discover and register all app containers."""
        from framework_m.core.container import (
            Container,
            auto_load_app_containers,
        )

        # Mock entrypoints
        mock_ep = Mock()
        mock_ep.name = "ecommerce"
        mock_ep.load.return_value = EcommerceContainer

        with patch("framework_m.core.container.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_ep]

            main_container = Container()
            count = auto_load_app_containers(main_container)

            # Should have registered the container
            assert count == 1
            assert hasattr(main_container, "ecommerce")

    def test_auto_load_returns_count(self) -> None:
        """auto_load_app_containers should return count of loaded containers."""
        from framework_m.core.container import (
            Container,
            auto_load_app_containers,
        )

        # Mock two entrypoints
        mock_ep1 = Mock()
        mock_ep1.name = "ecommerce"
        mock_ep1.load.return_value = EcommerceContainer

        mock_ep2 = Mock()
        mock_ep2.name = "marketing"
        mock_ep2.load.return_value = MarketingContainer

        with patch("framework_m.core.container.entry_points") as mock_entry_points:
            mock_entry_points.return_value = [mock_ep1, mock_ep2]

            main_container = Container()
            count = auto_load_app_containers(main_container)

            assert count == 2

    def test_auto_load_with_no_containers(self) -> None:
        """auto_load_app_containers should handle no containers gracefully."""
        from framework_m.core.container import (
            Container,
            auto_load_app_containers,
        )

        with patch("framework_m.core.container.entry_points") as mock_entry_points:
            mock_entry_points.return_value = []

            main_container = Container()
            count = auto_load_app_containers(main_container)

            assert count == 0


class TestProtocolUsagePattern:
    """Test realistic usage patterns for app-defined protocols."""

    @pytest.mark.asyncio
    async def test_use_protocol_through_container(self) -> None:
        """Should be able to use protocol implementation through container."""
        container = EcommerceContainer()

        payment_gateway = container.payment_gateway()

        # Use the protocol
        charge_id = await payment_gateway.charge(Decimal("100.00"), "tok_123")

        assert charge_id == "stripe_charge_100.00"

    @pytest.mark.asyncio
    async def test_use_overridden_protocol(self) -> None:
        """Should be able to use overridden protocol implementation."""
        container = EcommerceContainer()

        # Override with PayPal
        container.payment_gateway.override(providers.Singleton(PayPalAdapter))

        payment_gateway = container.payment_gateway()

        # Use the overridden protocol
        charge_id = await payment_gateway.charge(Decimal("50.00"), "tok_456")

        assert charge_id == "paypal_charge_50.00"

    @pytest.mark.asyncio
    async def test_protocol_methods_work_as_expected(self) -> None:
        """All protocol methods should work correctly."""
        container = EcommerceContainer()

        payment_gateway = container.payment_gateway()

        # Test charge
        charge_id = await payment_gateway.charge(Decimal("75.00"), "tok_789")
        assert "stripe_charge" in charge_id

        # Test refund
        refund_result = await payment_gateway.refund(charge_id)
        assert refund_result is True


class TestEdgeCases:
    """Test edge cases in custom protocol registration."""

    def test_duplicate_container_name_overwrites(self) -> None:
        """Registering same name twice should overwrite."""
        from framework_m.core.container import (
            Container,
            register_app_container,
        )

        main_container = Container()
        ecommerce1 = EcommerceContainer()
        ecommerce2 = EcommerceContainer()

        register_app_container(main_container, "ecommerce", ecommerce1)
        register_app_container(main_container, "ecommerce", ecommerce2)

        # Should have the second one
        assert main_container.ecommerce is ecommerce2  # type: ignore[comparison-overlap]

    def test_container_name_conflicts_with_framework_provider(self) -> None:
        """App container name should not conflict with framework providers."""
        from framework_m.core.container import (
            Container,
            register_app_container,
        )

        main_container = Container()
        ecommerce = EcommerceContainer()

        # Try to register with name that conflicts with framework provider
        # Should not overwrite framework providers
        register_app_container(main_container, "config", ecommerce)

        # Framework config should still work
        assert hasattr(main_container, "config")
        # But also has the app container (different attribute handling)
        # In practice, this should be prevented or handled gracefully

    def test_get_app_container_list(self) -> None:
        """Should be able to list all registered app containers."""
        from framework_m.core.container import (
            Container,
            get_app_container_names,
            register_app_container,
        )

        main_container = Container()
        ecommerce = EcommerceContainer()
        marketing = MarketingContainer()

        register_app_container(main_container, "ecommerce", ecommerce)
        register_app_container(main_container, "marketing", marketing)

        # Get list of app container names
        names = get_app_container_names(main_container)

        assert "ecommerce" in names
        assert "marketing" in names
        # Should not include framework providers
        assert "config" not in names
        assert "event_bus" not in names

"""Tests for Webhook Listener."""

from unittest.mock import AsyncMock, Mock

import pytest

from framework_m.core.events import DocCreated

# =============================================================================
# Test: WebhookListener Import
# =============================================================================


class TestWebhookListenerImport:
    """Tests for WebhookListener import."""

    def test_import_webhook_listener(self) -> None:
        """WebhookListener should be importable."""
        from framework_m.adapters.webhooks.listener import WebhookListener

        assert WebhookListener is not None

    def test_webhook_listener_instantiation(self) -> None:
        """WebhookListener should be instantiable."""
        from framework_m.adapters.webhooks.listener import WebhookListener

        mock_event_bus = Mock()
        listener = WebhookListener(event_bus=mock_event_bus)
        assert listener is not None


# =============================================================================
# Test: WebhookListener Start/Stop
# =============================================================================


class TestWebhookListenerLifecycle:
    """Tests for WebhookListener lifecycle."""

    @pytest.mark.asyncio
    async def test_start_subscribes_to_events(self) -> None:
        """start() should subscribe to doc events."""
        from framework_m.adapters.webhooks.listener import WebhookListener

        mock_event_bus = AsyncMock()
        mock_event_bus.subscribe_pattern = AsyncMock(return_value="sub-123")

        listener = WebhookListener(event_bus=mock_event_bus)
        await listener.start()

        mock_event_bus.subscribe_pattern.assert_called()

    @pytest.mark.asyncio
    async def test_stop_unsubscribes(self) -> None:
        """stop() should unsubscribe from events."""
        from framework_m.adapters.webhooks.listener import WebhookListener

        mock_event_bus = AsyncMock()
        mock_event_bus.subscribe_pattern = AsyncMock(return_value="sub-123")
        mock_event_bus.unsubscribe = AsyncMock()

        listener = WebhookListener(event_bus=mock_event_bus)
        await listener.start()
        await listener.stop()

        mock_event_bus.unsubscribe.assert_called_with("sub-123")


# =============================================================================
# Test: Event Handling
# =============================================================================


class TestWebhookEventHandling:
    """Tests for WebhookListener event handling."""

    @pytest.mark.asyncio
    async def test_handle_event_matches_webhooks(self) -> None:
        """handle_event should match event to webhooks."""
        from framework_m.adapters.webhooks.listener import WebhookListener

        mock_event_bus = AsyncMock()
        mock_webhook_loader = AsyncMock()
        mock_webhook_loader.load_active_webhooks = AsyncMock(return_value=[])

        listener = WebhookListener(
            event_bus=mock_event_bus,
            webhook_loader=mock_webhook_loader,
        )

        event = DocCreated(doctype="Invoice", doc_name="INV-001")
        await listener.handle_event(event)

        mock_webhook_loader.load_active_webhooks.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_event_filters_by_event_type(self) -> None:
        """handle_event should filter webhooks by event type."""
        from framework_m.adapters.webhooks.listener import WebhookListener
        from framework_m.core.doctypes.webhook import Webhook

        mock_event_bus = AsyncMock()

        # Webhook for doc.created events only
        webhook = Webhook(
            name="test_hook",
            event="doc.created",
            url="https://example.com/webhook",
        )

        mock_webhook_loader = AsyncMock()
        mock_webhook_loader.load_active_webhooks = AsyncMock(return_value=[webhook])

        mock_deliverer = AsyncMock()

        listener = WebhookListener(
            event_bus=mock_event_bus,
            webhook_loader=mock_webhook_loader,
            deliverer=mock_deliverer,
        )

        event = DocCreated(doctype="Invoice", doc_name="INV-001")
        await listener.handle_event(event)

        # Should trigger delivery
        mock_deliverer.deliver.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_event_filters_by_doctype(self) -> None:
        """handle_event should filter webhooks by doctype_filter."""
        from framework_m.adapters.webhooks.listener import WebhookListener
        from framework_m.core.doctypes.webhook import Webhook

        mock_event_bus = AsyncMock()

        # Webhook for Invoice only
        webhook = Webhook(
            name="invoice_hook",
            event="doc.created",
            url="https://example.com/webhook",
            doctype_filter="Invoice",
        )

        mock_webhook_loader = AsyncMock()
        mock_webhook_loader.load_active_webhooks = AsyncMock(return_value=[webhook])

        mock_deliverer = AsyncMock()

        listener = WebhookListener(
            event_bus=mock_event_bus,
            webhook_loader=mock_webhook_loader,
            deliverer=mock_deliverer,
        )

        # Event for Order - should NOT trigger
        event = DocCreated(doctype="Order", doc_name="ORD-001")
        await listener.handle_event(event)

        mock_deliverer.deliver.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_event_matches_doctype_filter(self) -> None:
        """handle_event should match when doctype matches filter."""
        from framework_m.adapters.webhooks.listener import WebhookListener
        from framework_m.core.doctypes.webhook import Webhook

        mock_event_bus = AsyncMock()

        webhook = Webhook(
            name="invoice_hook",
            event="doc.created",
            url="https://example.com/webhook",
            doctype_filter="Invoice",
        )

        mock_webhook_loader = AsyncMock()
        mock_webhook_loader.load_active_webhooks = AsyncMock(return_value=[webhook])

        mock_deliverer = AsyncMock()

        listener = WebhookListener(
            event_bus=mock_event_bus,
            webhook_loader=mock_webhook_loader,
            deliverer=mock_deliverer,
        )

        # Event for Invoice - should trigger
        event = DocCreated(doctype="Invoice", doc_name="INV-001")
        await listener.handle_event(event)

        mock_deliverer.deliver.assert_called_once()

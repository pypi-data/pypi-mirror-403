"""Tests for Webhook Delivery."""

import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework_m.core.doctypes.webhook import Webhook
from framework_m.core.events import DocCreated

# =============================================================================
# Test: HttpWebhookDeliverer Import
# =============================================================================


class TestHttpWebhookDelivererImport:
    """Tests for HttpWebhookDeliverer import."""

    def test_import_http_webhook_deliverer(self) -> None:
        """HttpWebhookDeliverer should be importable."""
        from framework_m.adapters.webhooks.delivery import HttpWebhookDeliverer

        assert HttpWebhookDeliverer is not None

    def test_deliverer_instantiation(self) -> None:
        """HttpWebhookDeliverer should be instantiable."""
        from framework_m.adapters.webhooks.delivery import HttpWebhookDeliverer

        deliverer = HttpWebhookDeliverer()
        assert deliverer is not None


# =============================================================================
# Test: Signature Generation
# =============================================================================


class TestSignatureGeneration:
    """Tests for webhook signature generation."""

    def test_generate_signature_with_secret(self) -> None:
        """generate_signature should create HMAC-SHA256 signature."""
        from framework_m.adapters.webhooks.delivery import generate_signature

        payload = b'{"event": "test"}'
        secret = "my-secret-key"

        signature = generate_signature(payload, secret)

        # Verify it's a valid hex HMAC-SHA256
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        assert signature == expected

    def test_generate_signature_returns_sha256_prefix(self) -> None:
        """generate_signature should return hex string."""
        from framework_m.adapters.webhooks.delivery import generate_signature

        signature = generate_signature(b"test", "secret")

        # SHA256 hex is 64 characters
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)


# =============================================================================
# Test: Webhook Delivery
# =============================================================================


class TestHttpWebhookDelivery:
    """Tests for HTTP webhook delivery."""

    @pytest.mark.asyncio
    async def test_deliver_makes_http_request(self) -> None:
        """deliver should make HTTP POST request."""
        from framework_m.adapters.webhooks.delivery import HttpWebhookDeliverer

        webhook = Webhook(
            name="test_hook",
            event="doc.created",
            url="https://example.com/webhook",
        )
        event = DocCreated(doctype="Invoice", doc_name="INV-001")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            deliverer = HttpWebhookDeliverer()
            await deliverer.deliver(webhook, event)

            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_deliver_uses_webhook_method(self) -> None:
        """deliver should use webhook's HTTP method."""
        from framework_m.adapters.webhooks.delivery import HttpWebhookDeliverer

        webhook = Webhook(
            name="test_hook",
            event="doc.updated",
            url="https://example.com/webhook",
            method="PUT",
        )
        event = DocCreated(doctype="Invoice", doc_name="INV-001")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            deliverer = HttpWebhookDeliverer()
            await deliverer.deliver(webhook, event)

            call_kwargs = mock_client.request.call_args[1]
            assert call_kwargs.get("method") == "PUT"

    @pytest.mark.asyncio
    async def test_deliver_includes_signature_header(self) -> None:
        """deliver should include X-Webhook-Signature header when secret set."""
        from framework_m.adapters.webhooks.delivery import HttpWebhookDeliverer

        webhook = Webhook(
            name="test_hook",
            event="doc.created",
            url="https://example.com/webhook",
            secret="my-secret",
        )
        event = DocCreated(doctype="Invoice", doc_name="INV-001")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            deliverer = HttpWebhookDeliverer()
            await deliverer.deliver(webhook, event)

            call_kwargs = mock_client.request.call_args[1]
            headers = call_kwargs.get("headers", {})
            assert "X-Webhook-Signature" in headers

    @pytest.mark.asyncio
    async def test_deliver_includes_custom_headers(self) -> None:
        """deliver should include webhook's custom headers."""
        from framework_m.adapters.webhooks.delivery import HttpWebhookDeliverer

        webhook = Webhook(
            name="test_hook",
            event="doc.created",
            url="https://example.com/webhook",
            headers={"X-Custom": "value"},
        )
        event = DocCreated(doctype="Invoice", doc_name="INV-001")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            deliverer = HttpWebhookDeliverer()
            await deliverer.deliver(webhook, event)

            call_kwargs = mock_client.request.call_args[1]
            headers = call_kwargs.get("headers", {})
            assert headers.get("X-Custom") == "value"


# =============================================================================
# Test: Retry Logic
# =============================================================================


class TestRetryLogic:
    """Tests for retry logic."""

    def test_default_max_retries_is_3(self) -> None:
        """Default max retries should be 3."""
        from framework_m.adapters.webhooks.delivery import HttpWebhookDeliverer

        deliverer = HttpWebhookDeliverer()
        assert deliverer.max_retries == 3

    def test_default_timeout_is_30(self) -> None:
        """Default timeout should be 30 seconds."""
        from framework_m.adapters.webhooks.delivery import HttpWebhookDeliverer

        deliverer = HttpWebhookDeliverer()
        assert deliverer.timeout == 30.0

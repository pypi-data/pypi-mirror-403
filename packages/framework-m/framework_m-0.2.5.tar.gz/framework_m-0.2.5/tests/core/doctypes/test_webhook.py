"""Tests for Webhook DocType."""


# =============================================================================
# Test: Webhook DocType Import
# =============================================================================


class TestWebhookImport:
    """Tests for Webhook DocType import."""

    def test_import_webhook(self) -> None:
        """Webhook should be importable from doctypes."""
        from framework_m.core.doctypes.webhook import Webhook

        assert Webhook is not None

    def test_webhook_in_all_exports(self) -> None:
        """Webhook should be in __all__."""
        from framework_m.core.doctypes import webhook

        assert "Webhook" in webhook.__all__


# =============================================================================
# Test: Webhook Creation
# =============================================================================


class TestWebhookCreation:
    """Tests for Webhook DocType creation."""

    def test_create_webhook_with_required_fields(self) -> None:
        """Webhook should be creatable with required fields."""
        from framework_m.core.doctypes.webhook import Webhook

        webhook = Webhook(
            name="order_created_hook",
            event="doc.created",
            url="https://example.com/webhook",
        )

        assert webhook.name == "order_created_hook"
        assert webhook.event == "doc.created"
        assert webhook.url == "https://example.com/webhook"

    def test_webhook_default_method_is_post(self) -> None:
        """Webhook method should default to POST."""
        from framework_m.core.doctypes.webhook import Webhook

        webhook = Webhook(
            name="test_hook",
            event="doc.created",
            url="https://example.com/webhook",
        )

        assert webhook.method == "POST"

    def test_webhook_default_enabled_is_true(self) -> None:
        """Webhook enabled should default to True."""
        from framework_m.core.doctypes.webhook import Webhook

        webhook = Webhook(
            name="test_hook",
            event="doc.created",
            url="https://example.com/webhook",
        )

        assert webhook.enabled is True

    def test_webhook_default_headers_is_empty_dict(self) -> None:
        """Webhook headers should default to empty dict."""
        from framework_m.core.doctypes.webhook import Webhook

        webhook = Webhook(
            name="test_hook",
            event="doc.created",
            url="https://example.com/webhook",
        )

        assert webhook.headers == {}


# =============================================================================
# Test: Webhook Optional Fields
# =============================================================================


class TestWebhookOptionalFields:
    """Tests for Webhook optional fields."""

    def test_webhook_with_doctype_filter(self) -> None:
        """Webhook should accept doctype_filter."""
        from framework_m.core.doctypes.webhook import Webhook

        webhook = Webhook(
            name="invoice_hook",
            event="doc.created",
            url="https://example.com/webhook",
            doctype_filter="Invoice",
        )

        assert webhook.doctype_filter == "Invoice"

    def test_webhook_with_custom_headers(self) -> None:
        """Webhook should accept custom headers."""
        from framework_m.core.doctypes.webhook import Webhook

        webhook = Webhook(
            name="test_hook",
            event="doc.created",
            url="https://example.com/webhook",
            headers={"X-Custom-Header": "value"},
        )

        assert webhook.headers == {"X-Custom-Header": "value"}

    def test_webhook_with_secret(self) -> None:
        """Webhook should accept secret for signature verification."""
        from framework_m.core.doctypes.webhook import Webhook

        webhook = Webhook(
            name="test_hook",
            event="doc.created",
            url="https://example.com/webhook",
            secret="my-secret-key",
        )

        assert webhook.secret == "my-secret-key"

    def test_webhook_with_put_method(self) -> None:
        """Webhook should accept PUT method."""
        from framework_m.core.doctypes.webhook import Webhook

        webhook = Webhook(
            name="test_hook",
            event="doc.updated",
            url="https://example.com/webhook",
            method="PUT",
        )

        assert webhook.method == "PUT"


# =============================================================================
# Test: Webhook Meta Configuration
# =============================================================================


class TestWebhookMeta:
    """Tests for Webhook Meta configuration."""

    def test_webhook_has_meta_class(self) -> None:
        """Webhook should have Meta class."""
        from framework_m.core.doctypes.webhook import Webhook

        assert hasattr(Webhook, "Meta")

    def test_webhook_requires_auth(self) -> None:
        """Webhook should require authentication."""
        from framework_m.core.doctypes.webhook import Webhook

        assert Webhook.Meta.requires_auth is True

    def test_webhook_applies_rls(self) -> None:
        """Webhook should apply row-level security."""
        from framework_m.core.doctypes.webhook import Webhook

        assert Webhook.Meta.apply_rls is True

    def test_webhook_has_permissions(self) -> None:
        """Webhook should define permissions."""
        from framework_m.core.doctypes.webhook import Webhook

        assert "read" in Webhook.Meta.permissions
        assert "write" in Webhook.Meta.permissions
        assert "create" in Webhook.Meta.permissions
        assert "delete" in Webhook.Meta.permissions

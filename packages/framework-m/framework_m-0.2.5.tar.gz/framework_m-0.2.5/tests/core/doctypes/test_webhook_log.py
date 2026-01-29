"""Tests for WebhookLog DocType."""

from datetime import UTC, datetime

# =============================================================================
# Test: WebhookLog DocType Import
# =============================================================================


class TestWebhookLogImport:
    """Tests for WebhookLog DocType import."""

    def test_import_webhook_log(self) -> None:
        """WebhookLog should be importable from doctypes."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        assert WebhookLog is not None

    def test_webhook_log_in_all_exports(self) -> None:
        """WebhookLog should be in __all__."""
        from framework_m.core.doctypes import webhook_log

        assert "WebhookLog" in webhook_log.__all__


# =============================================================================
# Test: WebhookLog Creation
# =============================================================================


class TestWebhookLogCreation:
    """Tests for WebhookLog DocType creation."""

    def test_create_webhook_log_with_required_fields(self) -> None:
        """WebhookLog should be creatable with required fields."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        log = WebhookLog(
            webhook="order_hook",
            event="doc.created",
            status="success",
            response_code=200,
        )

        assert log.webhook == "order_hook"
        assert log.event == "doc.created"
        assert log.status == "success"
        assert log.response_code == 200

    def test_webhook_log_has_auto_timestamp(self) -> None:
        """WebhookLog should auto-generate timestamp."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        before = datetime.now(UTC)
        log = WebhookLog(
            webhook="test_hook",
            event="doc.created",
            status="success",
            response_code=200,
        )
        after = datetime.now(UTC)

        assert log.timestamp is not None
        assert before <= log.timestamp <= after


# =============================================================================
# Test: WebhookLog Optional Fields
# =============================================================================


class TestWebhookLogOptionalFields:
    """Tests for WebhookLog optional fields."""

    def test_webhook_log_with_response_body(self) -> None:
        """WebhookLog should accept response_body."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        log = WebhookLog(
            webhook="test_hook",
            event="doc.created",
            status="success",
            response_code=200,
            response_body='{"received": true}',
        )

        assert log.response_body == '{"received": true}'

    def test_webhook_log_with_error(self) -> None:
        """WebhookLog should accept error message."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        log = WebhookLog(
            webhook="test_hook",
            event="doc.created",
            status="failed",
            response_code=500,
            error="Connection timeout",
        )

        assert log.error == "Connection timeout"

    def test_webhook_log_default_response_body_is_none(self) -> None:
        """WebhookLog response_body should default to None."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        log = WebhookLog(
            webhook="test_hook",
            event="doc.created",
            status="success",
            response_code=200,
        )

        assert log.response_body is None

    def test_webhook_log_default_error_is_none(self) -> None:
        """WebhookLog error should default to None."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        log = WebhookLog(
            webhook="test_hook",
            event="doc.created",
            status="success",
            response_code=200,
        )

        assert log.error is None


# =============================================================================
# Test: WebhookLog Status Values
# =============================================================================


class TestWebhookLogStatus:
    """Tests for WebhookLog status values."""

    def test_webhook_log_success_status(self) -> None:
        """WebhookLog should accept 'success' status."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        log = WebhookLog(
            webhook="test_hook",
            event="doc.created",
            status="success",
            response_code=200,
        )

        assert log.status == "success"

    def test_webhook_log_failed_status(self) -> None:
        """WebhookLog should accept 'failed' status."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        log = WebhookLog(
            webhook="test_hook",
            event="doc.created",
            status="failed",
            response_code=500,
        )

        assert log.status == "failed"


# =============================================================================
# Test: WebhookLog Meta Configuration
# =============================================================================


class TestWebhookLogMeta:
    """Tests for WebhookLog Meta configuration."""

    def test_webhook_log_has_meta_class(self) -> None:
        """WebhookLog should have Meta class."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        assert hasattr(WebhookLog, "Meta")

    def test_webhook_log_requires_auth(self) -> None:
        """WebhookLog should require authentication."""
        from framework_m.core.doctypes.webhook_log import WebhookLog

        assert WebhookLog.Meta.requires_auth is True

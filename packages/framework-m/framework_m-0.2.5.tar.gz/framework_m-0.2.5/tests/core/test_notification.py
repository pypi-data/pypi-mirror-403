"""Tests for Notification DocType.

Tests cover:
- Notification model creation
- Field validation
- Meta configuration
"""

from datetime import UTC

from framework_m.core.doctypes.notification import Notification, NotificationType

# =============================================================================
# Test: Import
# =============================================================================


class TestNotificationImport:
    """Tests for Notification import."""

    def test_import_notification(self) -> None:
        """Notification should be importable."""
        from framework_m.core.doctypes.notification import Notification

        assert Notification is not None

    def test_import_notification_type(self) -> None:
        """NotificationType should be importable."""
        from framework_m.core.doctypes.notification import NotificationType

        assert NotificationType is not None


# =============================================================================
# Test: Model Creation
# =============================================================================


class TestNotificationCreation:
    """Tests for Notification model creation."""

    def test_create_minimal(self) -> None:
        """Notification should work with required fields only."""
        notif = Notification(
            user_id="user-001",
            subject="Test Subject",
            message="Test message",
        )

        assert notif.user_id == "user-001"
        assert notif.subject == "Test Subject"
        assert notif.message == "Test message"
        assert notif.read is False

    def test_create_with_document_reference(self) -> None:
        """Notification should accept document reference."""
        notif = Notification(
            user_id="user-001",
            subject="Invoice Approved",
            message="Your invoice has been approved.",
            doctype="Invoice",
            document_id="INV-001",
        )

        assert notif.doctype == "Invoice"
        assert notif.document_id == "INV-001"

    def test_default_notification_type(self) -> None:
        """Notification should default to info type."""
        notif = Notification(
            user_id="user-001",
            subject="Test",
            message="Test",
        )

        assert notif.notification_type == NotificationType.INFO

    def test_custom_notification_type(self) -> None:
        """Notification should accept custom type."""
        notif = Notification(
            user_id="user-001",
            subject="Error",
            message="Something failed",
            notification_type=NotificationType.ERROR,
        )

        assert notif.notification_type == NotificationType.ERROR

    def test_timestamp_is_utc(self) -> None:
        """Notification timestamp should be UTC."""
        notif = Notification(
            user_id="user-001",
            subject="Test",
            message="Test",
        )

        assert notif.timestamp.tzinfo is not None
        assert notif.timestamp.tzinfo == UTC


# =============================================================================
# Test: NotificationType Constants
# =============================================================================


class TestNotificationType:
    """Tests for NotificationType constants."""

    def test_info_type(self) -> None:
        """INFO type should be 'info'."""
        assert NotificationType.INFO == "info"

    def test_all_types_defined(self) -> None:
        """All expected types should be defined."""
        expected = [
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "MENTION",
            "ASSIGNMENT",
            "SHARE",
        ]
        for type_name in expected:
            assert hasattr(NotificationType, type_name)


# =============================================================================
# Test: Meta Configuration
# =============================================================================


class TestNotificationMeta:
    """Tests for Meta class configuration."""

    def test_meta_table_name(self) -> None:
        """Meta should have correct table_name."""
        assert Notification.Meta.table_name == "notifications"

    def test_meta_requires_auth(self) -> None:
        """Meta should require authentication."""
        assert Notification.Meta.requires_auth is True

    def test_meta_rls_enabled(self) -> None:
        """Meta should apply RLS on user_id."""
        assert Notification.Meta.apply_rls is True
        assert Notification.Meta.rls_field == "user_id"

    def test_meta_all_can_read(self) -> None:
        """Meta should allow all to read (RLS limits to own)."""
        assert "All" in Notification.Meta.permissions["read"]

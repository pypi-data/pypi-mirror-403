"""Tests for ActivityLog DocType.

Tests cover:
- ActivityLog model creation
- Field validation
- Meta configuration
"""

from datetime import UTC

import pytest

from framework_m.core.doctypes.activity_log import ActivityLog

# =============================================================================
# Test: Import
# =============================================================================


class TestActivityLogImport:
    """Tests for ActivityLog import."""

    def test_import_activity_log(self) -> None:
        """ActivityLog should be importable."""
        from framework_m.core.doctypes.activity_log import ActivityLog

        assert ActivityLog is not None


# =============================================================================
# Test: Model Creation
# =============================================================================


class TestActivityLogCreation:
    """Tests for ActivityLog model creation."""

    def test_create_minimal(self) -> None:
        """ActivityLog should work with required fields only."""
        log = ActivityLog(
            user_id="user-001",
            action="create",
            doctype="Invoice",
            document_id="INV-001",
        )

        assert log.user_id == "user-001"
        assert log.action == "create"
        assert log.doctype == "Invoice"
        assert log.document_id == "INV-001"
        assert log.id is not None
        assert log.timestamp is not None

    def test_create_with_changes(self) -> None:
        """ActivityLog should accept changes dict."""
        log = ActivityLog(
            user_id="user-001",
            action="update",
            doctype="Invoice",
            document_id="INV-001",
            changes={"status": {"old": "draft", "new": "submitted"}},
        )

        assert log.changes is not None
        assert log.changes["status"]["old"] == "draft"
        assert log.changes["status"]["new"] == "submitted"

    def test_create_with_metadata(self) -> None:
        """ActivityLog should accept metadata dict."""
        log = ActivityLog(
            user_id="user-001",
            action="read",
            doctype="Invoice",
            document_id="INV-001",
            metadata={"request_id": "req-123", "ip": "192.168.1.1"},
        )

        assert log.metadata is not None
        assert log.metadata["request_id"] == "req-123"

    def test_timestamp_is_utc(self) -> None:
        """ActivityLog timestamp should be UTC."""
        log = ActivityLog(
            user_id="user-001",
            action="create",
            doctype="Todo",
            document_id="TODO-001",
        )

        assert log.timestamp.tzinfo is not None
        assert log.timestamp.tzinfo == UTC


# =============================================================================
# Test: Validation
# =============================================================================


class TestActivityLogValidation:
    """Tests for field validation."""

    def test_action_must_be_valid(self) -> None:
        """action should only accept create, read, update, delete."""
        # Valid actions
        for action in ["create", "read", "update", "delete"]:
            log = ActivityLog(
                user_id="user-001",
                action=action,
                doctype="Todo",
                document_id="TODO-001",
            )
            assert log.action == action

    def test_invalid_action_rejected(self) -> None:
        """Invalid action should raise validation error."""
        with pytest.raises(ValueError):
            ActivityLog(
                user_id="user-001",
                action="invalid",
                doctype="Todo",
                document_id="TODO-001",
            )

    def test_user_id_required(self) -> None:
        """user_id should be required."""
        with pytest.raises(ValueError):
            ActivityLog(
                user_id="",
                action="create",
                doctype="Todo",
                document_id="TODO-001",
            )


# =============================================================================
# Test: Meta Configuration
# =============================================================================


class TestActivityLogMeta:
    """Tests for Meta class configuration."""

    def test_meta_table_name(self) -> None:
        """Meta should have correct table_name."""
        assert ActivityLog.Meta.table_name == "activity_logs"

    def test_meta_requires_auth(self) -> None:
        """Meta should require authentication."""
        assert ActivityLog.Meta.requires_auth is True

    def test_meta_apply_rls(self) -> None:
        """Meta should apply RLS."""
        assert ActivityLog.Meta.apply_rls is True

    def test_meta_rls_field(self) -> None:
        """Meta should use user_id for RLS."""
        assert ActivityLog.Meta.rls_field == "user_id"

    def test_meta_permissions_read_only(self) -> None:
        """Meta should have read-only permissions (no write/delete)."""
        assert ActivityLog.Meta.permissions["write"] == []
        assert ActivityLog.Meta.permissions["delete"] == []

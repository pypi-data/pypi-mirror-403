"""Tests for ErrorLog DocType.

Tests cover:
- ErrorLog model creation
- Field validation
- Meta configuration
"""

from datetime import UTC

import pytest

from framework_m.core.doctypes.error_log import ErrorLog

# =============================================================================
# Test: Import
# =============================================================================


class TestErrorLogImport:
    """Tests for ErrorLog import."""

    def test_import_error_log(self) -> None:
        """ErrorLog should be importable."""
        from framework_m.core.doctypes.error_log import ErrorLog

        assert ErrorLog is not None


# =============================================================================
# Test: Model Creation
# =============================================================================


class TestErrorLogCreation:
    """Tests for ErrorLog model creation."""

    def test_create_minimal(self) -> None:
        """ErrorLog should work with required fields only."""
        log = ErrorLog(
            title="Test error",
            error_type="ValueError",
            error_message="Invalid value",
        )

        assert log.title == "Test error"
        assert log.error_type == "ValueError"
        assert log.error_message == "Invalid value"
        assert log.id is not None
        assert log.timestamp is not None

    def test_create_with_traceback(self) -> None:
        """ErrorLog should accept traceback."""
        log = ErrorLog(
            title="Test error",
            error_type="ValueError",
            error_message="Invalid value",
            traceback="Traceback (most recent call last):\n  File ...",
        )

        assert log.traceback is not None
        assert "Traceback" in log.traceback

    def test_create_with_request_context(self) -> None:
        """ErrorLog should accept request context."""
        log = ErrorLog(
            title="API error",
            error_type="HTTPException",
            error_message="Not found",
            request_url="/api/v1/users/123",
            user_id="user-001",
            request_id="req-abc-123",
        )

        assert log.request_url == "/api/v1/users/123"
        assert log.user_id == "user-001"
        assert log.request_id == "req-abc-123"

    def test_create_with_context_dict(self) -> None:
        """ErrorLog should accept context dict."""
        log = ErrorLog(
            title="Request failed",
            error_type="ValidationError",
            error_message="Invalid JSON",
            context={"content_type": "application/json", "method": "POST"},
        )

        assert log.context is not None
        assert log.context["content_type"] == "application/json"

    def test_timestamp_is_utc(self) -> None:
        """ErrorLog timestamp should be UTC."""
        log = ErrorLog(
            title="Test",
            error_type="Exception",
            error_message="Test",
        )

        assert log.timestamp.tzinfo is not None
        assert log.timestamp.tzinfo == UTC


# =============================================================================
# Test: Validation
# =============================================================================


class TestErrorLogValidation:
    """Tests for field validation."""

    def test_title_max_length(self) -> None:
        """title should have max length 255."""
        long_title = "x" * 300
        with pytest.raises(ValueError):
            ErrorLog(
                title=long_title,
                error_type="Exception",
                error_message="Test",
            )


# =============================================================================
# Test: Meta Configuration
# =============================================================================


class TestErrorLogMeta:
    """Tests for Meta class configuration."""

    def test_meta_table_name(self) -> None:
        """Meta should have correct table_name."""
        assert ErrorLog.Meta.table_name == "error_logs"

    def test_meta_requires_auth(self) -> None:
        """Meta should require authentication."""
        assert ErrorLog.Meta.requires_auth is True

    def test_meta_no_rls(self) -> None:
        """Meta should not apply RLS (admin only)."""
        assert ErrorLog.Meta.apply_rls is False

    def test_meta_permissions_admin_only(self) -> None:
        """Meta should allow only System Manager to read."""
        assert "System Manager" in ErrorLog.Meta.permissions["read"]

    def test_meta_permissions_immutable(self) -> None:
        """Meta should have no write/delete permissions (immutable)."""
        assert ErrorLog.Meta.permissions["write"] == []
        assert ErrorLog.Meta.permissions["delete"] == []

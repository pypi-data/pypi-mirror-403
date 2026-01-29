"""ErrorLog DocType - System error tracking and debugging.

This module defines the ErrorLog DocType for Framework M's error logging system.

The ErrorLog DocType stores information about unhandled exceptions and errors:
- Exception type and message
- Full stack trace for debugging
- Request context (URL, user, request_id)
- Timestamp for correlation

Security:
- Only admins can view error logs
- Error logs are immutable (read-only after creation)
- Sensitive data should be redacted before logging

Example:
    log = ErrorLog(
        title="Database connection failed",
        error_type="ConnectionError",
        error_message="Could not connect to PostgreSQL",
        traceback="Traceback (most recent call last):\n  ...",
        request_url="/api/v1/users",
        user_id="user-001",
        request_id="req-abc-123",
    )
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class ErrorLog(BaseDocType):
    """Error log entry DocType.

    Stores information about system errors for debugging.
    Errors are captured by the global exception handler.

    Attributes:
        title: Short description of the error
        error_type: Exception class name (e.g., "ValueError")
        error_message: Full error message
        traceback: Stack trace for debugging
        request_url: URL that triggered the error
        user_id: User who triggered the error
        request_id: Request ID for correlation
        timestamp: When the error occurred
        context: Additional context (headers, params, etc.)

    Example:
        log = ErrorLog(
            title="Validation failed",
            error_type="ValidationError",
            error_message="Field 'email' is invalid",
        )
    """

    # Required fields
    title: str = Field(
        ...,
        description="Short description of the error",
        max_length=255,
    )

    error_type: str = Field(
        ...,
        description="Exception class name (e.g., ValueError)",
    )

    error_message: str = Field(
        ...,
        description="Full error message",
    )

    # Optional fields
    traceback: str | None = Field(
        default=None,
        description="Full stack trace for debugging",
    )

    request_url: str | None = Field(
        default=None,
        description="URL that triggered the error",
    )

    user_id: str | None = Field(
        default=None,
        description="User who triggered the error",
    )

    request_id: str | None = Field(
        default=None,
        description="Request ID for log correlation",
    )

    timestamp: datetime = Field(
        default_factory=lambda: __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
        description="When the error occurred (UTC)",
    )

    context: dict[str, Any] | None = Field(
        default=None,
        description="Additional context: headers, params, etc.",
    )

    class Meta:
        """DocType metadata."""

        table_name = "error_logs"
        requires_auth = True
        apply_rls = False  # Admins only, no RLS needed

        # Permissions - only admins can view, system can create
        permissions = {  # noqa: RUF012
            "read": ["System Manager"],
            "write": [],  # No updates allowed
            "create": ["System Manager"],  # Only system can create
            "delete": [],  # No deletions allowed
        }


__all__ = ["ErrorLog"]

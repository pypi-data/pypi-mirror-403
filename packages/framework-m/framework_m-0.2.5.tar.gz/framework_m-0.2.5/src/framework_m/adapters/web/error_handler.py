"""Error Logging Integration - Global exception handler.

This module provides a global exception handler for Framework M that:
- Catches all unhandled exceptions
- Creates ErrorLog entries for debugging
- Returns user-friendly error responses
- Logs to console in development mode

The handler integrates with Litestar's exception handling system.

Usage:
    from framework_m.adapters.web.error_handler import (
        create_error_handler,
        ErrorResponse,
    )

    # Register with Litestar app
    app = Litestar(
        exception_handlers={Exception: create_error_handler(debug=True)},
    )
"""

from __future__ import annotations

import traceback
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from litestar import Request, Response
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from pydantic import BaseModel, Field

from framework_m.core.doctypes.error_log import ErrorLog

# =============================================================================
# Response Models
# =============================================================================


class ErrorResponse(BaseModel):
    """User-friendly error response.

    Returned to clients when an unhandled exception occurs.
    Does not expose sensitive information in production.

    Attributes:
        error: User-friendly error message
        error_id: Unique ID for error correlation
        timestamp: When the error occurred
        detail: Optional detail (only in debug mode)
    """

    error: str = Field(description="User-friendly error message")
    error_id: str = Field(description="Unique ID for error correlation")
    timestamp: datetime = Field(description="When the error occurred")
    detail: str | None = Field(default=None, description="Error detail (debug only)")


# =============================================================================
# Error Handler
# =============================================================================


class ErrorHandler:
    """Global exception handler.

    Catches unhandled exceptions, logs them, and returns user-friendly responses.

    Attributes:
        debug: If True, include stack traces in responses
        log_to_console: If True, print errors to console

    Example:
        handler = ErrorHandler(debug=True)
        response = await handler.handle(request, exception)
    """

    def __init__(
        self,
        debug: bool = False,
        log_to_console: bool = True,
    ) -> None:
        """Initialize error handler.

        Args:
            debug: Include stack traces in responses
            log_to_console: Print errors to console
        """
        self._debug = debug
        self._log_to_console = log_to_console
        self._error_logs: list[ErrorLog] = []  # In-memory for testing

    async def handle(
        self,
        request: Request[Any, Any, Any],
        exception: Exception,
    ) -> Response[Any]:
        """Handle an unhandled exception.

        Creates an ErrorLog entry and returns a user-friendly response.

        Args:
            request: The request that caused the exception
            exception: The unhandled exception

        Returns:
            Response with ErrorResponse body
        """
        error_id = str(uuid4())
        now = datetime.now(UTC)

        # Extract exception info
        error_type = type(exception).__name__
        error_message = str(exception)
        tb = traceback.format_exc()

        # Extract request context
        request_url = str(request.url) if request else None
        request_id = request.headers.get("X-Request-ID") if request else None
        user_id = self._get_user_id(request)

        # Create ErrorLog entry
        error_log = ErrorLog(
            title=f"{error_type}: {error_message[:100]}",
            error_type=error_type,
            error_message=error_message,
            traceback=tb,
            request_url=request_url,
            user_id=user_id,
            request_id=request_id,
            timestamp=now,
            context=self._get_context(request),
        )

        # TODO: Persist to database via repository
        # await self._repository.save(error_log)
        self._error_logs.append(error_log)

        # Log to console
        if self._log_to_console:
            self._log_to_console_output(error_log)

        # Build response
        response_data = ErrorResponse(
            error="An internal error occurred. Please try again later.",
            error_id=error_id,
            timestamp=now,
            detail=f"{error_type}: {error_message}" if self._debug else None,
        )

        return Response(
            content=response_data.model_dump_json(),
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json",
        )

    def _get_user_id(self, request: Request[Any, Any, Any] | None) -> str | None:
        """Extract user ID from request."""
        if not request:
            return None
        # TODO: Get from auth context
        return request.headers.get("X-User-ID")

    def _get_context(self, request: Request[Any, Any, Any] | None) -> dict[str, Any]:
        """Extract context from request."""
        if not request:
            return {}
        return {
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None,
            "user_agent": request.headers.get("User-Agent"),
        }

    def _log_to_console_output(self, error_log: ErrorLog) -> None:
        """Log error to console."""
        print(f"\n{'=' * 60}")
        print(f"ERROR: {error_log.title}")
        print(f"Time: {error_log.timestamp}")
        print(f"URL: {error_log.request_url}")
        print(f"User: {error_log.user_id}")
        print(f"Request ID: {error_log.request_id}")
        print(f"\n{error_log.traceback}")
        print(f"{'=' * 60}\n")


def create_error_handler(
    debug: bool = False,
    log_to_console: bool = True,
) -> Any:
    """Create a Litestar-compatible exception handler.

    Args:
        debug: Include stack traces in responses
        log_to_console: Print errors to console

    Returns:
        Exception handler function for Litestar

    Example:
        app = Litestar(
            exception_handlers={Exception: create_error_handler(debug=True)},
        )
    """
    handler = ErrorHandler(debug=debug, log_to_console=log_to_console)

    async def exception_handler(
        request: Request[Any, Any, Any],
        exception: Exception,
    ) -> Response[Any]:
        return await handler.handle(request, exception)

    return exception_handler


__all__ = [
    "ErrorHandler",
    "ErrorResponse",
    "create_error_handler",
]

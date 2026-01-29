"""Tests for Error Handler.

Tests cover:
- ErrorHandler class
- ErrorResponse model
- create_error_handler factory
"""

from datetime import UTC
from unittest.mock import MagicMock

import pytest

from framework_m.adapters.web.error_handler import (
    ErrorHandler,
    ErrorResponse,
    create_error_handler,
)

# =============================================================================
# Test: Import
# =============================================================================


class TestErrorHandlerImport:
    """Tests for error handler imports."""

    def test_import_error_handler(self) -> None:
        """ErrorHandler should be importable."""
        from framework_m.adapters.web.error_handler import ErrorHandler

        assert ErrorHandler is not None

    def test_import_error_response(self) -> None:
        """ErrorResponse should be importable."""
        from framework_m.adapters.web.error_handler import ErrorResponse

        assert ErrorResponse is not None

    def test_import_create_error_handler(self) -> None:
        """create_error_handler should be importable."""
        from framework_m.adapters.web.error_handler import create_error_handler

        assert create_error_handler is not None


# =============================================================================
# Test: ErrorResponse Model
# =============================================================================


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_create_minimal(self) -> None:
        """ErrorResponse should work with required fields."""
        from datetime import datetime

        response = ErrorResponse(
            error="Something went wrong",
            error_id="err-123",
            timestamp=datetime.now(UTC),
        )

        assert response.error == "Something went wrong"
        assert response.error_id == "err-123"
        assert response.detail is None

    def test_create_with_detail(self) -> None:
        """ErrorResponse should accept detail field."""
        from datetime import datetime

        response = ErrorResponse(
            error="Internal error",
            error_id="err-456",
            timestamp=datetime.now(UTC),
            detail="ValueError: invalid input",
        )

        assert response.detail == "ValueError: invalid input"


# =============================================================================
# Test: ErrorHandler
# =============================================================================


def _create_mock_request() -> MagicMock:
    """Create a properly configured mock request."""
    mock_request = MagicMock()
    mock_url = MagicMock()
    mock_url.path = "/api/test"
    mock_url.query = ""
    mock_url.__str__ = lambda self: "http://localhost/api/test"
    mock_request.url = mock_url
    mock_request.method = "GET"
    mock_request.headers = {}
    return mock_request


class TestErrorHandler:
    """Tests for ErrorHandler class."""

    def test_init_default(self) -> None:
        """ErrorHandler should initialize with defaults."""
        handler = ErrorHandler()

        assert handler._debug is False
        assert handler._log_to_console is True

    def test_init_with_debug(self) -> None:
        """ErrorHandler should accept debug flag."""
        handler = ErrorHandler(debug=True)

        assert handler._debug is True

    @pytest.mark.asyncio
    async def test_handle_creates_error_log(self) -> None:
        """handle() should create ErrorLog entry."""
        handler = ErrorHandler(debug=True, log_to_console=False)

        mock_request = _create_mock_request()
        mock_request.headers = {"User-Agent": "TestAgent"}

        exception = ValueError("Test error")

        await handler.handle(mock_request, exception)

        assert len(handler._error_logs) == 1
        assert handler._error_logs[0].error_type == "ValueError"
        assert handler._error_logs[0].error_message == "Test error"

    @pytest.mark.asyncio
    async def test_handle_returns_response(self) -> None:
        """handle() should return Response with ErrorResponse body."""
        handler = ErrorHandler(debug=False, log_to_console=False)

        mock_request = _create_mock_request()
        exception = RuntimeError("Crash!")

        response = await handler.handle(mock_request, exception)

        assert response.status_code == 500
        # Check content contains error_id
        assert "error_id" in response.content

    @pytest.mark.asyncio
    async def test_handle_hides_detail_in_production(self) -> None:
        """handle() should not include detail when debug=False."""
        handler = ErrorHandler(debug=False, log_to_console=False)

        mock_request = _create_mock_request()
        exception = ValueError("Sensitive info")

        response = await handler.handle(mock_request, exception)

        # Detail should not be in response content
        assert "Sensitive info" not in response.content

    @pytest.mark.asyncio
    async def test_handle_includes_detail_in_debug(self) -> None:
        """handle() should include detail when debug=True."""
        handler = ErrorHandler(debug=True, log_to_console=False)

        mock_request = _create_mock_request()
        exception = ValueError("Debug info")

        response = await handler.handle(mock_request, exception)

        # Detail should be in response content
        assert "Debug info" in response.content


# =============================================================================
# Test: create_error_handler Factory
# =============================================================================


class TestCreateErrorHandler:
    """Tests for create_error_handler factory."""

    def test_returns_callable(self) -> None:
        """create_error_handler should return a callable."""
        handler = create_error_handler()

        assert callable(handler)

    def test_accepts_debug_flag(self) -> None:
        """create_error_handler should accept debug flag."""
        handler = create_error_handler(debug=True)

        assert callable(handler)

    @pytest.mark.asyncio
    async def test_handler_works(self) -> None:
        """Returned handler should work with exceptions."""
        handler = create_error_handler(debug=True, log_to_console=False)

        mock_request = _create_mock_request()
        response = await handler(mock_request, ValueError("Test"))

        assert response.status_code == 500

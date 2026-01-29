"""Tests for Request/Response DTOs.

Tests for the DTO classes in dtos.py.
"""

from framework_m.adapters.web.dtos import (
    ErrorResponse,
    PaginatedResponse,
    SuccessResponse,
)

# =============================================================================
# Tests for PaginatedResponse
# =============================================================================


class TestPaginatedResponse:
    """Tests for PaginatedResponse DTO."""

    def test_create_basic(self) -> None:
        """Should create with all required fields."""
        items = [{"id": "1"}, {"id": "2"}]
        response = PaginatedResponse[dict[str, str]](
            items=items,
            total=100,
            limit=20,
            offset=0,
            has_more=True,
        )
        assert response.items == items
        assert response.total == 100
        assert response.limit == 20
        assert response.offset == 0
        assert response.has_more is True

    def test_create_helper(self) -> None:
        """Should compute has_more automatically via create()."""
        items = [{"id": "1"}, {"id": "2"}]
        response = PaginatedResponse.create(
            items=items,
            total=100,
            limit=20,
            offset=0,
        )
        # has_more should be True: 0 + 2 < 100
        assert response.has_more is True

    def test_create_helper_no_more(self) -> None:
        """Should set has_more=False when at end."""
        items = [{"id": "99"}, {"id": "100"}]
        response = PaginatedResponse.create(
            items=items,
            total=100,
            limit=20,
            offset=98,
        )
        # has_more should be False: 98 + 2 >= 100
        assert response.has_more is False

    def test_empty_items(self) -> None:
        """Should handle empty items list."""
        response = PaginatedResponse[dict[str, str]].create(
            items=[],
            total=0,
            limit=20,
            offset=0,
        )
        assert response.items == []
        assert response.total == 0
        assert response.has_more is False

    def test_model_dump(self) -> None:
        """Should serialize to dict correctly."""
        items = [{"id": "1"}]
        response = PaginatedResponse[dict[str, str]](
            items=items,
            total=1,
            limit=20,
            offset=0,
            has_more=False,
        )
        data = response.model_dump()
        assert data["items"] == items
        assert data["total"] == 1
        assert data["has_more"] is False


# =============================================================================
# Tests for ErrorResponse
# =============================================================================


class TestErrorResponse:
    """Tests for ErrorResponse DTO."""

    def test_basic_error(self) -> None:
        """Should create with error and message."""
        response = ErrorResponse(
            error="ValidationError",
            message="Field 'email' is required",
        )
        assert response.error == "ValidationError"
        assert response.message == "Field 'email' is required"
        assert response.details is None

    def test_error_with_details(self) -> None:
        """Should include details when provided."""
        response = ErrorResponse(
            error="ValidationError",
            message="Invalid data",
            details={"field": "email", "constraint": "required"},
        )
        assert response.details == {"field": "email", "constraint": "required"}

    def test_model_dump(self) -> None:
        """Should serialize to dict correctly."""
        response = ErrorResponse(
            error="PermissionDenied",
            message="Access denied",
        )
        data = response.model_dump()
        assert data["error"] == "PermissionDenied"
        assert data["message"] == "Access denied"


# =============================================================================
# Tests for SuccessResponse
# =============================================================================


class TestSuccessResponse:
    """Tests for SuccessResponse DTO."""

    def test_basic_success(self) -> None:
        """Should default success to True."""
        response = SuccessResponse()
        assert response.success is True
        assert response.message is None
        assert response.data is None

    def test_with_message(self) -> None:
        """Should include message when provided."""
        response = SuccessResponse(message="Document created")
        assert response.message == "Document created"

    def test_with_data(self) -> None:
        """Should include data when provided."""
        response = SuccessResponse(data={"id": "123"})
        assert response.data == {"id": "123"}

    def test_model_dump(self) -> None:
        """Should serialize to dict correctly."""
        response = SuccessResponse(message="Done", data={"count": 5})
        data = response.model_dump()
        assert data["success"] is True
        assert data["message"] == "Done"
        assert data["data"] == {"count": 5}

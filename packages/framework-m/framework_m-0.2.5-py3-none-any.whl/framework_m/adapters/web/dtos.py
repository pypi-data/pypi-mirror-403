"""Request/Response DTOs for web API.

This module provides standardized Data Transfer Objects for API responses:
- PaginatedResponse: Generic paginated list response
- ErrorResponse: Standard error response format

These DTOs ensure consistent API response formats across all endpoints.

Example:
    # Paginated list response
    PaginatedResponse[Todo](
        items=[todo1, todo2],
        total=100,
        limit=20,
        offset=0,
        has_more=True,
    )

    # Error response
    ErrorResponse(
        error="ValidationError",
        message="Field 'email' is required",
        details={"field": "email"},
    )
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PaginatedResponse[T](BaseModel):
    """Paginated list response DTO.

    Provides a standardized format for paginated list endpoints.

    Attributes:
        items: List of items for current page
        total: Total count of items matching the query
        limit: Maximum items per page
        offset: Number of items skipped
        has_more: Whether more items exist beyond this page

    Example:
        >>> response = PaginatedResponse[dict[str, Any]](
        ...     items=[{"id": "1", "name": "Item 1"}],
        ...     total=100,
        ...     limit=20,
        ...     offset=0,
        ...     has_more=True,
        ... )
    """

    items: list[T] = Field(description="List of items for current page")
    total: int = Field(description="Total count of items matching the query")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")
    has_more: bool = Field(description="Whether more items exist beyond this page")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[T]:
        """Create a paginated response with computed has_more.

        Args:
            items: List of items for current page
            total: Total count of items
            limit: Maximum items per page
            offset: Number of items skipped

        Returns:
            PaginatedResponse with has_more computed
        """
        has_more = offset + len(items) < total
        return cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )


class ErrorResponse(BaseModel):
    """Standard error response DTO.

    Provides a consistent format for all API error responses.

    Attributes:
        error: Error type/code (e.g., "ValidationError", "PermissionDenied")
        message: Human-readable error message
        details: Optional additional error details

    Example:
        >>> error = ErrorResponse(
        ...     error="ValidationError",
        ...     message="Field 'email' is required",
        ...     details={"field": "email", "constraint": "required"},
        ... )
    """

    error: str = Field(description="Error type/code")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None, description="Optional additional error details"
    )


class SuccessResponse(BaseModel):
    """Standard success response DTO.

    Provides a consistent format for success responses.

    Attributes:
        success: Always True
        message: Optional success message
        data: Optional response data
    """

    success: bool = Field(default=True, description="Success indicator")
    message: str | None = Field(default=None, description="Optional success message")
    data: dict[str, Any] | None = Field(
        default=None, description="Optional response data"
    )


__all__ = ["ErrorResponse", "PaginatedResponse", "SuccessResponse"]

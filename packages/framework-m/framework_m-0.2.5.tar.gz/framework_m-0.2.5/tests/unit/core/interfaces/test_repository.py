"""Tests for RepositoryProtocol interface compliance."""

import inspect
from typing import TypeVar, get_type_hints
from uuid import UUID

from framework_m.core.interfaces.repository import (
    FilterOperator,
    FilterSpec,
    OrderDirection,
    OrderSpec,
    PaginatedResult,
    RepositoryProtocol,
)

T = TypeVar("T")


class TestFilterSpec:
    """Tests for FilterSpec model."""

    def test_filter_spec_creation(self) -> None:
        """FilterSpec should create with field, operator, value."""
        filter_spec = FilterSpec(
            field="status",
            operator=FilterOperator.EQ,
            value="active",
        )
        assert filter_spec.field == "status"
        assert filter_spec.operator == FilterOperator.EQ
        assert filter_spec.value == "active"

    def test_filter_operators(self) -> None:
        """FilterOperator should have standard comparison operators."""
        assert FilterOperator.EQ.value == "eq"
        assert FilterOperator.NE.value == "ne"
        assert FilterOperator.LT.value == "lt"
        assert FilterOperator.LTE.value == "lte"
        assert FilterOperator.GT.value == "gt"
        assert FilterOperator.GTE.value == "gte"
        assert FilterOperator.IN.value == "in"
        assert FilterOperator.NOT_IN.value == "not_in"
        assert FilterOperator.LIKE.value == "like"
        assert FilterOperator.IS_NULL.value == "is_null"


class TestOrderSpec:
    """Tests for OrderSpec model."""

    def test_order_spec_creation(self) -> None:
        """OrderSpec should create with field and direction."""
        order_spec = OrderSpec(field="created_at", direction=OrderDirection.DESC)
        assert order_spec.field == "created_at"
        assert order_spec.direction == OrderDirection.DESC

    def test_order_directions(self) -> None:
        """OrderDirection should have ASC and DESC."""
        assert OrderDirection.ASC.value == "asc"
        assert OrderDirection.DESC.value == "desc"

    def test_order_spec_default_direction(self) -> None:
        """OrderSpec should default to ASC direction."""
        order_spec = OrderSpec(field="name")
        assert order_spec.direction == OrderDirection.ASC


class TestPaginatedResult:
    """Tests for PaginatedResult model."""

    def test_paginated_result_creation(self) -> None:
        """PaginatedResult should create with items, total, limit, offset."""
        result: PaginatedResult[str] = PaginatedResult(
            items=["a", "b", "c"],
            total=10,
            limit=3,
            offset=0,
        )
        assert result.items == ["a", "b", "c"]
        assert result.total == 10
        assert result.limit == 3
        assert result.offset == 0

    def test_paginated_result_has_more(self) -> None:
        """has_more should be True when more items exist."""
        result: PaginatedResult[str] = PaginatedResult(
            items=["a", "b", "c"],
            total=10,
            limit=3,
            offset=0,
        )
        assert result.has_more is True

    def test_paginated_result_no_more(self) -> None:
        """has_more should be False when all items shown."""
        result: PaginatedResult[str] = PaginatedResult(
            items=["a", "b"],
            total=5,
            limit=3,
            offset=3,
        )
        assert result.has_more is False

    def test_paginated_result_empty(self) -> None:
        """PaginatedResult should handle empty results."""
        result: PaginatedResult[str] = PaginatedResult(
            items=[],
            total=0,
            limit=10,
            offset=0,
        )
        assert result.items == []
        assert result.total == 0
        assert result.has_more is False


class TestRepositoryProtocol:
    """Tests for RepositoryProtocol interface."""

    def test_protocol_has_get_method(self) -> None:
        """RepositoryProtocol should define get method."""
        assert hasattr(RepositoryProtocol, "get")

    def test_protocol_has_save_method(self) -> None:
        """RepositoryProtocol should define save method."""
        assert hasattr(RepositoryProtocol, "save")

    def test_protocol_has_delete_method(self) -> None:
        """RepositoryProtocol should define delete method."""
        assert hasattr(RepositoryProtocol, "delete")

    def test_protocol_has_exists_method(self) -> None:
        """RepositoryProtocol should define exists method."""
        assert hasattr(RepositoryProtocol, "exists")

    def test_protocol_has_count_method(self) -> None:
        """RepositoryProtocol should define count method."""
        assert hasattr(RepositoryProtocol, "count")

    def test_protocol_has_list_method(self) -> None:
        """RepositoryProtocol should define list method."""
        assert hasattr(RepositoryProtocol, "list")

    def test_protocol_has_bulk_save_method(self) -> None:
        """RepositoryProtocol should define bulk_save method."""
        assert hasattr(RepositoryProtocol, "bulk_save")

    def test_protocol_is_generic(self) -> None:
        """RepositoryProtocol should be generic over T."""
        # Protocol should support generic parameterization
        assert hasattr(RepositoryProtocol, "__class_getitem__")

    def test_get_method_uses_uuid_id(self) -> None:
        """get() method should accept UUID for id parameter."""
        hints = get_type_hints(RepositoryProtocol.get)
        assert hints["id"] is UUID, f"get() id param should be UUID, got {hints['id']}"

    def test_delete_method_uses_uuid_id(self) -> None:
        """delete() method should accept UUID for id parameter."""
        hints = get_type_hints(RepositoryProtocol.delete)
        assert hints["id"] is UUID, (
            f"delete() id param should be UUID, got {hints['id']}"
        )

    def test_exists_method_uses_uuid_id(self) -> None:
        """exists() method should accept UUID for id parameter."""
        hints = get_type_hints(RepositoryProtocol.exists)
        assert hints["id"] is UUID, (
            f"exists() id param should be UUID, got {hints['id']}"
        )

    def test_get_method_signature(self) -> None:
        """get() should have correct signature: (id: UUID) -> T | None."""
        sig = inspect.signature(RepositoryProtocol.get)
        params = list(sig.parameters.keys())
        # 'self' and 'id'
        assert "id" in params

    def test_delete_method_signature(self) -> None:
        """delete() should have correct signature: (id: UUID) -> None."""
        sig = inspect.signature(RepositoryProtocol.delete)
        params = list(sig.parameters.keys())
        assert "id" in params

    def test_exists_method_signature(self) -> None:
        """exists() should have correct signature: (id: UUID) -> bool."""
        sig = inspect.signature(RepositoryProtocol.exists)
        params = list(sig.parameters.keys())
        assert "id" in params

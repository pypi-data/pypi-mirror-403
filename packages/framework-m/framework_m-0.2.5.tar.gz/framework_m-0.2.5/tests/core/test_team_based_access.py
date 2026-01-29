"""Tests for Team-Based Access (rls_field option).

TDD tests for the Meta.rls_field feature that enables team-based
Row-Level Security filtering.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from typing import ClassVar

import pytest

from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.registry import MetaRegistry
from framework_m.core.rls import get_rls_filters

# =============================================================================
# Test DocTypes
# =============================================================================


class Invoice(BaseDocType):
    """Standard DocType with default rls_field (owner)."""

    amount: float = 0.0

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        # rls_field not specified = defaults to "owner"
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager"],
        }


class TeamDocument(BaseDocType):
    """DocType with team-based RLS."""

    title: str = ""
    team: str = ""  # e.g., "sales", "engineering"

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        rls_field: ClassVar[str] = "team"  # RLS: WHERE team IN :user_teams
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee"],
        }


class DepartmentReport(BaseDocType):
    """DocType with custom rls_field."""

    title: str = ""
    department_code: str = ""

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        rls_field: ClassVar[str] = "department_code"
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee"],
        }


# =============================================================================
# Tests for get_rls_field()
# =============================================================================


class TestGetRlsField:
    """Test BaseDocType.get_rls_field() classmethod."""

    def test_default_rls_field_is_owner(self) -> None:
        """DocType without Meta.rls_field should default to 'owner'."""
        assert Invoice.get_rls_field() == "owner"

    def test_team_rls_field(self) -> None:
        """DocType with rls_field='team' should return 'team'."""
        assert TeamDocument.get_rls_field() == "team"

    def test_custom_rls_field(self) -> None:
        """DocType with custom rls_field should return that field."""
        assert DepartmentReport.get_rls_field() == "department_code"


# =============================================================================
# Tests for Team-Based get_permitted_filters
# =============================================================================


class TestTeamBasedPermittedFilters:
    """Test get_permitted_filters for team-based RLS."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Register test DocTypes before each test."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)
        registry.register_doctype(TeamDocument)
        registry.register_doctype(DepartmentReport)

    @pytest.mark.asyncio
    async def test_owner_based_rls_returns_owner_filter(self) -> None:
        """Default rls_field='owner' should filter by owner."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="user-123",
            principal_attributes={
                "roles": ["Employee"],
                "teams": ["sales"],
            },
            resource="Invoice",
        )

        # Should filter by owner, not team
        assert filters == {"owner": "user-123"}

    @pytest.mark.asyncio
    async def test_team_based_rls_returns_team_filter(self) -> None:
        """rls_field='team' should filter by team IN user_teams."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="user-123",
            principal_attributes={
                "roles": ["Employee"],
                "teams": ["sales", "marketing"],
            },
            resource="TeamDocument",
        )

        # Should filter by team
        assert filters == {"team": ["sales", "marketing"]}

    @pytest.mark.asyncio
    async def test_custom_field_rls(self) -> None:
        """Custom rls_field should use that field with teams."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="user-123",
            principal_attributes={
                "roles": ["Employee"],
                "teams": ["DEPT-001", "DEPT-002"],
            },
            resource="DepartmentReport",
        )

        # Should filter by the custom field
        assert filters == {"department_code": ["DEPT-001", "DEPT-002"]}

    @pytest.mark.asyncio
    async def test_no_teams_returns_empty_list(self) -> None:
        """User with no teams should get empty list filter for team-based RLS."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="user-123",
            principal_attributes={
                "roles": ["Employee"],
                "teams": [],  # No teams
            },
            resource="TeamDocument",
        )

        # Should return empty team list (no access)
        assert filters == {"team": []}


# =============================================================================
# Tests for UserContext with teams
# =============================================================================


class TestUserContextTeams:
    """Test UserContext teams field."""

    def test_user_context_has_teams_field(self) -> None:
        """UserContext should have teams field."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            teams=["sales", "engineering"],
        )

        assert user.teams == ["sales", "engineering"]

    def test_user_context_teams_default_empty(self) -> None:
        """UserContext teams should default to empty list."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
        )

        assert user.teams == []


# =============================================================================
# Tests for get_rls_filters helper with teams
# =============================================================================


class TestGetRlsFiltersWithTeams:
    """Test get_rls_filters helper for team-based RLS."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Register test DocTypes."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)
        registry.register_doctype(TeamDocument)

    @pytest.mark.asyncio
    async def test_returns_team_filter_for_team_doctype(self) -> None:
        """get_rls_filters should return team filter for team-based DocType."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
            teams=["sales"],
        )

        filters = await get_rls_filters(user, "TeamDocument")

        assert filters == {"team": ["sales"]}

    @pytest.mark.asyncio
    async def test_returns_owner_filter_for_owner_doctype(self) -> None:
        """get_rls_filters should return owner filter for owner-based DocType."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
            teams=["sales"],
        )

        filters = await get_rls_filters(user, "Invoice")

        assert filters == {"owner": "user-123"}

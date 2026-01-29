"""Tests for System Context (Elevated Operations).

TDD tests for the SystemContext context manager used for background jobs,
migrations, and service-to-service calls that need elevated access.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

import pytest

from framework_m.core.system_context import (
    SystemPrincipal,
    get_current_system_context,
    is_system_context,
    system_context,
)


class TestSystemPrincipal:
    """Test the SystemPrincipal dataclass."""

    def test_system_principal_has_system_id(self) -> None:
        """SystemPrincipal should have id='system'."""
        principal = SystemPrincipal()
        assert principal.id == "system"

    def test_system_principal_has_system_role(self) -> None:
        """SystemPrincipal should have 'System' role."""
        principal = SystemPrincipal()
        assert "System" in principal.roles

    def test_system_principal_is_system_flag(self) -> None:
        """SystemPrincipal should have is_system=True."""
        principal = SystemPrincipal()
        assert principal.is_system is True

    def test_system_principal_custom_id(self) -> None:
        """SystemPrincipal can have custom id for different system processes."""
        principal = SystemPrincipal(id="scheduler")
        assert principal.id == "scheduler"
        assert principal.is_system is True

    def test_system_principal_additional_roles(self) -> None:
        """SystemPrincipal can have additional roles."""
        principal = SystemPrincipal(roles=["System", "Admin"])
        assert "System" in principal.roles
        assert "Admin" in principal.roles


class TestSystemContextManager:
    """Test the system_context() context manager."""

    @pytest.mark.asyncio
    async def test_yields_system_principal(self) -> None:
        """system_context should yield a SystemPrincipal."""
        async with system_context() as ctx:
            assert isinstance(ctx, SystemPrincipal)
            assert ctx.id == "system"
            assert ctx.is_system is True

    @pytest.mark.asyncio
    async def test_custom_principal_id(self) -> None:
        """system_context can accept custom principal id."""
        async with system_context(principal_id="migration") as ctx:
            assert ctx.id == "migration"
            assert ctx.is_system is True

    @pytest.mark.asyncio
    async def test_context_is_available_inside(self) -> None:
        """Inside system_context, is_system_context() should return True."""
        async with system_context():
            assert is_system_context() is True

    @pytest.mark.asyncio
    async def test_context_not_available_outside(self) -> None:
        """Outside system_context, is_system_context() should return False."""
        assert is_system_context() is False

    @pytest.mark.asyncio
    async def test_get_current_returns_principal_inside(self) -> None:
        """get_current_system_context should return principal inside context."""
        async with system_context() as ctx:
            current = get_current_system_context()
            assert current is ctx

    @pytest.mark.asyncio
    async def test_get_current_returns_none_outside(self) -> None:
        """get_current_system_context should return None outside context."""
        current = get_current_system_context()
        assert current is None

    @pytest.mark.asyncio
    async def test_nested_contexts_preserve_outer(self) -> None:
        """Nested system_context should preserve the outer context."""
        async with system_context(principal_id="outer"):
            async with system_context(principal_id="inner") as inner:
                assert inner.id == "inner"
            # After inner exits, we should still be in outer
            current = get_current_system_context()
            assert current is not None
            assert current.id == "outer"

    @pytest.mark.asyncio
    async def test_context_cleaned_up_on_exception(self) -> None:
        """system_context should clean up even if exception raised."""
        with pytest.raises(ValueError):
            async with system_context():
                assert is_system_context() is True
                raise ValueError("Test exception")

        # After exception, context should be cleaned up
        assert is_system_context() is False


class TestSystemContextWithPermissions:
    """Test system context integration with permission system."""

    @pytest.mark.asyncio
    async def test_system_principal_converts_to_user_context(self) -> None:
        """SystemPrincipal can be converted to UserContext for permission checks."""
        async with system_context() as ctx:
            user_context = ctx.to_user_context()

            assert user_context.id == "system"
            assert "System" in user_context.roles
            assert user_context.is_system_user is True

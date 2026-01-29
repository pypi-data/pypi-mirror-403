"""Tests for UnitOfWork context manager."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

if TYPE_CHECKING:
    pass


# =============================================================================
# Test: UnitOfWork Context Manager
# =============================================================================


class TestUnitOfWorkContextManager:
    """Tests for UnitOfWork as async context manager."""

    def test_unit_of_work_is_importable(self) -> None:
        """UnitOfWork should be importable from core module."""
        from framework_m.core.unit_of_work import UnitOfWork

        assert UnitOfWork is not None

    @pytest.mark.asyncio
    async def test_uow_provides_session(self) -> None:
        """UnitOfWork should provide session property after entering."""
        from framework_m.core.unit_of_work import UnitOfWork

        mock_session = AsyncMock()
        session_factory = MagicMock(return_value=mock_session)

        async with UnitOfWork(session_factory) as uow:
            assert uow.session is mock_session

    @pytest.mark.asyncio
    async def test_session_before_enter_raises_error(self) -> None:
        """Accessing session before __aenter__ should raise RuntimeError."""
        from framework_m.core.unit_of_work import UnitOfWork

        mock_session = AsyncMock()
        session_factory = MagicMock(return_value=mock_session)

        uow = UnitOfWork(session_factory)

        with pytest.raises(RuntimeError, match="UnitOfWork not entered"):
            _ = uow.session


class TestUnitOfWorkCommit:
    """Tests for commit functionality."""

    @pytest.mark.asyncio
    async def test_commit_calls_session_commit(self) -> None:
        """commit() should call session.commit()."""
        from framework_m.core.unit_of_work import UnitOfWork

        mock_session = AsyncMock()
        session_factory = MagicMock(return_value=mock_session)

        async with UnitOfWork(session_factory) as uow:
            await uow.commit()

        mock_session.commit.assert_called_once()


class TestUnitOfWorkRollback:
    """Tests for rollback on exception."""

    @pytest.mark.asyncio
    async def test_exception_triggers_rollback(self) -> None:
        """Exception in context should trigger rollback."""
        from framework_m.core.unit_of_work import UnitOfWork

        mock_session = AsyncMock()
        session_factory = MagicMock(return_value=mock_session)

        with pytest.raises(ValueError):
            async with UnitOfWork(session_factory):
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_exception_no_rollback(self) -> None:
        """Normal exit should not call rollback."""
        from framework_m.core.unit_of_work import UnitOfWork

        mock_session = AsyncMock()
        session_factory = MagicMock(return_value=mock_session)

        async with UnitOfWork(session_factory):
            pass

        mock_session.rollback.assert_not_called()


class TestUnitOfWorkSessionClose:
    """Tests for session cleanup."""

    @pytest.mark.asyncio
    async def test_session_closed_after_normal_exit(self) -> None:
        """Session should be closed after normal exit."""
        from framework_m.core.unit_of_work import UnitOfWork

        mock_session = AsyncMock()
        session_factory = MagicMock(return_value=mock_session)

        async with UnitOfWork(session_factory):
            pass

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_closed_after_exception(self) -> None:
        """Session should be closed even after exception."""
        from framework_m.core.unit_of_work import UnitOfWork

        mock_session = AsyncMock()
        session_factory = MagicMock(return_value=mock_session)

        with pytest.raises(ValueError):
            async with UnitOfWork(session_factory):
                raise ValueError("Test error")

        mock_session.close.assert_called_once()


class TestUnitOfWorkImport:
    """Tests for module imports."""

    def test_import_unit_of_work_from_core(self) -> None:
        """UnitOfWork should be importable from core module."""
        from framework_m.core.unit_of_work import UnitOfWork

        assert UnitOfWork is not None


class TestUnitOfWorkExplicitRollback:
    """Tests for explicit rollback method."""

    @pytest.mark.asyncio
    async def test_explicit_rollback(self) -> None:
        """rollback() should call session.rollback()."""
        from framework_m.core.unit_of_work import UnitOfWork

        mock_session = AsyncMock()
        session_factory = MagicMock(return_value=mock_session)

        async with UnitOfWork(session_factory) as uow:
            await uow.rollback()

        mock_session.rollback.assert_called()

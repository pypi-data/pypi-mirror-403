"""Tests for Taskiq DI integration with JobContext."""

from unittest.mock import Mock

import pytest

# =============================================================================
# Test: get_job_context Dependency
# =============================================================================


class TestGetJobContext:
    """Tests for get_job_context dependency function."""

    def test_import_get_job_context(self) -> None:
        """get_job_context should be importable."""
        from framework_m.adapters.jobs.taskiq_adapter import get_job_context

        assert get_job_context is not None

    @pytest.mark.asyncio
    async def test_get_job_context_with_taskiq_context(self) -> None:
        """get_job_context should create JobContext from Taskiq Context."""
        from taskiq import Context

        from framework_m.adapters.jobs.taskiq_adapter import get_job_context

        # Mock Taskiq Context
        mock_message = Mock()
        mock_message.task_id = "task-123"
        mock_message.task_name = "test_job"
        mock_message.labels = {}

        mock_broker = Mock()
        context = Context(mock_message, mock_broker)

        # Call dependency
        job_ctx = await get_job_context(context)

        assert job_ctx.metadata.job_id == "task-123"
        assert job_ctx.metadata.job_name == "test_job"
        assert job_ctx.metadata.started_at is not None
        # db_session and event_bus will be None in basic usage
        assert job_ctx.db_session is None
        assert job_ctx.event_bus is None

    @pytest.mark.asyncio
    async def test_get_job_context_extracts_user_id(self) -> None:
        """get_job_context should extract user_id from message labels."""
        from taskiq import Context

        from framework_m.adapters.jobs.taskiq_adapter import get_job_context

        mock_message = Mock()
        mock_message.task_id = "task-123"
        mock_message.task_name = "test_job"
        mock_message.labels = {"user_id": "user-456"}

        mock_broker = Mock()
        context = Context(mock_message, mock_broker)
        job_ctx = await get_job_context(context)

        assert job_ctx.metadata.user_id == "user-456"


# =============================================================================
# Test: Job Using Context
# =============================================================================


class TestJobWithContext:
    """Tests for jobs using JobContext via DI."""

    @pytest.mark.asyncio
    async def test_job_can_receive_context(self) -> None:
        """Job function should be able to receive JobContext via TaskiqDepends."""
        from taskiq import TaskiqDepends

        from framework_m.adapters.jobs.taskiq_adapter import JobContext, job

        # Define a job that uses context
        @job(name="test_context_job")
        async def test_job(
            name: str,
            ctx: JobContext = TaskiqDepends(),  # Will use default factory
        ) -> dict:
            return {
                "name": name,
                "job_id": ctx.metadata.job_id if ctx else None,
            }

        # Job should have metadata
        assert hasattr(test_job, "_job_meta")
        assert test_job._job_meta["name"] == "test_context_job"  # type: ignore[attr-defined]

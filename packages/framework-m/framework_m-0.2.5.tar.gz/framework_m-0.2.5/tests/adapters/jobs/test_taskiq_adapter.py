"""Tests for TaskiqJobQueueAdapter with NATS JetStream.

TDD tests for the Taskiq-based job queue adapter.
Uses mocks for unit tests - integration tests require running NATS.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from framework_m.core.interfaces.job_queue import JobStatus

if TYPE_CHECKING:
    from framework_m.adapters.jobs.taskiq_adapter import TaskiqJobQueueAdapter

# =============================================================================
# Test: Module Imports
# =============================================================================


class TestTaskiqAdapterImports:
    """Tests for taskiq adapter imports."""

    def test_import_taskiq_adapter_module(self) -> None:
        """TaskiqJobQueueAdapter should be importable."""
        from framework_m.adapters.jobs.taskiq_adapter import TaskiqJobQueueAdapter

        assert TaskiqJobQueueAdapter is not None

    def test_import_job_decorator(self) -> None:
        """@job decorator should be importable."""
        from framework_m.adapters.jobs.taskiq_adapter import job

        assert job is not None

    def test_import_job_registry(self) -> None:
        """JobRegistry should be importable."""
        from framework_m.adapters.jobs.taskiq_adapter import JobRegistry

        assert JobRegistry is not None


# =============================================================================
# Test: JobRegistry
# =============================================================================


class TestJobRegistry:
    """Tests for job registration."""

    def test_register_and_get_job(self) -> None:
        """JobRegistry should store and retrieve job handlers."""
        from framework_m.adapters.jobs.taskiq_adapter import JobRegistry

        registry = JobRegistry()

        async def my_handler() -> str:
            return "done"

        registry.register("my_job", my_handler)

        assert registry.get("my_job") is my_handler

    def test_get_unknown_job_returns_none(self) -> None:
        """JobRegistry.get should return None for unknown jobs."""
        from framework_m.adapters.jobs.taskiq_adapter import JobRegistry

        registry = JobRegistry()

        assert registry.get("unknown") is None

    def test_list_jobs(self) -> None:
        """JobRegistry.list should return all registered job names."""
        from framework_m.adapters.jobs.taskiq_adapter import JobRegistry

        registry = JobRegistry()

        async def job1() -> None:
            pass

        async def job2() -> None:
            pass

        registry.register("job1", job1)
        registry.register("job2", job2)

        assert set(registry.list()) == {"job1", "job2"}


# =============================================================================
# Test: @job Decorator
# =============================================================================


class TestJobDecorator:
    """Tests for @job decorator."""

    def test_job_decorator_registers_function(self) -> None:
        """@job decorator should register the function in global registry."""
        from framework_m.adapters.jobs.taskiq_adapter import (
            get_global_registry,
            job,
        )

        registry = get_global_registry()
        initial_count = len(registry.list())

        @job(name="test_decorated_job")
        async def my_decorated_job() -> str:
            return "done"

        # Should be registered
        assert "test_decorated_job" in registry.list()
        assert len(registry.list()) == initial_count + 1

    def test_job_decorator_with_retry(self) -> None:
        """@job decorator should accept retry parameter."""
        from framework_m.adapters.jobs.taskiq_adapter import job

        @job(name="retry_job", retry=5)
        async def my_retry_job() -> str:
            return "done"

        # Check metadata is stored
        assert hasattr(my_retry_job, "_job_meta")
        assert my_retry_job._job_meta["retry"] == 5

    def test_job_decorator_preserves_function(self) -> None:
        """@job decorator should return the original function."""
        from framework_m.adapters.jobs.taskiq_adapter import job

        @job(name="preserved_job")
        async def original_func() -> str:
            return "original"

        # Should still be callable
        import asyncio

        result = asyncio.run(original_func())
        assert result == "original"


# =============================================================================
# Test: TaskiqJobQueueAdapter - Unit Tests
# =============================================================================


class TestTaskiqJobQueueAdapterUnit:
    """Unit tests for TaskiqJobQueueAdapter (mocked broker)."""

    @pytest.fixture
    def mock_broker(self) -> MagicMock:
        """Create a mock Taskiq broker."""
        broker = MagicMock()
        broker.task = MagicMock(return_value=lambda f: f)
        return broker

    @pytest.fixture
    def adapter(self, mock_broker: MagicMock) -> "TaskiqJobQueueAdapter":
        """Create adapter with mocked broker."""
        from framework_m.adapters.jobs.taskiq_adapter import TaskiqJobQueueAdapter

        return TaskiqJobQueueAdapter(broker=mock_broker)

    @pytest.mark.asyncio
    async def test_enqueue_calls_kiq(self, adapter: "TaskiqJobQueueAdapter") -> None:
        """enqueue should call .kiq() on the registered task."""

        # Register a mock task
        mock_task = AsyncMock()
        mock_task.kiq = AsyncMock(return_value=MagicMock(task_id="job-123"))
        adapter._tasks["send_email"] = mock_task

        job_id = await adapter.enqueue("send_email", to="user@example.com")

        mock_task.kiq.assert_called_once_with(to="user@example.com")
        assert job_id == "job-123"

    @pytest.mark.asyncio
    async def test_enqueue_unregistered_raises(
        self, adapter: "TaskiqJobQueueAdapter"
    ) -> None:
        """enqueue should raise ValueError for unregistered jobs."""
        with pytest.raises(ValueError, match="not registered"):
            await adapter.enqueue("nonexistent_job")

    @pytest.mark.asyncio
    async def test_get_status_returns_job_info(
        self, adapter: "TaskiqJobQueueAdapter"
    ) -> None:
        """get_status should return JobInfo from broker result."""
        # Mock the result backend
        mock_result = MagicMock()
        mock_result.is_ready = True
        mock_result.return_value = {"result": "success"}
        mock_result.is_err = False

        adapter._broker.result_backend.get_result = AsyncMock(return_value=mock_result)

        status = await adapter.get_status("job-123")

        assert status is not None
        assert status.id == "job-123"
        assert status.status == JobStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_cancel_returns_false_no_result_backend(
        self, adapter: "TaskiqJobQueueAdapter"
    ) -> None:
        """cancel should return False if no result backend."""
        adapter._broker.result_backend = None

        result = await adapter.cancel("job-123")

        assert result is False


# =============================================================================
# Test: Factory Integration
# =============================================================================


class TestFactoryIntegration:
    """Tests for factory auto-detection with Taskiq."""

    def test_factory_returns_taskiq_when_nats_url_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_job_queue should return TaskiqJobQueueAdapter when NATS_URL set."""
        monkeypatch.setenv("NATS_URL", "nats://localhost:4222")

        from framework_m.adapters.factory import get_job_queue
        from framework_m.adapters.jobs.taskiq_adapter import TaskiqJobQueueAdapter

        queue = get_job_queue()
        assert isinstance(queue, TaskiqJobQueueAdapter)


# =============================================================================
# Test: build_cron_expression
# =============================================================================


class TestBuildCronExpression:
    """Tests for build_cron_expression helper."""

    def test_build_cron_default(self) -> None:
        """Default should be every minute."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        cron = build_cron_expression()

        assert cron == "* * * * *"

    def test_build_cron_daily_9am(self) -> None:
        """Should build daily at 9 AM expression."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        cron = build_cron_expression(minute=0, hour=9)

        assert cron == "0 9 * * *"

    def test_build_cron_every_hour(self) -> None:
        """Should build hourly expression."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        cron = build_cron_expression(minute=0)

        assert cron == "0 * * * *"

    def test_build_cron_specific_day(self) -> None:
        """Should build specific day expression."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        cron = build_cron_expression(minute=0, hour=12, day=15)

        assert cron == "0 12 15 * *"

    def test_build_cron_monthly(self) -> None:
        """Should build monthly expression."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        cron = build_cron_expression(minute=0, hour=0, day=1, month=6)

        assert cron == "0 0 1 6 *"

    def test_build_cron_day_of_week(self) -> None:
        """Should build day of week expression."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        cron = build_cron_expression(minute=0, hour=14, day_of_week=1)

        assert cron == "0 14 * * 1"


# =============================================================================
# Test: cron helper
# =============================================================================


class TestCronHelper:
    """Tests for cron schedule helper."""

    def test_cron_returns_dict(self) -> None:
        """cron should return schedule dict."""
        from framework_m.adapters.jobs.taskiq_adapter import cron

        schedule = cron("my_job", minute=0, hour=9)

        assert isinstance(schedule, dict)
        assert schedule["task_name"] == "my_job"
        assert schedule["cron"] == "0 9 * * *"

    def test_cron_every_minute(self) -> None:
        """cron with defaults should run every minute."""
        from framework_m.adapters.jobs.taskiq_adapter import cron

        schedule = cron("every_min_job")

        assert schedule["cron"] == "* * * * *"


# =============================================================================
# Test: get_job_context
# =============================================================================


class TestGetJobContext:
    """Tests for get_job_context dependency."""

    @pytest.mark.asyncio
    async def test_get_job_context_no_context(self) -> None:
        """get_job_context without context returns test context."""
        from framework_m.adapters.jobs.taskiq_adapter import get_job_context

        ctx = await get_job_context(None)

        assert ctx is not None
        assert ctx.metadata.job_id == "test-job-id"
        assert ctx.metadata.job_name == "test_job"

    @pytest.mark.asyncio
    async def test_get_job_context_with_taskiq_context(self) -> None:
        """get_job_context with Taskiq context extracts metadata."""
        from framework_m.adapters.jobs.taskiq_adapter import get_job_context

        # Mock Taskiq Context
        mock_message = MagicMock()
        mock_message.task_id = "real-job-id"
        mock_message.task_name = "real_job"
        mock_message.labels = {"user_id": "user-123"}

        mock_ctx = MagicMock()
        mock_ctx.message = mock_message

        ctx = await get_job_context(mock_ctx)

        assert ctx.metadata.job_id == "real-job-id"
        assert ctx.metadata.job_name == "real_job"
        assert ctx.metadata.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_get_job_context_no_labels(self) -> None:
        """get_job_context should handle missing labels."""
        from framework_m.adapters.jobs.taskiq_adapter import get_job_context

        mock_message = MagicMock()
        mock_message.task_id = "job-id"
        mock_message.task_name = "job"
        mock_message.labels = None

        mock_ctx = MagicMock()
        mock_ctx.message = mock_message

        ctx = await get_job_context(mock_ctx)

        assert ctx.metadata.user_id is None


# =============================================================================
# Test: TaskiqJobQueueAdapter Schedule and Retry
# =============================================================================


class TestTaskiqScheduleAndRetry:
    """Tests for schedule and retry methods."""

    @pytest.fixture
    def mock_broker(self) -> MagicMock:
        """Create a mock Taskiq broker."""
        broker = MagicMock()
        broker.task = MagicMock(return_value=lambda f: f)
        broker.result_backend = MagicMock()
        return broker

    @pytest.fixture
    def adapter(self, mock_broker: MagicMock) -> "TaskiqJobQueueAdapter":
        """Create adapter with mocked broker."""
        from framework_m.adapters.jobs.taskiq_adapter import TaskiqJobQueueAdapter

        return TaskiqJobQueueAdapter(broker=mock_broker)

    @pytest.mark.asyncio
    async def test_schedule_returns_schedule_id(
        self, adapter: "TaskiqJobQueueAdapter"
    ) -> None:
        """schedule should return a schedule ID."""
        # Register a mock task
        mock_task = AsyncMock()
        adapter._tasks["scheduled_job"] = mock_task

        schedule_id = await adapter.schedule("scheduled_job", "0 9 * * *")

        assert schedule_id is not None
        assert len(schedule_id) > 0

    @pytest.mark.asyncio
    async def test_schedule_unregistered_raises(
        self, adapter: "TaskiqJobQueueAdapter"
    ) -> None:
        """schedule should raise ValueError for unregistered job."""
        with pytest.raises(ValueError, match="not registered"):
            await adapter.schedule("nonexistent_job", "0 * * * *")

    @pytest.mark.asyncio
    async def test_retry_success(self, adapter: "TaskiqJobQueueAdapter") -> None:
        """retry should re-enqueue a failed job."""
        from framework_m.core.interfaces.job_queue import JobInfo, JobStatus

        # Set up a failed job
        adapter._job_store["failed-job-id"] = JobInfo(
            id="failed-job-id",
            name="send_email",
            status=JobStatus.FAILED,
            enqueued_at=datetime.now(UTC),
        )

        # Register the task
        mock_task = AsyncMock()
        mock_task.kiq = AsyncMock(return_value=MagicMock(task_id="new-job-id"))
        adapter._tasks["send_email"] = mock_task

        new_job_id = await adapter.retry("failed-job-id")

        assert new_job_id == "new-job-id"

    @pytest.mark.asyncio
    async def test_retry_not_found_raises(
        self, adapter: "TaskiqJobQueueAdapter"
    ) -> None:
        """retry should raise ValueError for non-existent job."""
        with pytest.raises(ValueError, match="not found"):
            await adapter.retry("nonexistent-job-id")

    @pytest.mark.asyncio
    async def test_retry_not_failed_raises(
        self, adapter: "TaskiqJobQueueAdapter"
    ) -> None:
        """retry should raise ValueError for non-failed job."""
        from framework_m.core.interfaces.job_queue import JobInfo, JobStatus

        # Set up a successful job
        adapter._job_store["success-job-id"] = JobInfo(
            id="success-job-id",
            name="send_email",
            status=JobStatus.SUCCESS,
            enqueued_at=datetime.now(UTC),
        )

        with pytest.raises(ValueError, match="not failed"):
            await adapter.retry("success-job-id")

    def test_register_task(self, adapter: "TaskiqJobQueueAdapter") -> None:
        """register_task should add task to adapter."""
        mock_task = MagicMock()

        adapter.register_task("my_task", mock_task)

        assert "my_task" in adapter._tasks
        assert adapter._tasks["my_task"] is mock_task


class TestTaskiqCancelExtended:
    """Extended tests for cancel method."""

    @pytest.fixture
    def mock_broker(self) -> MagicMock:
        """Create a mock Taskiq broker."""
        broker = MagicMock()
        broker.result_backend = MagicMock()
        return broker

    @pytest.fixture
    def adapter(self, mock_broker: MagicMock) -> "TaskiqJobQueueAdapter":
        """Create adapter with mocked broker."""
        from framework_m.adapters.jobs.taskiq_adapter import TaskiqJobQueueAdapter

        return TaskiqJobQueueAdapter(broker=mock_broker)

    @pytest.mark.asyncio
    async def test_cancel_not_found(self, adapter: "TaskiqJobQueueAdapter") -> None:
        """cancel should return False for non-existent job."""
        result = await adapter.cancel("nonexistent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_already_complete(
        self, adapter: "TaskiqJobQueueAdapter"
    ) -> None:
        """cancel should return False for completed job."""
        from framework_m.core.interfaces.job_queue import JobInfo, JobStatus

        adapter._job_store["completed-id"] = JobInfo(
            id="completed-id",
            name="test",
            status=JobStatus.SUCCESS,
            enqueued_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )

        result = await adapter.cancel("completed-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_pending_job(self, adapter: "TaskiqJobQueueAdapter") -> None:
        """cancel should return True for pending job."""
        from framework_m.core.interfaces.job_queue import JobInfo, JobStatus

        adapter._job_store["pending-id"] = JobInfo(
            id="pending-id",
            name="test",
            status=JobStatus.PENDING,
            enqueued_at=datetime.now(UTC),
        )

        result = await adapter.cancel("pending-id")

        assert result is True
        assert adapter._job_store["pending-id"].status == JobStatus.CANCELLED


class TestJobRegistryMetadata:
    """Tests for JobRegistry metadata."""

    def test_get_metadata_for_registered_job(self) -> None:
        """get_metadata should return stored metadata."""
        from framework_m.adapters.jobs.taskiq_adapter import JobRegistry

        registry = JobRegistry()

        async def my_handler() -> str:
            return "done"

        metadata = {"retry": 5, "timeout": 600}
        registry.register("my_job", my_handler, metadata)

        result = registry.get_metadata("my_job")

        assert result["retry"] == 5
        assert result["timeout"] == 600

    def test_get_metadata_for_unknown_returns_empty(self) -> None:
        """get_metadata should return empty dict for unknown job."""
        from framework_m.adapters.jobs.taskiq_adapter import JobRegistry

        registry = JobRegistry()

        result = registry.get_metadata("unknown")

        assert result == {}

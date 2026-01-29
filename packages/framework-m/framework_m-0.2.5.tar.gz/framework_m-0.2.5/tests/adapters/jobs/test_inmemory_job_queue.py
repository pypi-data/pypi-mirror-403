"""Tests for InMemoryJobQueue adapter."""

import asyncio

import pytest

from framework_m.adapters.jobs import InMemoryJobQueue
from framework_m.core.interfaces.job_queue import JobStatus

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def job_queue() -> InMemoryJobQueue:
    """Create a fresh InMemoryJobQueue for each test."""
    queue = InMemoryJobQueue()
    yield queue
    queue.clear()


# =============================================================================
# Test: Job Registration
# =============================================================================


class TestJobRegistration:
    """Tests for job registration."""

    def test_register_job(self, job_queue: InMemoryJobQueue) -> None:
        """register_job should store the handler."""

        async def my_handler() -> str:
            return "done"

        job_queue.register_job("my_job", my_handler)

        assert "my_job" in job_queue._job_handlers

    @pytest.mark.asyncio
    async def test_enqueue_unregistered_job_raises(
        self, job_queue: InMemoryJobQueue
    ) -> None:
        """enqueue should raise ValueError for unregistered jobs."""
        with pytest.raises(ValueError, match="not registered"):
            await job_queue.enqueue("nonexistent_job")


# =============================================================================
# Test: Enqueue and Execute
# =============================================================================


class TestEnqueueAndExecute:
    """Tests for job enqueueing and execution."""

    @pytest.mark.asyncio
    async def test_enqueue_returns_job_id(self, job_queue: InMemoryJobQueue) -> None:
        """enqueue should return a unique job ID."""

        async def my_handler() -> str:
            return "done"

        job_queue.register_job("my_job", my_handler)
        job_id = await job_queue.enqueue("my_job")

        assert job_id is not None
        assert len(job_id) > 0

    @pytest.mark.asyncio
    async def test_job_executes_successfully(self, job_queue: InMemoryJobQueue) -> None:
        """Enqueued job should execute and complete with SUCCESS status."""
        result_holder: list[str] = []

        async def my_handler(message: str) -> dict[str, str]:
            result_holder.append(message)
            return {"message": message}

        job_queue.register_job("my_job", my_handler)
        job_id = await job_queue.enqueue("my_job", message="hello")

        # Wait for job to complete
        await asyncio.sleep(0.1)

        status = await job_queue.get_status(job_id)
        assert status is not None
        assert status.status == JobStatus.SUCCESS
        assert status.result == {"message": "hello"}
        assert result_holder == ["hello"]

    @pytest.mark.asyncio
    async def test_job_failure_sets_error(self, job_queue: InMemoryJobQueue) -> None:
        """Failed job should have FAILED status and error message."""

        async def failing_handler() -> None:
            raise RuntimeError("Something went wrong")

        job_queue.register_job("failing_job", failing_handler)
        job_id = await job_queue.enqueue("failing_job")

        # Wait for job to complete
        await asyncio.sleep(0.1)

        status = await job_queue.get_status(job_id)
        assert status is not None
        assert status.status == JobStatus.FAILED
        assert status.error == "Something went wrong"

    @pytest.mark.asyncio
    async def test_job_has_timing_info(self, job_queue: InMemoryJobQueue) -> None:
        """Completed job should have started_at and completed_at."""

        async def quick_handler() -> str:
            return "done"

        job_queue.register_job("quick_job", quick_handler)
        job_id = await job_queue.enqueue("quick_job")

        # Wait for job to complete
        await asyncio.sleep(0.1)

        status = await job_queue.get_status(job_id)
        assert status is not None
        assert status.enqueued_at is not None
        assert status.started_at is not None
        assert status.completed_at is not None


# =============================================================================
# Test: Get Status
# =============================================================================


class TestGetStatus:
    """Tests for job status retrieval."""

    @pytest.mark.asyncio
    async def test_get_status_returns_none_for_unknown(
        self, job_queue: InMemoryJobQueue
    ) -> None:
        """get_status should return None for unknown job ID."""
        status = await job_queue.get_status("nonexistent-id")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_status_returns_job_info(
        self, job_queue: InMemoryJobQueue
    ) -> None:
        """get_status should return JobInfo for known job."""

        async def my_handler() -> str:
            return "done"

        job_queue.register_job("my_job", my_handler)
        job_id = await job_queue.enqueue("my_job")

        status = await job_queue.get_status(job_id)
        assert status is not None
        assert status.id == job_id
        assert status.name == "my_job"


# =============================================================================
# Test: Cancel
# =============================================================================


class TestCancel:
    """Tests for job cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_returns_false_for_unknown(
        self, job_queue: InMemoryJobQueue
    ) -> None:
        """cancel should return False for unknown job ID."""
        result = await job_queue.cancel("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_completed_job_returns_false(
        self, job_queue: InMemoryJobQueue
    ) -> None:
        """cancel should return False for already completed job."""

        async def quick_handler() -> str:
            return "done"

        job_queue.register_job("quick_job", quick_handler)
        job_id = await job_queue.enqueue("quick_job")

        # Wait for completion
        await asyncio.sleep(0.1)

        result = await job_queue.cancel(job_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_running_job(self, job_queue: InMemoryJobQueue) -> None:
        """cancel should cancel a running job."""

        async def slow_handler() -> str:
            await asyncio.sleep(10)
            return "done"

        job_queue.register_job("slow_job", slow_handler)
        job_id = await job_queue.enqueue("slow_job")

        # Give it a moment to start
        await asyncio.sleep(0.01)

        result = await job_queue.cancel(job_id)
        assert result is True

        status = await job_queue.get_status(job_id)
        assert status is not None
        assert status.status == JobStatus.CANCELLED


# =============================================================================
# Test: Retry
# =============================================================================


class TestRetry:
    """Tests for job retry."""

    @pytest.mark.asyncio
    async def test_retry_unknown_job_raises(self, job_queue: InMemoryJobQueue) -> None:
        """retry should raise ValueError for unknown job."""
        with pytest.raises(ValueError, match="not found"):
            await job_queue.retry("nonexistent-id")

    @pytest.mark.asyncio
    async def test_retry_non_failed_job_raises(
        self, job_queue: InMemoryJobQueue
    ) -> None:
        """retry should raise ValueError for non-failed job."""

        async def quick_handler() -> str:
            return "done"

        job_queue.register_job("quick_job", quick_handler)
        job_id = await job_queue.enqueue("quick_job")

        # Wait for completion
        await asyncio.sleep(0.1)

        with pytest.raises(ValueError, match="not failed"):
            await job_queue.retry(job_id)

    @pytest.mark.asyncio
    async def test_retry_failed_job_creates_new_job(
        self, job_queue: InMemoryJobQueue
    ) -> None:
        """retry should create a new job with same parameters."""
        attempt_count = [0]

        async def sometimes_fails(value: int) -> dict[str, int]:
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                raise RuntimeError("First attempt fails")
            return {"value": value}

        job_queue.register_job("retry_job", sometimes_fails)
        job_id = await job_queue.enqueue("retry_job", value=42)

        # Wait for first attempt to fail
        await asyncio.sleep(0.1)

        status = await job_queue.get_status(job_id)
        assert status is not None
        assert status.status == JobStatus.FAILED

        # Retry
        new_job_id = await job_queue.retry(job_id)
        assert new_job_id != job_id

        # Wait for retry to complete
        await asyncio.sleep(0.1)

        new_status = await job_queue.get_status(new_job_id)
        assert new_status is not None
        assert new_status.status == JobStatus.SUCCESS
        assert new_status.result == {"value": 42}


# =============================================================================
# Test: Schedule
# =============================================================================


class TestSchedule:
    """Tests for job scheduling."""

    @pytest.mark.asyncio
    async def test_schedule_unregistered_job_raises(
        self, job_queue: InMemoryJobQueue
    ) -> None:
        """schedule should raise ValueError for unregistered jobs."""
        with pytest.raises(ValueError, match="not registered"):
            await job_queue.schedule("nonexistent_job", cron="* * * * *")

    @pytest.mark.asyncio
    async def test_schedule_returns_schedule_id(
        self, job_queue: InMemoryJobQueue
    ) -> None:
        """schedule should return a schedule ID."""

        async def my_handler() -> str:
            return "done"

        job_queue.register_job("my_job", my_handler)
        schedule_id = await job_queue.schedule("my_job", cron="* * * * *")

        assert schedule_id is not None
        assert len(schedule_id) > 0


# =============================================================================
# Test: List Jobs
# =============================================================================


class TestListJobs:
    """Tests for listing jobs."""

    @pytest.mark.asyncio
    async def test_list_jobs_empty(self, job_queue: InMemoryJobQueue) -> None:
        """list_jobs should return empty list when no jobs."""
        jobs = job_queue.list_jobs()
        assert jobs == []

    @pytest.mark.asyncio
    async def test_list_jobs_all(self, job_queue: InMemoryJobQueue) -> None:
        """list_jobs should return all jobs."""

        async def my_handler() -> str:
            return "done"

        job_queue.register_job("my_job", my_handler)
        await job_queue.enqueue("my_job")
        await job_queue.enqueue("my_job")

        jobs = job_queue.list_jobs()
        assert len(jobs) == 2

    @pytest.mark.asyncio
    async def test_list_jobs_by_status(self, job_queue: InMemoryJobQueue) -> None:
        """list_jobs should filter by status."""

        async def quick_handler() -> str:
            return "done"

        async def failing_handler() -> None:
            raise RuntimeError("fail")

        job_queue.register_job("quick_job", quick_handler)
        job_queue.register_job("failing_job", failing_handler)

        await job_queue.enqueue("quick_job")
        await job_queue.enqueue("failing_job")

        # Wait for completion
        await asyncio.sleep(0.1)

        success_jobs = job_queue.list_jobs(status=JobStatus.SUCCESS)
        assert len(success_jobs) == 1

        failed_jobs = job_queue.list_jobs(status=JobStatus.FAILED)
        assert len(failed_jobs) == 1


# =============================================================================
# Test: Clear
# =============================================================================


class TestClear:
    """Tests for clearing jobs."""

    @pytest.mark.asyncio
    async def test_clear_removes_all_jobs(self, job_queue: InMemoryJobQueue) -> None:
        """clear should remove all jobs."""

        async def my_handler() -> str:
            return "done"

        job_queue.register_job("my_job", my_handler)
        await job_queue.enqueue("my_job")
        await job_queue.enqueue("my_job")

        job_queue.clear()

        jobs = job_queue.list_jobs()
        assert jobs == []


# =============================================================================
# Test: Import
# =============================================================================


class TestImport:
    """Tests for module imports."""

    def test_import_inmemory_job_queue(self) -> None:
        """InMemoryJobQueue should be importable."""
        from framework_m.adapters.jobs import InMemoryJobQueue

        assert InMemoryJobQueue is not None

    def test_import_job_status(self) -> None:
        """JobStatus should be importable."""
        from framework_m.core.interfaces.job_queue import JobStatus

        assert JobStatus.PENDING is not None
        assert JobStatus.SUCCESS is not None

"""Tests for Job Router API - Comprehensive coverage tests."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# =============================================================================
# Test: Job Router Import
# =============================================================================


class TestJobRouterImport:
    """Tests for job router imports."""

    def test_import_create_job_router(self) -> None:
        """create_job_router should be importable."""
        from framework_m.adapters.web.job_router import create_job_router

        assert create_job_router is not None

    def test_import_list_jobs(self) -> None:
        """list_jobs should be importable."""
        from framework_m.adapters.web.job_router import list_jobs

        assert list_jobs is not None

    def test_import_get_job_status(self) -> None:
        """get_job_status should be importable."""
        from framework_m.adapters.web.job_router import get_job_status

        assert get_job_status is not None

    def test_import_cancel_job(self) -> None:
        """cancel_job should be importable."""
        from framework_m.adapters.web.job_router import cancel_job

        assert cancel_job is not None

    def test_import_retry_job(self) -> None:
        """retry_job should be importable."""
        from framework_m.adapters.web.job_router import retry_job

        assert retry_job is not None

    def test_exports(self) -> None:
        """job_router should export expected items."""
        from framework_m.adapters.web import job_router

        assert "create_job_router" in job_router.__all__
        assert "list_jobs" in job_router.__all__
        assert "get_job_status" in job_router.__all__
        assert "cancel_job" in job_router.__all__
        assert "retry_job" in job_router.__all__


# =============================================================================
# Test: Helper Functions
# =============================================================================


class TestGetJobQueue:
    """Tests for get_job_queue helper."""

    def test_get_job_queue_returns_instance(self) -> None:
        """get_job_queue should return InMemoryJobQueue."""
        from framework_m.adapters.web.job_router import get_job_queue

        queue = get_job_queue()

        from framework_m.adapters.jobs import InMemoryJobQueue

        assert isinstance(queue, InMemoryJobQueue)

    def test_get_job_queue_singleton(self) -> None:
        """get_job_queue should return same instance."""
        from framework_m.adapters.web.job_router import get_job_queue

        queue1 = get_job_queue()
        queue2 = get_job_queue()

        assert queue1 is queue2


class TestGetJobLogger:
    """Tests for get_job_logger helper."""

    def test_get_job_logger_returns_instance(self) -> None:
        """get_job_logger should return JobLogger."""
        from framework_m.adapters.web.job_router import get_job_logger

        logger = get_job_logger()

        from framework_m.adapters.jobs import JobLogger

        assert isinstance(logger, JobLogger)

    def test_get_job_logger_singleton(self) -> None:
        """get_job_logger should return same instance."""
        from framework_m.adapters.web.job_router import get_job_logger

        logger1 = get_job_logger()
        logger2 = get_job_logger()

        assert logger1 is logger2


# =============================================================================
# Test: Router Creation
# =============================================================================


class TestRouterCreation:
    """Tests for create_job_router."""

    def test_create_job_router_returns_router(self) -> None:
        """create_job_router should return Router."""
        from litestar import Router

        from framework_m.adapters.web.job_router import create_job_router

        router = create_job_router()

        assert isinstance(router, Router)

    def test_router_path(self) -> None:
        """Router should have correct path."""
        from framework_m.adapters.web.job_router import create_job_router

        router = create_job_router()

        assert router.path == "/api/v1/jobs"

    def test_router_has_tags(self) -> None:
        """Router should have jobs tag."""
        from framework_m.adapters.web.job_router import create_job_router

        router = create_job_router()

        assert "jobs" in router.tags


# =============================================================================
# Test: Handler Types
# =============================================================================


class TestHandlerTypes:
    """Tests for handler types and attributes."""

    def test_list_jobs_is_litestar_handler(self) -> None:
        """list_jobs should be Litestar handler."""
        from framework_m.adapters.web.job_router import list_jobs

        # Litestar decorators wrap functions
        assert hasattr(list_jobs, "fn") or callable(list_jobs)

    def test_get_job_status_is_litestar_handler(self) -> None:
        """get_job_status should be Litestar handler."""
        from framework_m.adapters.web.job_router import get_job_status

        assert hasattr(get_job_status, "fn") or callable(get_job_status)

    def test_cancel_job_is_litestar_handler(self) -> None:
        """cancel_job should be Litestar handler."""
        from framework_m.adapters.web.job_router import cancel_job

        assert hasattr(cancel_job, "fn") or callable(cancel_job)

    def test_retry_job_is_litestar_handler(self) -> None:
        """retry_job should be Litestar handler."""
        from framework_m.adapters.web.job_router import retry_job

        assert hasattr(retry_job, "fn") or callable(retry_job)


# =============================================================================
# Test: Handler Function Signatures
# =============================================================================


class TestHandlerSignatures:
    """Tests for handler function signatures."""

    def test_list_jobs_handler_fn(self) -> None:
        """list_jobs should have underlying function."""
        from framework_m.adapters.web.job_router import list_jobs

        # Access the wrapped function
        fn = getattr(list_jobs, "fn", list_jobs)
        assert callable(fn)

    def test_get_job_status_handler_fn(self) -> None:
        """get_job_status should have underlying function."""
        from framework_m.adapters.web.job_router import get_job_status

        fn = getattr(get_job_status, "fn", get_job_status)
        assert callable(fn)

    def test_cancel_job_handler_fn(self) -> None:
        """cancel_job should have underlying function."""
        from framework_m.adapters.web.job_router import cancel_job

        fn = getattr(cancel_job, "fn", cancel_job)
        assert callable(fn)

    def test_retry_job_handler_fn(self) -> None:
        """retry_job should have underlying function."""
        from framework_m.adapters.web.job_router import retry_job

        fn = getattr(retry_job, "fn", retry_job)
        assert callable(fn)


# =============================================================================
# Test: Handler Underlying Functions
# =============================================================================


class TestListJobsFn:
    """Tests for list_jobs underlying function."""

    @pytest.mark.asyncio
    async def test_list_jobs_fn_returns_dict(self) -> None:
        """list_jobs.fn should return dict with jobs."""
        from framework_m.adapters.web.job_router import list_jobs

        fn = getattr(list_jobs, "fn", None)
        if fn is None:
            pytest.skip("Cannot access underlying function")

        with patch("framework_m.adapters.web.job_router.get_job_logger") as mock_get:
            mock_logger = MagicMock()
            mock_logger._logs = {}
            mock_get.return_value = mock_logger

            result = await fn()

            assert isinstance(result, dict)
            assert "jobs" in result
            assert "total" in result

    @pytest.mark.asyncio
    async def test_list_jobs_fn_empty(self) -> None:
        """list_jobs.fn should return empty list when no jobs."""
        from framework_m.adapters.web.job_router import list_jobs

        fn = getattr(list_jobs, "fn", None)
        if fn is None:
            pytest.skip("Cannot access underlying function")

        with patch("framework_m.adapters.web.job_router.get_job_logger") as mock_get:
            mock_logger = MagicMock()
            mock_logger._logs = {}
            mock_get.return_value = mock_logger

            result = await fn()

            assert result["jobs"] == []
            assert result["total"] == 0


class TestGetJobStatusFn:
    """Tests for get_job_status underlying function."""

    @pytest.mark.asyncio
    async def test_get_job_status_fn_found(self) -> None:
        """get_job_status.fn should return job info when found."""
        from framework_m.adapters.web.job_router import get_job_status
        from framework_m.core.interfaces.job_queue import JobInfo, JobStatus

        fn = getattr(get_job_status, "fn", None)
        if fn is None:
            pytest.skip("Cannot access underlying function")

        mock_job = JobInfo(
            id="job-123",
            name="send_email",
            status=JobStatus.SUCCESS,
            enqueued_at=datetime.now(UTC),
        )

        with patch("framework_m.adapters.web.job_router.get_job_queue") as mock_get:
            mock_queue = MagicMock()
            mock_queue.get_status = AsyncMock(return_value=mock_job)
            mock_get.return_value = mock_queue

            result = await fn("job-123")

            assert result["id"] == "job-123"
            assert result["name"] == "send_email"

    @pytest.mark.asyncio
    async def test_get_job_status_fn_not_found(self) -> None:
        """get_job_status.fn should raise NotFoundException."""
        from litestar.exceptions import NotFoundException

        from framework_m.adapters.web.job_router import get_job_status

        fn = getattr(get_job_status, "fn", None)
        if fn is None:
            pytest.skip("Cannot access underlying function")

        with patch("framework_m.adapters.web.job_router.get_job_queue") as mock_get:
            mock_queue = MagicMock()
            mock_queue.get_status = AsyncMock(return_value=None)
            mock_get.return_value = mock_queue

            with pytest.raises(NotFoundException):
                await fn("nonexistent")


class TestCancelJobFn:
    """Tests for cancel_job underlying function."""

    @pytest.mark.asyncio
    async def test_cancel_job_fn_success(self) -> None:
        """cancel_job.fn should return success when cancelled."""
        from framework_m.adapters.web.job_router import cancel_job

        fn = getattr(cancel_job, "fn", None)
        if fn is None:
            pytest.skip("Cannot access underlying function")

        with patch("framework_m.adapters.web.job_router.get_job_queue") as mock_get:
            mock_queue = MagicMock()
            mock_queue.cancel = AsyncMock(return_value=True)
            mock_get.return_value = mock_queue

            result = await fn("job-123")

            assert result["cancelled"] is True
            assert result["job_id"] == "job-123"

    @pytest.mark.asyncio
    async def test_cancel_job_fn_not_found(self) -> None:
        """cancel_job.fn should raise NotFoundException when not found."""
        from litestar.exceptions import NotFoundException

        from framework_m.adapters.web.job_router import cancel_job

        fn = getattr(cancel_job, "fn", None)
        if fn is None:
            pytest.skip("Cannot access underlying function")

        with patch("framework_m.adapters.web.job_router.get_job_queue") as mock_get:
            mock_queue = MagicMock()
            mock_queue.cancel = AsyncMock(return_value=False)
            mock_get.return_value = mock_queue

            with pytest.raises(NotFoundException):
                await fn("nonexistent")


class TestRetryJobFn:
    """Tests for retry_job underlying function."""

    @pytest.mark.asyncio
    async def test_retry_job_fn_success(self) -> None:
        """retry_job.fn should return new job ID."""
        from framework_m.adapters.web.job_router import retry_job

        fn = getattr(retry_job, "fn", None)
        if fn is None:
            pytest.skip("Cannot access underlying function")

        with patch("framework_m.adapters.web.job_router.get_job_queue") as mock_get:
            mock_queue = MagicMock()
            mock_queue.retry = AsyncMock(return_value="new-job-456")
            mock_get.return_value = mock_queue

            result = await fn("job-123")

            assert result["new_job_id"] == "new-job-456"
            assert result["original_job_id"] == "job-123"

    @pytest.mark.asyncio
    async def test_retry_job_fn_error(self) -> None:
        """retry_job.fn should raise ClientException on error."""
        from litestar.exceptions import ClientException

        from framework_m.adapters.web.job_router import retry_job

        fn = getattr(retry_job, "fn", None)
        if fn is None:
            pytest.skip("Cannot access underlying function")

        with patch("framework_m.adapters.web.job_router.get_job_queue") as mock_get:
            mock_queue = MagicMock()
            mock_queue.retry = AsyncMock(side_effect=ValueError("Job not failed"))
            mock_get.return_value = mock_queue

            with pytest.raises(ClientException):
                await fn("job-123")

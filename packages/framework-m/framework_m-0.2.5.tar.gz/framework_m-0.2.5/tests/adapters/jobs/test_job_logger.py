"""Tests for JobLogger service."""

import pytest

# =============================================================================
# Test: JobLogger Import
# =============================================================================


class TestJobLoggerImport:
    """Tests for JobLogger import."""

    def test_import_job_logger(self) -> None:
        """JobLogger should be importable."""
        from framework_m.adapters.jobs.job_logger import JobLogger

        assert JobLogger is not None

    def test_import_job_logger_protocol(self) -> None:
        """JobLoggerProtocol should be importable."""
        from framework_m.adapters.jobs.job_logger import JobLoggerProtocol

        assert JobLoggerProtocol is not None


# =============================================================================
# Test: JobLogger Lifecycle
# =============================================================================


class TestJobLoggerLifecycle:
    """Tests for JobLogger logging lifecycle."""

    @pytest.mark.asyncio
    async def test_log_enqueue_creates_log(self) -> None:
        """log_enqueue should create a new JobLog entry."""
        from framework_m.adapters.jobs.job_logger import InMemoryJobLogger

        logger = InMemoryJobLogger()
        log = await logger.log_enqueue(job_id="job-123", job_name="send_email")

        assert log.job_id == "job-123"
        assert log.job_name == "send_email"
        assert log.status == "queued"

    @pytest.mark.asyncio
    async def test_log_start_updates_status(self) -> None:
        """log_start should update status to running."""
        from framework_m.adapters.jobs.job_logger import InMemoryJobLogger

        logger = InMemoryJobLogger()
        await logger.log_enqueue(job_id="job-123", job_name="send_email")
        log = await logger.log_start(job_id="job-123")

        assert log is not None
        assert log.status == "running"
        assert log.started_at is not None

    @pytest.mark.asyncio
    async def test_log_success_updates_status(self) -> None:
        """log_success should update status to success."""
        from framework_m.adapters.jobs.job_logger import InMemoryJobLogger

        logger = InMemoryJobLogger()
        await logger.log_enqueue(job_id="job-123", job_name="send_email")
        await logger.log_start(job_id="job-123")
        log = await logger.log_success(job_id="job-123", result={"sent": True})

        assert log is not None
        assert log.status == "success"
        assert log.completed_at is not None
        assert log.result == {"sent": True}

    @pytest.mark.asyncio
    async def test_log_failure_updates_status(self) -> None:
        """log_failure should update status to failed."""
        from framework_m.adapters.jobs.job_logger import InMemoryJobLogger

        logger = InMemoryJobLogger()
        await logger.log_enqueue(job_id="job-123", job_name="send_email")
        await logger.log_start(job_id="job-123")
        log = await logger.log_failure(job_id="job-123", error="Connection refused")

        assert log is not None
        assert log.status == "failed"
        assert log.completed_at is not None
        assert log.error == "Connection refused"


# =============================================================================
# Test: JobLogger Retrieval
# =============================================================================


class TestJobLoggerRetrieval:
    """Tests for JobLogger log retrieval."""

    @pytest.mark.asyncio
    async def test_get_log_returns_log(self) -> None:
        """get_log should return log by job_id."""
        from framework_m.adapters.jobs.job_logger import InMemoryJobLogger

        logger = InMemoryJobLogger()
        await logger.log_enqueue(job_id="job-123", job_name="send_email")

        log = await logger.get_log(job_id="job-123")
        assert log is not None
        assert log.job_id == "job-123"

    @pytest.mark.asyncio
    async def test_get_log_returns_none_for_unknown(self) -> None:
        """get_log should return None for unknown job_id."""
        from framework_m.adapters.jobs.job_logger import InMemoryJobLogger

        logger = InMemoryJobLogger()
        log = await logger.get_log(job_id="unknown")
        assert log is None

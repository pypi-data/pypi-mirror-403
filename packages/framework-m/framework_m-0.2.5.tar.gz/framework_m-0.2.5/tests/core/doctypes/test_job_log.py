"""Tests for JobLog DocType."""

from datetime import UTC, datetime

# =============================================================================
# Test: JobLog DocType Import
# =============================================================================


class TestJobLogImport:
    """Tests for JobLog DocType import."""

    def test_import_job_log(self) -> None:
        """JobLog should be importable from doctypes."""
        from framework_m.core.doctypes.job_log import JobLog

        assert JobLog is not None

    def test_job_log_in_all_exports(self) -> None:
        """JobLog should be in __all__."""
        from framework_m.core.doctypes import job_log

        assert "JobLog" in job_log.__all__


# =============================================================================
# Test: JobLog Creation
# =============================================================================


class TestJobLogCreation:
    """Tests for JobLog DocType creation."""

    def test_create_job_log_with_required_fields(self) -> None:
        """JobLog should be creatable with required fields."""
        from framework_m.core.doctypes.job_log import JobLog

        log = JobLog(
            job_id="job-123",
            job_name="send_email",
            status="queued",
        )

        assert log.job_id == "job-123"
        assert log.job_name == "send_email"
        assert log.status == "queued"

    def test_job_log_has_auto_enqueued_at(self) -> None:
        """JobLog should auto-generate enqueued_at timestamp."""
        from framework_m.core.doctypes.job_log import JobLog

        before = datetime.now(UTC)
        log = JobLog(
            job_id="job-123",
            job_name="send_email",
            status="queued",
        )
        after = datetime.now(UTC)

        assert log.enqueued_at is not None
        assert before <= log.enqueued_at <= after


# =============================================================================
# Test: JobLog Status Values
# =============================================================================


class TestJobLogStatus:
    """Tests for JobLog status values."""

    def test_job_log_queued_status(self) -> None:
        """JobLog should accept 'queued' status."""
        from framework_m.core.doctypes.job_log import JobLog

        log = JobLog(job_id="job-123", job_name="test", status="queued")
        assert log.status == "queued"

    def test_job_log_running_status(self) -> None:
        """JobLog should accept 'running' status."""
        from framework_m.core.doctypes.job_log import JobLog

        log = JobLog(job_id="job-123", job_name="test", status="running")
        assert log.status == "running"

    def test_job_log_success_status(self) -> None:
        """JobLog should accept 'success' status."""
        from framework_m.core.doctypes.job_log import JobLog

        log = JobLog(job_id="job-123", job_name="test", status="success")
        assert log.status == "success"

    def test_job_log_failed_status(self) -> None:
        """JobLog should accept 'failed' status."""
        from framework_m.core.doctypes.job_log import JobLog

        log = JobLog(job_id="job-123", job_name="test", status="failed")
        assert log.status == "failed"


# =============================================================================
# Test: JobLog Optional Fields
# =============================================================================


class TestJobLogOptionalFields:
    """Tests for JobLog optional fields."""

    def test_job_log_with_started_at(self) -> None:
        """JobLog should accept started_at timestamp."""
        from framework_m.core.doctypes.job_log import JobLog

        started = datetime.now(UTC)
        log = JobLog(
            job_id="job-123",
            job_name="test",
            status="running",
            started_at=started,
        )

        assert log.started_at == started

    def test_job_log_with_completed_at(self) -> None:
        """JobLog should accept completed_at timestamp."""
        from framework_m.core.doctypes.job_log import JobLog

        completed = datetime.now(UTC)
        log = JobLog(
            job_id="job-123",
            job_name="test",
            status="success",
            completed_at=completed,
        )

        assert log.completed_at == completed

    def test_job_log_with_error(self) -> None:
        """JobLog should accept error message."""
        from framework_m.core.doctypes.job_log import JobLog

        log = JobLog(
            job_id="job-123",
            job_name="test",
            status="failed",
            error="Connection refused",
        )

        assert log.error == "Connection refused"

    def test_job_log_with_result(self) -> None:
        """JobLog should accept result dict."""
        from framework_m.core.doctypes.job_log import JobLog

        log = JobLog(
            job_id="job-123",
            job_name="test",
            status="success",
            result={"emails_sent": 100},
        )

        assert log.result == {"emails_sent": 100}

    def test_job_log_defaults_are_none(self) -> None:
        """JobLog optional fields should default to None."""
        from framework_m.core.doctypes.job_log import JobLog

        log = JobLog(job_id="job-123", job_name="test", status="queued")

        assert log.started_at is None
        assert log.completed_at is None
        assert log.error is None
        assert log.result is None


# =============================================================================
# Test: JobLog Meta Configuration
# =============================================================================


class TestJobLogMeta:
    """Tests for JobLog Meta configuration."""

    def test_job_log_has_meta_class(self) -> None:
        """JobLog should have Meta class."""
        from framework_m.core.doctypes.job_log import JobLog

        assert hasattr(JobLog, "Meta")

    def test_job_log_requires_auth(self) -> None:
        """JobLog should require authentication."""
        from framework_m.core.doctypes.job_log import JobLog

        assert JobLog.Meta.requires_auth is True

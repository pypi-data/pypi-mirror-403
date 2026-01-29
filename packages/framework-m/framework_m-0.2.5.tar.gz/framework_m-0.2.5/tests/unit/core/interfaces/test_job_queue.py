"""Tests for JobQueueProtocol interface compliance."""

from datetime import UTC, datetime

from framework_m.core.interfaces.job_queue import (
    JobInfo,
    JobQueueProtocol,
    JobStatus,
)


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_job_status_values(self) -> None:
        """JobStatus should have all required status values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.SUCCESS.value == "success"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"


class TestJobInfo:
    """Tests for JobInfo model."""

    def test_job_info_creation(self) -> None:
        """JobInfo should create with required fields."""
        job = JobInfo(
            id="job-001",
            name="send_email",
            status=JobStatus.PENDING,
            enqueued_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )
        assert job.id == "job-001"
        assert job.name == "send_email"
        assert job.status == JobStatus.PENDING

    def test_job_info_with_started_at(self) -> None:
        """JobInfo should track started_at timestamp."""
        now = datetime.now(UTC)
        job = JobInfo(
            id="job-001",
            name="send_email",
            status=JobStatus.RUNNING,
            enqueued_at=now,
            started_at=now,
        )
        assert job.started_at == now

    def test_job_info_with_completed_at(self) -> None:
        """JobInfo should track completed_at timestamp."""
        now = datetime.now(UTC)
        job = JobInfo(
            id="job-001",
            name="send_email",
            status=JobStatus.SUCCESS,
            enqueued_at=now,
            completed_at=now,
        )
        assert job.completed_at == now

    def test_job_info_with_result(self) -> None:
        """JobInfo should store result on success."""
        job = JobInfo(
            id="job-001",
            name="calculate_sum",
            status=JobStatus.SUCCESS,
            enqueued_at=datetime.now(UTC),
            result={"sum": 42},
        )
        assert job.result == {"sum": 42}

    def test_job_info_with_error(self) -> None:
        """JobInfo should store error on failure."""
        job = JobInfo(
            id="job-001",
            name="send_email",
            status=JobStatus.FAILED,
            enqueued_at=datetime.now(UTC),
            error="Connection refused",
        )
        assert job.error == "Connection refused"

    def test_job_info_is_complete(self) -> None:
        """JobInfo.is_complete should check if job finished."""
        pending = JobInfo(
            id="job-001",
            name="test",
            status=JobStatus.PENDING,
            enqueued_at=datetime.now(UTC),
        )
        success = JobInfo(
            id="job-002",
            name="test",
            status=JobStatus.SUCCESS,
            enqueued_at=datetime.now(UTC),
        )
        failed = JobInfo(
            id="job-003",
            name="test",
            status=JobStatus.FAILED,
            enqueued_at=datetime.now(UTC),
        )
        assert pending.is_complete is False
        assert success.is_complete is True
        assert failed.is_complete is True


class TestJobQueueProtocol:
    """Tests for JobQueueProtocol interface."""

    def test_protocol_has_enqueue_method(self) -> None:
        """JobQueueProtocol should define enqueue method."""
        assert hasattr(JobQueueProtocol, "enqueue")

    def test_protocol_has_schedule_method(self) -> None:
        """JobQueueProtocol should define schedule method."""
        assert hasattr(JobQueueProtocol, "schedule")

    def test_protocol_has_cancel_method(self) -> None:
        """JobQueueProtocol should define cancel method."""
        assert hasattr(JobQueueProtocol, "cancel")

    def test_protocol_has_get_status_method(self) -> None:
        """JobQueueProtocol should define get_status method."""
        assert hasattr(JobQueueProtocol, "get_status")

    def test_protocol_has_retry_method(self) -> None:
        """JobQueueProtocol should define retry method."""
        assert hasattr(JobQueueProtocol, "retry")

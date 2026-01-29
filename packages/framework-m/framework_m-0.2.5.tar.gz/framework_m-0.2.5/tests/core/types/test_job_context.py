"""Tests for JobContext and JobMetadata types."""

from datetime import UTC, datetime

import pytest

# =============================================================================
# Test: JobMetadata
# =============================================================================


class TestJobMetadata:
    """Tests for JobMetadata dataclass."""

    def test_import_job_metadata(self) -> None:
        """JobMetadata should be importable."""
        from framework_m.core.types.job_context import JobMetadata

        assert JobMetadata is not None

    def test_job_metadata_creation(self) -> None:
        """JobMetadata should be creatable with required fields."""
        from framework_m.core.types.job_context import JobMetadata

        now = datetime.now(UTC)
        metadata = JobMetadata(
            job_id="job-123",
            job_name="send_email",
            enqueued_at=now,
        )

        assert metadata.job_id == "job-123"
        assert metadata.job_name == "send_email"
        assert metadata.enqueued_at == now
        assert metadata.started_at is None
        assert metadata.user_id is None

    def test_job_metadata_with_optional_fields(self) -> None:
        """JobMetadata should accept optional fields."""
        from framework_m.core.types.job_context import JobMetadata

        now = datetime.now(UTC)
        metadata = JobMetadata(
            job_id="job-123",
            job_name="send_email",
            enqueued_at=now,
            started_at=now,
            user_id="user-456",
        )

        assert metadata.started_at == now
        assert metadata.user_id == "user-456"


# =============================================================================
# Test: JobContext
# =============================================================================


class TestJobContext:
    """Tests for JobContext dataclass."""

    def test_import_job_context(self) -> None:
        """JobContext should be importable."""
        from framework_m.core.types.job_context import JobContext

        assert JobContext is not None

    def test_job_context_creation(self) -> None:
        """JobContext should be creatable with metadata."""
        from framework_m.core.types.job_context import JobContext, JobMetadata

        metadata = JobMetadata(
            job_id="job-123",
            job_name="test_job",
            enqueued_at=datetime.now(UTC),
        )

        context = JobContext(metadata=metadata)

        assert context.metadata == metadata
        assert context.db_session is None
        assert context.event_bus is None

    def test_job_context_with_dependencies(self) -> None:
        """JobContext should accept db_session and event_bus."""
        from unittest.mock import Mock

        from framework_m.core.types.job_context import JobContext, JobMetadata

        metadata = JobMetadata(
            job_id="job-123",
            job_name="test_job",
            enqueued_at=datetime.now(UTC),
        )
        mock_session = Mock()
        mock_bus = Mock()

        context = JobContext(
            metadata=metadata,
            db_session=mock_session,
            event_bus=mock_bus,
        )

        assert context.db_session is mock_session
        assert context.event_bus is mock_bus

    def test_job_context_get_repository_not_implemented(self) -> None:
        """get_repository should raise NotImplementedError for now."""
        from framework_m.core.types.job_context import JobContext, JobMetadata

        metadata = JobMetadata(
            job_id="job-123",
            job_name="test_job",
            enqueued_at=datetime.now(UTC),
        )
        context = JobContext(metadata=metadata)

        # For Phase 04, get_repository is a placeholder
        # Will be fully implemented when we add repository factory
        with pytest.raises(NotImplementedError):
            context.get_repository(object)

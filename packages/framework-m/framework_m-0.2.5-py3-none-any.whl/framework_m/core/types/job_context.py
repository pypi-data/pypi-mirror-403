"""Job context types for dependency injection in background jobs.

Provides JobContext and JobMetadata for accessing infrastructure
services (database, event bus, repositories) within job functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from framework_m.core.interfaces.event_bus import EventBusProtocol

# Type alias for database session - actual type provided by adapter
AsyncSession = Any

T = TypeVar("T")


@dataclass
class JobMetadata:
    """Metadata about a background job execution.

    Contains job identification, timing information, and optional
    user context that can be re-hydrated from job arguments.

    Attributes:
        job_id: Unique job execution ID
        job_name: Name of the job function
        enqueued_at: When the job was added to the queue
        started_at: When the job started executing (None if not started)
        user_id: Optional user context for auditing
    """

    job_id: str
    job_name: str
    enqueued_at: datetime
    started_at: datetime | None = None
    user_id: str | None = None


@dataclass
class JobContext:
    """Dependency injection context for background jobs.

    Provides access to infrastructure services within job functions
    through dependency injection, avoiding global state.

    Example:
        >>> from taskiq import TaskiqDepends
        >>> @job(name="send_email")
        ... async def send_email(
        ...     to: str,
        ...     ctx: JobContext = TaskiqDepends(get_job_context),
        ... ) -> bool:
        ...     # Access event bus via context
        ...     await ctx.event_bus.publish(EmailSentEvent(...))
        ...     return True

    Attributes:
        metadata: Job execution metadata (ID, name, timing)
        db_session: Database session for repository access
        event_bus: Event bus for publishing events
    """

    metadata: JobMetadata
    db_session: AsyncSession | None = None
    event_bus: EventBusProtocol | None = None

    def get_repository(self, repo_type: type[T]) -> T:
        """Get a repository instance with the current database session.

        Args:
            repo_type: Repository class type

        Returns:
            Repository instance

        Raises:
            NotImplementedError: Repository factory not yet implemented

        Note:
            This is a placeholder for Phase 04. Full implementation
            will come when we add a repository factory pattern.
        """
        raise NotImplementedError(
            "Repository factory not yet implemented. "
            "This will be added in a future phase."
        )


__all__ = ["JobContext", "JobMetadata"]

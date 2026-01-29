"""Interfaces (Ports) - Protocol definitions for the hexagonal architecture.

All ports are defined as Python Protocols for structural typing.
Infrastructure adapters implement these interfaces.

Exports all 12 core protocols:
    - RepositoryProtocol: Data persistence operations
    - EventBusProtocol: Pub/sub messaging
    - AuthContextProtocol: User authentication context
    - IdentityProtocol: Identity management and authentication
    - StorageProtocol: File storage operations
    - JobQueueProtocol: Background job processing
    - PermissionProtocol: Authorization and RBAC
    - PrintProtocol: Document rendering
    - CacheProtocol: Key-value caching
    - NotificationProtocol: Email, SMS, push notifications
    - SearchProtocol: Full-text search
    - I18nProtocol: Internationalization
"""

from framework_m.core.interfaces.auth_context import (
    AuthContextProtocol,
    UserContext,
)
from framework_m.core.interfaces.cache import CacheProtocol
from framework_m.core.interfaces.event_bus import (
    Event,
    EventBusProtocol,
    EventHandler,
)
from framework_m.core.interfaces.i18n import I18nProtocol
from framework_m.core.interfaces.identity import (
    Credentials,
    IdentityProtocol,
    PasswordCredentials,
    Token,
)
from framework_m.core.interfaces.job_queue import (
    JobInfo,
    JobQueueProtocol,
    JobStatus,
)
from framework_m.core.interfaces.notification import (
    NotificationProtocol,
    NotificationType,
)
from framework_m.core.interfaces.permission import (
    PermissionAction,
    PermissionProtocol,
)
from framework_m.core.interfaces.print import (
    PrintFormat,
    PrintProtocol,
)
from framework_m.core.interfaces.repository import (
    FilterOperator,
    FilterSpec,
    OrderDirection,
    OrderSpec,
    PaginatedResult,
    RepositoryProtocol,
)
from framework_m.core.interfaces.search import (
    SearchProtocol,
    SearchResult,
)
from framework_m.core.interfaces.storage import (
    FileMetadata,
    StorageProtocol,
)

__all__ = [
    "AuthContextProtocol",
    "CacheProtocol",
    "Credentials",
    "Event",
    "EventBusProtocol",
    "EventHandler",
    "FileMetadata",
    "FilterOperator",
    "FilterSpec",
    "I18nProtocol",
    "IdentityProtocol",
    "JobInfo",
    "JobQueueProtocol",
    "JobStatus",
    "NotificationProtocol",
    "NotificationType",
    "OrderDirection",
    "OrderSpec",
    "PaginatedResult",
    "PasswordCredentials",
    "PermissionAction",
    "PermissionProtocol",
    "PrintFormat",
    "PrintProtocol",
    "RepositoryProtocol",
    "SearchProtocol",
    "SearchResult",
    "StorageProtocol",
    "Token",
    "UserContext",
]

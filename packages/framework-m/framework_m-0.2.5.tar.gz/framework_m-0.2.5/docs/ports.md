# Protocol Interfaces (Ports)

Framework M defines clear protocol interfaces for all infrastructure concerns. This allows different implementations to be swapped without changing business logic.

## Overview

| Protocol | File | Purpose |
|----------|------|---------|
| `RepositoryProtocol` | `repository.py` | CRUD operations for documents |
| `EventBusProtocol` | `event_bus.py` | Publish/subscribe events |
| `AuthContextProtocol` | `auth_context.py` | Current user context |
| `PermissionProtocol` | `permission.py` | Authorization with RLS |
| `StorageProtocol` | `storage.py` | File storage abstraction |
| `JobQueueProtocol` | `job_queue.py` | Background job processing |
| `CacheProtocol` | `cache.py` | Caching layer |
| `NotificationProtocol` | `notification.py` | Email/SMS notifications |
| `SearchProtocol` | `search.py` | Full-text search |
| `PrintProtocol` | `print.py` | PDF/document generation |
| `I18nProtocol` | `i18n.py` | Internationalization |

---

## RepositoryProtocol

**Purpose**: Data access for documents with filtering, pagination, and optimistic concurrency.

```python
from typing import Protocol, Generic, TypeVar

T = TypeVar("T")

class RepositoryProtocol(Protocol[T]):
    async def get(self, name: str) -> T | None:
        """Fetch a document by its name."""
        ...
    
    async def save(self, doc: T, version: int | None = None) -> T:
        """Save a document with optional optimistic concurrency."""
        ...
    
    async def delete(self, name: str) -> None:
        """Delete a document."""
        ...
    
    async def exists(self, name: str) -> bool:
        """Check if a document exists."""
        ...
    
    async def list(
        self,
        filters: FilterSpec | None = None,
        order_by: list[OrderSpec] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedResult[T]:
        """List documents with filtering and pagination."""
        ...
```

**Key Types**:
- `FilterSpec`: Nested filter conditions
- `OrderSpec`: Sort specification (field, direction)
- `PaginatedResult`: Paginated response with items and total

---

## EventBusProtocol

**Purpose**: Publish/subscribe event system with CloudEvents format.

```python
class EventBusProtocol(Protocol):
    async def publish(self, event: CloudEvent) -> None:
        """Publish an event to all subscribers."""
        ...
    
    async def subscribe(
        self,
        pattern: str,
        handler: EventHandler,
    ) -> str:
        """Subscribe to events matching a pattern."""
        ...
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription."""
        ...
```

**Event Types**:
- `doc.created` - Document created
- `doc.updated` - Document modified
- `doc.deleted` - Document deleted
- `workflow.transition` - Workflow state change

---

## AuthContextProtocol

**Purpose**: Access to current user, roles, and tenant information.

```python
class AuthContextProtocol(Protocol):
    @property
    def user(self) -> UserContext | None:
        """Get current user or None for anonymous."""
        ...
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        ...
    
    def is_system_user(self) -> bool:
        """Check if running as system (bypass permissions)."""
        ...
```

**UserContext**:
```python
class UserContext:
    user_id: str
    email: str
    full_name: str
    roles: list[str]
    tenant_id: str | None
```

---

## PermissionProtocol

**Purpose**: Check permissions and generate Row-Level Security filters.

```python
class PermissionProtocol(Protocol):
    async def can(
        self,
        action: PermissionAction,
        doctype: str,
        doc: BaseDocType | None = None,
    ) -> bool:
        """Check if user can perform action."""
        ...
    
    async def get_permitted_filters(
        self,
        doctype: str,
        action: PermissionAction,
    ) -> FilterSpec:
        """Get RLS filters for list queries."""
        ...
```

**PermissionAction**: `read`, `write`, `create`, `delete`, `submit`, `cancel`

---

## StorageProtocol

**Purpose**: File storage with presigned URLs and metadata.

```python
class StorageProtocol(Protocol):
    async def save_file(
        self,
        key: str,
        content: bytes | AsyncIterable[bytes],
        content_type: str | None = None,
    ) -> FileMetadata:
        """Save a file."""
        ...
    
    async def get_file(self, key: str) -> bytes:
        """Retrieve file content."""
        ...
    
    async def get_url(
        self,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """Get a presigned URL for direct access."""
        ...
    
    async def delete_file(self, key: str) -> None:
        """Delete a file."""
        ...
```

---

## JobQueueProtocol

**Purpose**: Enqueue background jobs with scheduling and retry.

```python
class JobQueueProtocol(Protocol):
    async def enqueue(
        self,
        job_name: str,
        *args: Any,
        defer_by: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Enqueue a job for background execution."""
        ...
    
    async def schedule(
        self,
        job_name: str,
        cron: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Schedule a recurring job."""
        ...
    
    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending job."""
        ...
```

---

## CacheProtocol

**Purpose**: Key-value caching with TTL and pattern operations.

```python
class CacheProtocol(Protocol):
    async def get(self, key: str) -> Any | None:
        """Get a cached value."""
        ...
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set a cached value with optional TTL."""
        ...
    
    async def delete(self, key: str) -> None:
        """Delete a cached value."""
        ...
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        ...
```

---

## NotificationProtocol

**Purpose**: Send notifications via email, SMS, push, etc.

```python
class NotificationProtocol(Protocol):
    async def send(
        self,
        notification: Notification,
    ) -> str:
        """Send a notification."""
        ...
    
    async def send_bulk(
        self,
        notifications: list[Notification],
    ) -> list[str]:
        """Send multiple notifications."""
        ...
```

**Notification Types**: `email`, `sms`, `push`, `in_app`

---

## SearchProtocol

**Purpose**: Full-text search with facets and highlighting.

```python
class SearchProtocol(Protocol):
    async def index(
        self,
        doctype: str,
        doc_id: str,
        data: dict[str, Any],
    ) -> None:
        """Index a document for search."""
        ...
    
    async def search(
        self,
        query: str,
        doctypes: list[str] | None = None,
        filters: FilterSpec | None = None,
        limit: int = 20,
    ) -> SearchResult:
        """Search documents."""
        ...
    
    async def delete_index(
        self,
        doctype: str,
        doc_id: str,
    ) -> None:
        """Remove a document from search index."""
        ...
```

---

## PrintProtocol

**Purpose**: Generate PDF/HTML documents from templates.

```python
class PrintProtocol(Protocol):
    async def render(
        self,
        template: str,
        data: dict[str, Any],
        format: Literal["pdf", "html"] = "pdf",
    ) -> bytes:
        """Render a template to PDF or HTML."""
        ...
    
    async def get_template(self, name: str) -> Template:
        """Get a print template by name."""
        ...
```

---

## I18nProtocol

**Purpose**: Internationalization and localization.

```python
class I18nProtocol(Protocol):
    def translate(
        self,
        key: str,
        locale: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Translate a key to the target locale."""
        ...
    
    def get_locale(self) -> str:
        """Get the current locale."""
        ...
    
    def list_locales(self) -> list[str]:
        """List available locales."""
        ...
```

---

## Using Protocols

### In Business Logic

```python
from framework_m.core.interfaces import RepositoryProtocol

class InvoiceService:
    def __init__(self, repo: RepositoryProtocol[Invoice]) -> None:
        self.repo = repo
    
    async def create_invoice(self, data: dict) -> Invoice:
        invoice = Invoice(**data)
        return await self.repo.save(invoice)
```

### With Dependency Injection

```python
from dependency_injector.wiring import inject, Provide
from framework_m.core.container import Container
from framework_m.core.interfaces import RepositoryProtocol

@inject
async def get_invoices(
    repo: RepositoryProtocol = Provide[Container.repository],
) -> list[Invoice]:
    result = await repo.list()
    return result.items
```

### In Testing

```python
class MockRepository:
    def __init__(self):
        self.data = {}
    
    async def get(self, name: str) -> Invoice | None:
        return self.data.get(name)
    
    async def save(self, doc: Invoice) -> Invoice:
        self.data[doc.name] = doc
        return doc

# In tests
def test_invoice_creation():
    repo = MockRepository()
    service = InvoiceService(repo)
    # ...
```

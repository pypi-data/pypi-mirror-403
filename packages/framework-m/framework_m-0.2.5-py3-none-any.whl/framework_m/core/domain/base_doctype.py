"""Base DocType - Foundation class for all document types."""

from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class BaseDocType(BaseModel):
    """
    Base class for all DocTypes in Framework M.

    Provides standard fields and configuration for metadata-driven documents.
    All custom DocTypes should inherit from this class.

    Example:
        class Todo(BaseDocType):
            title: str = Field(description="Task title")
            is_completed: bool = False

        class Invoice(BaseDocType):
            customer: str
            total: float = 0.0

            class Meta:
                layout = {"sections": [{"fields": ["customer", "total"]}]}
                permissions = {"roles": ["Accountant"]}
    """

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    # Standard fields for all DocTypes
    id: UUID = Field(
        default_factory=uuid4, description="Primary key (UUID), auto-generated"
    )
    name: str | None = Field(
        default=None,
        description="Human-readable unique identifier, auto-generated if None",
    )
    creation: datetime = Field(
        default_factory=_utc_now, description="Document creation timestamp"
    )
    modified: datetime = Field(
        default_factory=_utc_now, description="Last modification timestamp"
    )
    modified_by: str | None = Field(
        default=None, description="User who last modified the document"
    )
    owner: str | None = Field(default=None, description="User who created the document")
    deleted_at: datetime | None = Field(
        default=None, description="Soft delete timestamp, None if not deleted"
    )

    # Class-level metadata (not serialized)
    _doctype_name: ClassVar[str | None] = None

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, v: UUID | str) -> UUID:
        """Convert string UUID to UUID object for database compatibility."""
        if isinstance(v, UUID):
            return v
        if isinstance(v, str):
            return UUID(v)
        return v

    @field_validator("creation", "modified", "deleted_at", mode="before")
    @classmethod
    def parse_datetime(cls, v: datetime | str | None) -> datetime | None:
        """Convert string datetime to datetime object for database compatibility."""
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Handle ISO format with or without timezone
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v

    @classmethod
    def get_doctype_name(cls) -> str:
        """
        Get the DocType name for this class.

        Returns the class name by default, but can be overridden
        via the _doctype_name class variable.
        """
        return cls._doctype_name or cls.__name__

    @classmethod
    def get_layout(cls) -> dict[str, Any]:
        """
        Get the layout configuration from the Meta class.

        Returns:
            Layout dict for form rendering, or empty dict if not defined.
        """
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return {}
        return getattr(meta, "layout", {})

    @classmethod
    def get_permissions(cls) -> dict[str, Any]:
        """
        Get the permissions configuration from the Meta class.

        Returns:
            Permissions dict for RBAC, or empty dict if not defined.
        """
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return {}
        return getattr(meta, "permissions", {})

    @classmethod
    def get_requires_auth(cls) -> bool:
        """
        Check if this DocType requires authentication for access.

        Returns:
            True if auth is required (default), False for public DocTypes.

        Example:
            class PublicConfig(BaseDocType):
                class Meta:
                    requires_auth = False  # Public access
        """
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return True  # Default: require auth
        return getattr(meta, "requires_auth", True)

    @classmethod
    def get_apply_rls(cls) -> bool:
        """
        Check if Row-Level Security should be applied to this DocType.

        When True, users only see documents they own (or have explicit access to).
        When False, all authorized users see all documents.

        Returns:
            True if RLS is applied (default), False for shared tables.

        Example:
            class Country(BaseDocType):
                class Meta:
                    apply_rls = False  # Everyone sees all countries
        """
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return True  # Default: apply RLS
        return getattr(meta, "apply_rls", True)

    @classmethod
    def get_rls_field(cls) -> str:
        """
        Get the field used for Row-Level Security filtering.

        By default, RLS filters by 'owner'. Override this to enable
        team-based or custom field-based RLS.

        Returns:
            The field name used for RLS filtering.

        Example:
            class TeamDocument(BaseDocType):
                team: str

                class Meta:
                    rls_field = "team"  # RLS: WHERE team IN :user_teams
        """
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return "owner"  # Default: filter by owner
        return getattr(meta, "rls_field", "owner")

    @classmethod
    def get_api_resource(cls) -> bool:
        """
        Check if this DocType should have auto-generated CRUD API endpoints.

        When True, the meta router will generate standard REST endpoints:
        - GET /api/v1/{doctype} - List
        - POST /api/v1/{doctype} - Create
        - GET /api/v1/{doctype}/{id} - Read
        - PUT /api/v1/{doctype}/{id} - Update
        - DELETE /api/v1/{doctype}/{id} - Delete

        Returns:
            True if CRUD endpoints should be generated, False otherwise (default).

        Example:
            class Invoice(BaseDocType):
                class Meta:
                    api_resource = True  # Enable auto-CRUD endpoints
        """
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return False  # Default: no auto-CRUD
        return getattr(meta, "api_resource", False)

    @classmethod
    def get_is_child_table(cls) -> bool:
        """
        Check if this DocType is a child table (embedded in parent).

        Child tables:
        - Inherit parent's RLS (no independent permission checks)
        - Are not exposed as API resources
        - Are loaded with their parent (no separate queries)
        - Have parent_doctype and parent_id fields for linking

        Returns:
            True if this is a child table, False otherwise (default).

        Example:
            class InvoiceItem(BaseDocType):
                class Meta:
                    is_child_table = True  # Mark as child table
        """
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return False  # Default: not a child table
        return getattr(meta, "is_child_table", False)

    @classmethod
    def get_show_in_desk(cls) -> bool:
        """
        Check if this DocType should be visible in the Desk UI sidebar.

        When False, the DocType is hidden from navigation menus and lists.
        Useful for internal/system DocTypes that users shouldn't interact with directly.

        Returns:
            True if should be shown in Desk (default), False to hide.

        Example:
            class JobLog(BaseDocType):
                class Meta:
                    api_resource = True  # Has API
                    show_in_desk = False  # But hidden from UI
        """
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return True  # Default: show in desk
        return getattr(meta, "show_in_desk", True)

    @classmethod
    def get_indexes(cls) -> list[dict[str, str | list[str]]]:
        """
        Get custom indexes defined for this DocType.

        Define indexes in Meta.indexes as a list of dicts with 'fields' key.
        Supports single-column and composite (multi-column) indexes.

        Returns:
            List of index specifications, each with 'fields' key.

        Example:
            class Product(BaseDocType):
                category: str
                status: str

                class Meta:
                    indexes = [
                        {"fields": ["category"]},  # Single column
                        {"fields": ["status", "category"]},  # Composite
                    ]
        """
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return []
        return getattr(meta, "indexes", [])


# Re-export Field for convenience
__all__ = ["BaseDocType", "Field"]

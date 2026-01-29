"""Tests for BaseDocType."""

from datetime import datetime
from typing import Any, ClassVar

import pytest
from pydantic import ValidationError

from framework_m import DocType, Field


class Todo(DocType):
    """Test DocType for unit tests."""

    title: str = Field(description="Task title")
    is_completed: bool = False


class Invoice(DocType):
    """Test DocType with custom Meta configuration."""

    customer: str
    total: float = 0.0

    class Meta:
        layout: ClassVar[dict[str, Any]] = {
            "sections": [{"fields": ["customer", "total"]}]
        }
        permissions: ClassVar[dict[str, Any]] = {"roles": ["Accountant"], "level": 1}


class PublicConfig(DocType):
    """Test DocType with public access (no auth)."""

    key: str
    value: str = ""

    class Meta:
        requires_auth: ClassVar[bool] = False
        apply_rls: ClassVar[bool] = False


class ProtectedData(DocType):
    """Test DocType with auth but no RLS (everyone sees all)."""

    title: str

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = False


class TestBaseDocType:
    """Tests for BaseDocType functionality."""

    def test_create_doctype_with_defaults(self) -> None:
        """DocType should create with default values."""
        from uuid import UUID

        todo = Todo(title="Test task")

        assert todo.title == "Test task"
        assert todo.is_completed is False
        assert todo.name is None
        assert todo.owner is None
        assert isinstance(todo.creation, datetime)
        assert isinstance(todo.modified, datetime)
        # id should be auto-generated UUID
        assert isinstance(todo.id, UUID)

    def test_id_is_unique_per_instance(self) -> None:
        """Each DocType instance should have a unique id."""
        todo1 = Todo(title="First")
        todo2 = Todo(title="Second")

        assert todo1.id != todo2.id

    def test_id_is_primary_key_uuid(self) -> None:
        """id field should be a UUID and the primary key."""
        from uuid import UUID

        todo = Todo(title="Test")

        # id should be a valid UUID
        assert isinstance(todo.id, UUID)
        # id should have a proper string representation
        assert (
            len(str(todo.id)) == 36
        )  # UUID string format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

    def test_create_doctype_with_explicit_id(self) -> None:
        """DocType should accept explicit id."""
        from uuid import UUID, uuid4

        custom_id = uuid4()
        todo = Todo(title="Test", id=custom_id)

        assert todo.id == custom_id
        assert isinstance(todo.id, UUID)

    def test_create_doctype_with_name(self) -> None:
        """DocType should accept explicit name (human-readable identifier)."""
        todo = Todo(title="Test", name="TODO-001")

        assert todo.name == "TODO-001"

    def test_get_doctype_name(self) -> None:
        """get_doctype_name should return class name."""
        assert Todo.get_doctype_name() == "Todo"

    def test_doctype_validation(self) -> None:
        """DocType should validate required fields."""
        with pytest.raises(ValidationError):
            Todo()  # type: ignore[call-arg]  # Missing required 'title'

    def test_doctype_extra_fields_forbidden(self) -> None:
        """DocType should reject unknown fields."""
        with pytest.raises(ValidationError):
            Todo(title="Test", unknown_field="value")  # type: ignore[call-arg]

    def test_doctype_to_dict(self) -> None:
        """DocType should convert to dictionary."""
        todo = Todo(title="Test", name="TODO-001")
        data = todo.model_dump()

        assert data["title"] == "Test"
        assert data["name"] == "TODO-001"
        assert "creation" in data
        assert "modified" in data


class TestDocTypeMeta:
    """Tests for DocType Meta class configuration."""

    def test_meta_layout_default(self) -> None:
        """DocType without Meta should have empty layout."""
        assert Todo.get_layout() == {}

    def test_meta_layout_custom(self) -> None:
        """DocType with Meta should return custom layout."""
        layout = Invoice.get_layout()
        assert "sections" in layout
        assert len(layout["sections"]) == 1

    def test_meta_permissions_default(self) -> None:
        """DocType without Meta should have empty permissions."""
        assert Todo.get_permissions() == {}

    def test_meta_permissions_custom(self) -> None:
        """DocType with Meta should return custom permissions."""
        perms = Invoice.get_permissions()
        assert perms["roles"] == ["Accountant"]
        assert perms["level"] == 1

    # Tests for get_requires_auth()

    def test_requires_auth_default_is_true(self) -> None:
        """DocType without Meta.requires_auth should default to True."""
        assert Todo.get_requires_auth() is True

    def test_requires_auth_explicit_false(self) -> None:
        """DocType with requires_auth=False should return False."""
        assert PublicConfig.get_requires_auth() is False

    def test_requires_auth_explicit_true(self) -> None:
        """DocType with requires_auth=True should return True."""
        assert ProtectedData.get_requires_auth() is True

    # Tests for get_apply_rls()

    def test_apply_rls_default_is_true(self) -> None:
        """DocType without Meta.apply_rls should default to True."""
        assert Todo.get_apply_rls() is True

    def test_apply_rls_explicit_false(self) -> None:
        """DocType with apply_rls=False should return False."""
        assert PublicConfig.get_apply_rls() is False
        assert ProtectedData.get_apply_rls() is False

    def test_apply_rls_explicit_true(self) -> None:
        """DocType with apply_rls=True should return True."""
        # Invoice doesn't have explicit apply_rls, should default to True
        assert Invoice.get_apply_rls() is True

    # Tests for get_rls_field()

    def test_rls_field_default_is_owner(self) -> None:
        """DocType without Meta.rls_field should default to 'owner'."""
        assert Todo.get_rls_field() == "owner"

    def test_rls_field_custom(self) -> None:
        """DocType with custom rls_field should return that field."""

        class TeamDoc(DocType):
            team: str

            class Meta:
                rls_field: ClassVar[str] = "team"

        assert TeamDoc.get_rls_field() == "team"

    # Tests for get_api_resource()

    def test_api_resource_default_is_false(self) -> None:
        """DocType without Meta.api_resource should default to False."""
        assert Todo.get_api_resource() is False

    def test_api_resource_explicit_true(self) -> None:
        """DocType with api_resource=True should return True."""

        class ApiDoc(DocType):
            title: str

            class Meta:
                api_resource: ClassVar[bool] = True

        assert ApiDoc.get_api_resource() is True

    # Tests for get_is_child_table()

    def test_is_child_table_default_is_false(self) -> None:
        """DocType without Meta.is_child_table should default to False."""
        assert Todo.get_is_child_table() is False

    def test_is_child_table_explicit_true(self) -> None:
        """DocType with is_child_table=True should return True."""

        class ChildDoc(DocType):
            item_name: str

            class Meta:
                is_child_table: ClassVar[bool] = True

        assert ChildDoc.get_is_child_table() is True

    # Tests for get_indexes()

    def test_get_indexes_default_is_empty(self) -> None:
        """DocType without Meta.indexes should return empty list."""
        assert Todo.get_indexes() == []

    def test_get_indexes_single_column(self) -> None:
        """DocType with single column index should return it."""

        class IndexedDoc(DocType):
            category: str

            class Meta:
                indexes: ClassVar[list[dict[str, Any]]] = [
                    {"fields": ["category"]},
                ]

        assert IndexedDoc.get_indexes() == [{"fields": ["category"]}]

    def test_get_indexes_composite(self) -> None:
        """DocType with composite index should return it."""

        class CompositeDoc(DocType):
            category: str
            status: str

            class Meta:
                indexes: ClassVar[list[dict[str, Any]]] = [
                    {"fields": ["category"]},
                    {"fields": ["status", "category"]},
                ]

        indexes = CompositeDoc.get_indexes()
        assert len(indexes) == 2
        assert indexes[1]["fields"] == ["status", "category"]


class TestDocTypeImport:
    """Tests for package imports."""

    def test_import_doctype(self) -> None:
        """DocType should be importable from framework_m."""
        from framework_m import DocType

        assert DocType is not None

    def test_import_field(self) -> None:
        """Field should be importable from framework_m."""
        from framework_m import Field

        assert Field is not None

    def test_import_version(self) -> None:
        """Version should be importable."""
        from framework_m import __version__

        # Version is managed by semantic-release, just check it exists
        assert __version__ is not None
        assert isinstance(__version__, str)

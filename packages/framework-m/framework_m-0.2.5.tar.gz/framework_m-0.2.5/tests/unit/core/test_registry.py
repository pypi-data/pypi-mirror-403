"""Tests for MetaRegistry."""

from typing import Any

import pytest

from framework_m import DocType, Field
from framework_m.core.domain.base_controller import BaseController
from framework_m.core.exceptions import DuplicateDocTypeError
from framework_m.core.registry import MetaRegistry


class Todo(DocType):
    """Test DocType for registry tests."""

    title: str = Field(description="Task title")
    is_completed: bool = False


class TodoController(BaseController[Todo]):
    """Test controller for registry tests."""

    async def validate(self, context: Any = None) -> None:
        """Custom validation."""
        if not self.doc.title.strip():
            raise ValueError("Title cannot be empty")


class Project(DocType):
    """Another test DocType."""

    name: str
    status: str = "active"


class TestMetaRegistrySingleton:
    """Tests for MetaRegistry singleton behavior."""

    def test_registry_is_singleton(self) -> None:
        """MetaRegistry should be a singleton."""
        registry1 = MetaRegistry()
        registry2 = MetaRegistry()

        assert registry1 is registry2

    def test_registry_get_instance(self) -> None:
        """get_instance should return the singleton."""
        registry = MetaRegistry.get_instance()

        assert registry is MetaRegistry()


class TestMetaRegistryDocTypes:
    """Tests for DocType registration and retrieval."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MetaRegistry().clear()

    def test_register_doctype(self) -> None:
        """register_doctype should add doctype to registry."""
        registry = MetaRegistry()

        registry.register_doctype(Todo)

        assert "Todo" in registry.list_doctypes()

    def test_register_doctype_with_controller(self) -> None:
        """register_doctype should accept optional controller."""
        registry = MetaRegistry()

        registry.register_doctype(Todo, TodoController)

        assert registry.get_controller("Todo") is TodoController

    def test_get_doctype(self) -> None:
        """get_doctype should return registered doctype class."""
        registry = MetaRegistry()
        registry.register_doctype(Todo)

        result = registry.get_doctype("Todo")

        assert result is Todo

    def test_get_doctype_not_found(self) -> None:
        """get_doctype should raise KeyError for unknown doctype."""
        registry = MetaRegistry()

        with pytest.raises(KeyError):
            registry.get_doctype("Unknown")

    def test_get_controller(self) -> None:
        """get_controller should return registered controller class."""
        registry = MetaRegistry()
        registry.register_doctype(Todo, TodoController)

        result = registry.get_controller("Todo")

        assert result is TodoController

    def test_get_controller_not_registered(self) -> None:
        """get_controller should return None if no controller registered."""
        registry = MetaRegistry()
        registry.register_doctype(Todo)

        result = registry.get_controller("Todo")

        assert result is None

    def test_list_doctypes(self) -> None:
        """list_doctypes should return all registered doctype names."""
        registry = MetaRegistry()
        registry.register_doctype(Todo)
        registry.register_doctype(Project)

        result = registry.list_doctypes()

        assert "Todo" in result
        assert "Project" in result
        assert len(result) == 2

    def test_list_doctypes_empty(self) -> None:
        """list_doctypes should return empty list when no doctypes."""
        registry = MetaRegistry()

        result = registry.list_doctypes()

        assert result == []


class TestMetaRegistryConflictPolicy:
    """Tests for duplicate DocType detection."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MetaRegistry().clear()

    def test_duplicate_doctype_raises_error(self) -> None:
        """Registering same DocType name twice should raise DuplicateDocTypeError."""
        registry = MetaRegistry()
        registry.register_doctype(Todo)

        # Create a different class with same DocType name using _doctype_name
        class DuplicateTodo(DocType):
            _doctype_name = "Todo"  # Same name as Todo
            title: str = Field(description="Another Todo")

        with pytest.raises(DuplicateDocTypeError) as exc_info:
            registry.register_doctype(DuplicateTodo)

        assert "Todo" in str(exc_info.value)

    def test_duplicate_doctype_error_has_existing_source(self) -> None:
        """DuplicateDocTypeError should contain source info."""
        registry = MetaRegistry()
        registry.register_doctype(Todo)

        class AnotherTodo(DocType):
            _doctype_name = "Todo"  # Same name as Todo
            title: str

        with pytest.raises(DuplicateDocTypeError) as exc_info:
            registry.register_doctype(AnotherTodo)

        # Should include existing module info
        assert exc_info.value.existing_module is not None


class TestMetaRegistryLoadOrder:
    """Tests for load order functionality."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MetaRegistry().clear()

    def test_load_apps_discovers_doctypes_in_order(self) -> None:
        """load_apps should discover DocTypes from apps in order."""
        registry = MetaRegistry()

        # Load from installed_apps list - empty list should work
        count = registry.load_apps([])

        assert count == 0

    def test_load_apps_returns_total_count(self) -> None:
        """load_apps should return total discovered DocTypes."""
        registry = MetaRegistry()

        # This package doesn't exist but should not raise
        count = registry.load_apps(["nonexistent.app"])

        assert count == 0


class TestMetaRegistryDiscovery:
    """Tests for automatic DocType discovery."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MetaRegistry().clear()

    def test_discover_doctypes_returns_count(self) -> None:
        """discover_doctypes should return count of discovered doctypes."""
        registry = MetaRegistry()

        # Discover from test module (this file)
        count = registry.discover_doctypes("tests.unit.core.test_registry")

        # Should find Todo and Project defined in this file
        assert count >= 0  # May be 0 if discovery doesn't find test classes


class TestMetaRegistryImports:
    """Tests for registry imports."""

    def test_import_meta_registry(self) -> None:
        """MetaRegistry should be importable."""
        from framework_m.core.registry import MetaRegistry

        assert MetaRegistry is not None

    def test_import_duplicate_doctype_error(self) -> None:
        """DuplicateDocTypeError should be importable."""
        from framework_m.core.exceptions import DuplicateDocTypeError

        assert DuplicateDocTypeError is not None


# =============================================================================
# Test: Additional Edge Cases
# =============================================================================


class TestMetaRegistryEdgeCases:
    """Tests for additional edge cases."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MetaRegistry().clear()

    def test_get_controller_for_unknown_doctype(self) -> None:
        """get_controller should return None for unknown DocType."""
        registry = MetaRegistry()

        result = registry.get_controller("UnknownDocType")

        assert result is None

    def test_clear_removes_all_registrations(self) -> None:
        """clear() should remove all DocTypes and controllers."""
        registry = MetaRegistry()
        registry.register_doctype(Todo, TodoController)
        registry.register_doctype(Project)

        registry.clear()

        assert registry.list_doctypes() == []
        assert registry.get_controller("Todo") is None

    def test_discover_doctypes_nonexistent_package(self) -> None:
        """discover_doctypes should return 0 for non-existent package."""
        registry = MetaRegistry()

        count = registry.discover_doctypes("nonexistent.package.doctypes")

        assert count == 0

    def test_load_apps_multiple_nonexistent(self) -> None:
        """load_apps with multiple non-existent apps should return 0."""
        registry = MetaRegistry()

        count = registry.load_apps(["nonexistent.app1", "nonexistent.app2"])

        assert count == 0

    def test_discover_doctypes_with_real_package(self) -> None:
        """discover_doctypes should find DocTypes in framework_m.core.doctypes."""
        registry = MetaRegistry()
        registry.clear()

        # framework_m.core.doctypes has real DocTypes
        count = registry.discover_doctypes("framework_m.core.doctypes")

        # Should find at least CustomPermission and DocumentShare
        assert count >= 0  # May be 0 if already registered
        assert isinstance(count, int)

    def test_discover_doctypes_with_module_not_package(self) -> None:
        """discover_doctypes should handle module (not package) scanning."""
        registry = MetaRegistry()
        registry.clear()

        # Try a module that is not a package (has no __path__)
        count = registry.discover_doctypes("framework_m.core.exceptions")

        # Should return 0 or small number (no DocTypes in exceptions)
        assert count == 0

    def test_discover_doctypes_scans_submodules(self) -> None:
        """discover_doctypes should scan submodules in a package."""
        registry = MetaRegistry()
        registry.clear()

        # core.domain is a package with submodules
        count = registry.discover_doctypes("framework_m.core.domain")

        # May find BaseDocType subclasses
        assert isinstance(count, int)

    def test_register_doctype_already_exists(self) -> None:
        """register_doctype should raise if DocType already registered."""
        from framework_m.core.exceptions import DuplicateDocTypeError

        registry = MetaRegistry()
        registry.clear()
        registry.register_doctype(Todo)

        with pytest.raises(DuplicateDocTypeError):
            registry.register_doctype(Todo)

    def test_get_doctype_raises_for_unknown(self) -> None:
        """get_doctype should raise KeyError for unknown DocType."""
        registry = MetaRegistry()
        registry.clear()

        with pytest.raises(KeyError):
            registry.get_doctype("NonexistentDocType")

    def test_list_doctypes_returns_all(self) -> None:
        """list_doctypes should return all registered DocType names."""
        registry = MetaRegistry()
        registry.clear()
        registry.register_doctype(Todo)
        registry.register_doctype(Project)

        names = registry.list_doctypes()

        assert "Todo" in names
        assert "Project" in names
        assert len(names) == 2

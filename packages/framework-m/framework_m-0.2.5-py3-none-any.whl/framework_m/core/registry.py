"""Meta Registry - Central registry for DocTypes and Controllers.

This module provides the MetaRegistry singleton that tracks all registered
DocTypes and their associated controllers. It supports automatic discovery
of DocTypes from packages and enforces globally unique DocType names.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import TYPE_CHECKING, Any

from framework_m.core.exceptions import DuplicateDocTypeError

if TYPE_CHECKING:
    from framework_m.core.domain.base_controller import BaseController
    from framework_m.core.domain.base_doctype import BaseDocType


class MetaRegistry:
    """
    Singleton registry for DocTypes and Controllers.

    The MetaRegistry is the central store for all DocType metadata.
    It maps DocType names to their classes and optional controllers.

    DocType Uniqueness:
        Framework M enforces globally unique DocType names across all
        installed apps. Attempting to register a duplicate name will
        raise DuplicateDocTypeError.

    Example:
        registry = MetaRegistry()

        # Register a DocType
        registry.register_doctype(Todo, TodoController)

        # Get DocType class
        TodoClass = registry.get_doctype("Todo")

        # Get controller
        ControllerClass = registry.get_controller("Todo")

        # Load DocTypes from installed apps in order
        registry.load_apps(["app1", "app2", "app3"])
    """

    _instance: MetaRegistry | None = None
    _initialized: bool = False

    # Instance attributes - declared here for mypy
    _doctypes: dict[str, type[BaseDocType]]
    _controllers: dict[str, type[BaseController[Any]]]
    _doctype_sources: dict[str, str]  # Maps doctype name to source module
    _overrides: dict[str, type[BaseDocType]]  # Maps doctype name to override class

    def __new__(cls) -> MetaRegistry:
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry (only once)."""
        if not MetaRegistry._initialized:
            self._doctypes = {}
            self._controllers = {}
            self._doctype_sources = {}
            self._overrides = {}
            MetaRegistry._initialized = True

    @classmethod
    def get_instance(cls) -> MetaRegistry:
        """Get the singleton instance."""
        return cls()

    def register_doctype(
        self,
        doctype_class: type[BaseDocType],
        controller_class: type[BaseController[Any]] | None = None,
    ) -> None:
        """
        Register a DocType with optional controller.

        Args:
            doctype_class: The DocType class to register
            controller_class: Optional controller class for this DocType

        Raises:
            DuplicateDocTypeError: If a DocType with the same name is already
                registered. Framework M requires globally unique DocType names.
        """
        name = doctype_class.get_doctype_name()
        new_module = doctype_class.__module__

        # Check for duplicate registration
        if name in self._doctypes:
            existing_module = self._doctype_sources.get(name)
            raise DuplicateDocTypeError(
                doctype_name=name,
                existing_module=existing_module,
                new_module=new_module,
            )

        self._doctypes[name] = doctype_class
        self._doctype_sources[name] = new_module
        if controller_class is not None:
            self._controllers[name] = controller_class

    def get_doctype(self, name: str) -> type[BaseDocType]:
        """
        Get a registered DocType class by name.

        If an override is registered for this DocType, returns the override
        class instead of the base class.

        Args:
            name: The DocType name

        Returns:
            The DocType class (or override if registered)

        Raises:
            KeyError: If DocType is not registered
        """
        if name not in self._doctypes:
            raise KeyError(f"DocType '{name}' not registered")

        # Return override if registered, otherwise return base
        if name in self._overrides:
            return self._overrides[name]

        return self._doctypes[name]

    def get_controller(self, name: str) -> type[BaseController[Any]] | None:
        """
        Get a registered controller class by DocType name.

        Args:
            name: The DocType name

        Returns:
            The controller class, or None if not registered
        """
        return self._controllers.get(name)

    def list_doctypes(self) -> list[str]:
        """
        List all registered DocType names.

        Returns:
            List of DocType names
        """
        return list(self._doctypes.keys())

    def register_override(
        self,
        base_doctype: str,
        override_class: type[BaseDocType],
    ) -> None:
        """
        Register an override for a DocType.

        The override class must inherit from the base DocType. When get_doctype()
        is called for the base DocType, the override class will be returned instead.

        Only one override per base DocType is allowed. This enforces a clear
        override hierarchy and prevents ambiguity.

        Args:
            base_doctype: Name of the base DocType to override
            override_class: The override class (must inherit from base)

        Raises:
            KeyError: If base DocType is not registered
            ValueError: If override doesn't inherit from base or if an override
                already exists for this base DocType
        """
        # Check that base DocType is registered
        if base_doctype not in self._doctypes:
            raise KeyError(f"Base DocType '{base_doctype}' not registered")

        base_class = self._doctypes[base_doctype]

        # Validate that override inherits from base
        if not issubclass(override_class, base_class):
            raise ValueError(
                f"Override class must inherit from base DocType '{base_doctype}'"
            )

        # Check if an override already exists
        if base_doctype in self._overrides:
            existing_override = self._overrides[base_doctype]
            raise ValueError(
                f"DocType '{base_doctype}' already has an override registered: "
                f"{existing_override.__name__}"
            )

        # Register the override
        self._overrides[base_doctype] = override_class

    def has_override(self, doctype_name: str) -> bool:
        """
        Check if a DocType has an override registered.

        Args:
            doctype_name: The DocType name

        Returns:
            True if an override is registered, False otherwise
        """
        return doctype_name in self._overrides

    def get_override_class(self, doctype_name: str) -> type[BaseDocType] | None:
        """
        Get the override class for a DocType.

        Args:
            doctype_name: The DocType name

        Returns:
            The override class, or None if no override registered
        """
        return self._overrides.get(doctype_name)

    def load_apps(self, installed_apps: list[str]) -> int:
        """
        Load DocTypes from installed apps in order.

        Scans each app package in the order specified and registers
        any discovered DocTypes. This respects the load order, so
        earlier apps in the list are registered first.

        Args:
            installed_apps: List of app package names to load, in order

        Returns:
            Total number of DocTypes discovered across all apps
        """
        total = 0
        for app_name in installed_apps:
            count = self.discover_doctypes(app_name)
            total += count
        return total

    def discover_doctypes(self, package_name: str) -> int:
        """
        Discover and register DocTypes from a package.

        Scans all modules in the package for BaseDocType subclasses
        and registers them automatically. Raises DuplicateDocTypeError
        if a DocType name conflicts with an already registered one.

        Args:
            package_name: The package to scan (e.g., "myapp.doctypes")

        Returns:
            Number of DocTypes discovered and registered
        """
        # Import here to avoid circular imports
        from framework_m.core.domain.base_doctype import BaseDocType

        count = 0
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            return 0

        # Get package path for iteration
        package_path = getattr(package, "__path__", None)
        if package_path is None:
            # It's a module, not a package - scan it directly
            for _, obj in inspect.getmembers(package, inspect.isclass):
                if issubclass(obj, BaseDocType) and obj is not BaseDocType:
                    name = obj.get_doctype_name()
                    if name not in self._doctypes:
                        self.register_doctype(obj)
                        count += 1
            return count

        # Iterate through submodules
        for _, module_name, _ in pkgutil.walk_packages(
            package_path, prefix=f"{package_name}."
        ):
            try:
                module = importlib.import_module(module_name)
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseDocType) and obj is not BaseDocType:
                        name = obj.get_doctype_name()
                        if name not in self._doctypes:
                            self.register_doctype(obj)
                            count += 1
            except ImportError:
                continue

        return count

    def clear(self) -> None:
        """
        Clear all registered DocTypes, controllers, and overrides.

        Primarily used for testing.
        """
        self._doctypes.clear()
        self._controllers.clear()
        self._doctype_sources.clear()
        self._overrides.clear()


__all__ = ["MetaRegistry"]

"""Field Registry - Maps Python types to SQLAlchemy column types.

This module provides a singleton registry that handles type conversion
from Python/Pydantic types to SQLAlchemy column types. All mappings
are database-agnostic, avoiding PostgreSQL-specific types.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, get_origin
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, String
from sqlalchemy.types import JSON, TypeEngine
from sqlalchemy.types import UUID as SA_UUID


@dataclass
class FieldTypeInfo:
    """Metadata about a field type for Studio UI.

    Contains all information needed by the Studio UI to render
    field type selectors and generate code.

    Attributes:
        name: Unique identifier for the type (e.g., "str", "int").
        pydantic_type: The Python/Pydantic type string (e.g., "str", "datetime").
        label: Human-readable label for UI display (e.g., "Text", "Integer").
        ui_widget: The widget type for rendering (e.g., "text", "number", "checkbox").
        sqlalchemy_type: Optional SQLAlchemy type name (e.g., "String", "Integer").
        description: Optional description for tooltips.
    """

    name: str
    pydantic_type: str
    label: str
    ui_widget: str
    sqlalchemy_type: str | None = None
    description: str | None = None
    category: str | None = None
    validators: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "pydantic_type": self.pydantic_type,
            "label": self.label,
            "ui_widget": self.ui_widget,
            "sqlalchemy_type": self.sqlalchemy_type,
            "description": self.description,
            "category": self.category,
            "validators": self.validators,
        }


class FieldRegistry:
    """Singleton registry for Python to SQLAlchemy type mappings.

    The FieldRegistry provides a central place to define how Python types
    are mapped to SQLAlchemy column types. It supports:

    - Standard Python types (str, int, float, bool, etc.)
    - Generic types (list[str], dict[str, Any], etc.)
    - Custom type registration for plugins

    All mappings are database-agnostic, using portable SQL types that
    work with both SQLite and PostgreSQL.

    Example:
        registry = FieldRegistry()

        # Get SQLAlchemy type for Python type
        sa_type = registry.get_sqlalchemy_type(str)  # Returns String

        # Register custom type
        registry.register_type(MyCustomType, MyCustomSQLType)
    """

    _instance: FieldRegistry | None = None
    _initialized: bool = False

    # Instance attributes
    _type_map: dict[type, type[TypeEngine[Any]] | TypeEngine[Any]]

    def __new__(cls) -> FieldRegistry:
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry with standard type mappings."""
        if not FieldRegistry._initialized:
            self._type_map = {}
            self._ui_types: list[FieldTypeInfo] = []
            self._register_standard_types()
            FieldRegistry._initialized = True

    @classmethod
    def get_instance(cls) -> FieldRegistry:
        """Get the singleton instance."""
        return cls()

    def _register_standard_types(self) -> None:
        """Register standard Python to SQLAlchemy type mappings.

        All types are database-agnostic and work with SQLite and PostgreSQL.
        """
        self._type_map = {
            # Core Python types
            str: String,
            int: Integer,
            float: Float,
            bool: Boolean,
            # Date/time types
            datetime: DateTime(timezone=True),
            date: Date,
            # Numeric types
            Decimal: Numeric,
            # Special types
            UUID: SA_UUID,
            # Container types - use JSON for database agnosticism
            dict: JSON,
            list: JSON,
        }

        # UI metadata for Studio field type selector
        self._ui_types = [
            FieldTypeInfo("str", "str", "Text", "text", "String"),
            FieldTypeInfo("int", "int", "Integer", "number", "Integer"),
            FieldTypeInfo("float", "float", "Decimal", "number", "Float"),
            FieldTypeInfo("bool", "bool", "Checkbox", "checkbox", "Boolean"),
            FieldTypeInfo("date", "date", "Date", "date", "Date"),
            FieldTypeInfo("datetime", "datetime", "DateTime", "datetime", "DateTime"),
            FieldTypeInfo("UUID", "UUID", "UUID", "text", "UUID"),
            FieldTypeInfo("Decimal", "Decimal", "Currency", "number", "Numeric"),
            FieldTypeInfo("dict", "dict[str, Any]", "JSON", "json", "JSON"),
            FieldTypeInfo("list", "list[Any]", "List (JSON)", "json", "JSON"),
            # Extended types for Studio
            FieldTypeInfo("text", "str", "Long Text", "textarea", "Text"),
            FieldTypeInfo("email", "EmailStr", "Email", "email", "String"),
            FieldTypeInfo("url", "HttpUrl", "URL", "url", "String"),
            # Relational types
            FieldTypeInfo("Link", "str", "Link (Foreign Key)", "link", "String"),
            FieldTypeInfo("Table", "list[dict]", "Table (Child)", "table", "JSON"),
        ]

    def register_type(
        self,
        python_type: type,
        sqlalchemy_type: type[TypeEngine[Any]] | TypeEngine[Any],
    ) -> None:
        """Register a custom Python to SQLAlchemy type mapping.

        This allows plugins to add support for custom types like
        GeoLocation, Money, etc.

        Args:
            python_type: The Python type class
            sqlalchemy_type: The SQLAlchemy type class or instance to map to
        """
        self._type_map[python_type] = sqlalchemy_type

    def get_sqlalchemy_type(
        self, python_type: type
    ) -> type[TypeEngine[Any]] | TypeEngine[Any]:
        """Get the SQLAlchemy type for a Python type.

        Handles both simple types (str, int) and generic types
        (list[str], dict[str, Any]).

        Args:
            python_type: The Python type to look up

        Returns:
            The corresponding SQLAlchemy type class or instance

        Raises:
            TypeError: If the type is not registered
        """
        # Check for direct mapping first
        if python_type in self._type_map:
            return self._type_map[python_type]

        # Handle generic types (list[str], dict[str, Any], etc.)
        origin = get_origin(python_type)
        if origin is not None:
            # For any generic, check if origin is in type map
            if origin in self._type_map:
                return self._type_map[origin]

            # Handle list and dict specifically
            if origin is list:
                return JSON
            if origin is dict:
                return JSON

        # Type not found - raise helpful error
        type_name = getattr(python_type, "__name__", str(python_type))
        raise TypeError(
            f"No SQLAlchemy type mapping found for '{type_name}'. "
            f"Use register_type({type_name}, SQLAlchemyType) to add a custom mapping."
        )

    def reset(self) -> None:
        """Reset the registry to initial state."""
        self._type_map = {}
        self._ui_types = []
        self._register_standard_types()

    def get_all_types(self) -> list[FieldTypeInfo]:
        """Get all registered field types with UI metadata.

        Returns a list of FieldTypeInfo objects containing type information
        needed by the Studio UI for field type selection and code generation.

        Returns:
            List of FieldTypeInfo objects for all registered types.
        """
        return list(self._ui_types)


__all__ = ["FieldRegistry", "FieldTypeInfo"]

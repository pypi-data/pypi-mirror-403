"""Tests for FieldRegistry - Type mapping from Python to SQLAlchemy types.

TDD: Tests written first, implementation to follow.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, String
from sqlalchemy.types import JSON, TypeEngine
from sqlalchemy.types import UUID as SA_UUID


class TestFieldRegistryImports:
    """Tests for FieldRegistry imports."""

    def test_import_field_registry(self) -> None:
        """FieldRegistry should be importable from adapters.db."""
        from framework_m.adapters.db.field_registry import FieldRegistry

        assert FieldRegistry is not None

    def test_import_from_adapters_db(self) -> None:
        """FieldRegistry should be exported from adapters.db module."""
        from framework_m.adapters.db import FieldRegistry

        assert FieldRegistry is not None


class TestFieldRegistrySingleton:
    """Tests for FieldRegistry singleton behavior."""

    def test_registry_is_singleton(self) -> None:
        """FieldRegistry should be a singleton."""
        from framework_m.adapters.db.field_registry import FieldRegistry

        registry1 = FieldRegistry()
        registry2 = FieldRegistry()

        assert registry1 is registry2

    def test_get_instance(self) -> None:
        """get_instance should return the singleton."""
        from framework_m.adapters.db.field_registry import FieldRegistry

        registry = FieldRegistry.get_instance()

        assert registry is FieldRegistry()


class TestFieldRegistryStandardTypes:
    """Tests for standard Python to SQLAlchemy type mappings."""

    def setup_method(self) -> None:
        """Get fresh registry for each test."""
        from framework_m.adapters.db.field_registry import FieldRegistry

        self.registry = FieldRegistry()

    def test_str_maps_to_string(self) -> None:
        """str should map to SQLAlchemy String."""
        result = self.registry.get_sqlalchemy_type(str)

        assert isinstance(result, type)
        assert issubclass(result, String)

    def test_int_maps_to_integer(self) -> None:
        """int should map to SQLAlchemy Integer."""
        result = self.registry.get_sqlalchemy_type(int)

        assert isinstance(result, type)
        assert issubclass(result, Integer)

    def test_float_maps_to_float(self) -> None:
        """float should map to SQLAlchemy Float."""
        result = self.registry.get_sqlalchemy_type(float)

        assert isinstance(result, type)
        assert issubclass(result, Float)

    def test_bool_maps_to_boolean(self) -> None:
        """bool should map to SQLAlchemy Boolean."""
        result = self.registry.get_sqlalchemy_type(bool)

        assert isinstance(result, type)
        assert issubclass(result, Boolean)

    def test_datetime_maps_to_datetime(self) -> None:
        """datetime should map to SQLAlchemy DateTime."""
        result = self.registry.get_sqlalchemy_type(datetime)

        assert isinstance(result, DateTime)
        assert result.timezone is True

    def test_date_maps_to_date(self) -> None:
        """date should map to SQLAlchemy Date."""
        result = self.registry.get_sqlalchemy_type(date)

        assert isinstance(result, type)
        assert issubclass(result, Date)

    def test_decimal_maps_to_numeric(self) -> None:
        """Decimal should map to SQLAlchemy Numeric."""
        result = self.registry.get_sqlalchemy_type(Decimal)

        assert isinstance(result, type)
        assert issubclass(result, Numeric)

    def test_uuid_maps_to_uuid(self) -> None:
        """UUID should map to SQLAlchemy UUID."""
        result = self.registry.get_sqlalchemy_type(UUID)

        assert isinstance(result, type)
        assert issubclass(result, SA_UUID)

    def test_dict_maps_to_json(self) -> None:
        """dict should map to SQLAlchemy JSON."""
        result = self.registry.get_sqlalchemy_type(dict)

        assert isinstance(result, type)
        assert issubclass(result, JSON)


class TestFieldRegistryGenericTypes:
    """Tests for generic type mappings (list, Optional, etc.)."""

    def setup_method(self) -> None:
        """Get fresh registry for each test."""
        from framework_m.adapters.db.field_registry import FieldRegistry

        self.registry = FieldRegistry()

    def test_list_str_maps_to_json(self) -> None:
        """list[str] should map to JSON (database agnostic)."""
        result = self.registry.get_sqlalchemy_type(list[str])

        assert isinstance(result, type)
        assert issubclass(result, JSON)

    def test_list_int_maps_to_json(self) -> None:
        """list[int] should map to JSON."""
        result = self.registry.get_sqlalchemy_type(list[int])

        assert isinstance(result, type)
        assert issubclass(result, JSON)

    def test_list_any_maps_to_json(self) -> None:
        """list[Any] should map to JSON."""
        result = self.registry.get_sqlalchemy_type(list[Any])

        assert isinstance(result, type)
        assert issubclass(result, JSON)

    def test_dict_str_any_maps_to_json(self) -> None:
        """dict[str, Any] should map to JSON."""
        result = self.registry.get_sqlalchemy_type(dict[str, Any])

        assert isinstance(result, type)
        assert issubclass(result, JSON)


class TestFieldRegistryCustomTypes:
    """Tests for custom type registration."""

    def setup_method(self) -> None:
        """Get fresh registry for each test."""
        from framework_m.adapters.db.field_registry import FieldRegistry

        self.registry = FieldRegistry()

    def test_register_custom_type(self) -> None:
        """register_type should add custom type mapping."""

        class CustomPythonType:
            pass

        class CustomSQLType(TypeEngine[Any]):
            pass

        self.registry.register_type(CustomPythonType, CustomSQLType)

        result = self.registry.get_sqlalchemy_type(CustomPythonType)
        assert result is CustomSQLType

    def test_override_standard_type(self) -> None:
        """register_type should allow overriding standard mappings."""
        from sqlalchemy import Text

        # Override str to map to Text instead of String
        self.registry.register_type(str, Text)

        result = self.registry.get_sqlalchemy_type(str)
        assert issubclass(result, Text)


class TestFieldRegistryUnknownTypes:
    """Tests for unknown type handling."""

    def setup_method(self) -> None:
        """Get fresh registry for each test."""
        from framework_m.adapters.db.field_registry import FieldRegistry

        self.registry = FieldRegistry()

    def test_unknown_type_raises_error(self) -> None:
        """Unknown types should raise TypeError."""

        class UnknownType:
            pass

        with pytest.raises(TypeError) as exc_info:
            self.registry.get_sqlalchemy_type(UnknownType)

        assert "UnknownType" in str(exc_info.value)

    def test_error_message_is_helpful(self) -> None:
        """Error message should suggest using register_type."""

        class MyCustomType:
            pass

        with pytest.raises(TypeError) as exc_info:
            self.registry.get_sqlalchemy_type(MyCustomType)

        assert "register_type" in str(exc_info.value)


class TestFieldTypeInfo:
    """Tests for FieldTypeInfo dataclass for Studio UI metadata."""

    def test_import_field_type_info(self) -> None:
        """FieldTypeInfo should be importable from adapters.db."""
        from framework_m.adapters.db.field_registry import FieldTypeInfo

        assert FieldTypeInfo is not None

    def test_field_type_info_has_required_fields(self) -> None:
        """FieldTypeInfo should have name, pydantic_type, label, ui_widget."""
        from framework_m.adapters.db.field_registry import FieldTypeInfo

        info = FieldTypeInfo(
            name="str",
            pydantic_type="str",
            label="Text",
            ui_widget="text",
        )

        assert info.name == "str"
        assert info.pydantic_type == "str"
        assert info.label == "Text"
        assert info.ui_widget == "text"

    def test_field_type_info_has_optional_sqlalchemy_type(self) -> None:
        """FieldTypeInfo should have optional sqlalchemy_type."""
        from framework_m.adapters.db.field_registry import FieldTypeInfo

        info = FieldTypeInfo(
            name="str",
            pydantic_type="str",
            label="Text",
            ui_widget="text",
            sqlalchemy_type="String",
        )

        assert info.sqlalchemy_type == "String"

    def test_field_type_info_to_dict(self) -> None:
        """FieldTypeInfo should be serializable to dict."""
        from framework_m.adapters.db.field_registry import FieldTypeInfo

        info = FieldTypeInfo(
            name="str",
            pydantic_type="str",
            label="Text",
            ui_widget="text",
        )
        result = info.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "str"
        assert result["label"] == "Text"


class TestFieldRegistryGetAllTypes:
    """Tests for get_all_types method returning Studio UI metadata."""

    def setup_method(self) -> None:
        """Get fresh registry for each test."""
        from framework_m.adapters.db.field_registry import FieldRegistry

        self.registry = FieldRegistry()

    def test_get_all_types_returns_list(self) -> None:
        """get_all_types should return a list."""
        result = self.registry.get_all_types()

        assert isinstance(result, list)

    def test_get_all_types_includes_standard_types(self) -> None:
        """get_all_types should include all standard types."""
        result = self.registry.get_all_types()
        type_names = [t.name for t in result]

        assert "str" in type_names
        assert "int" in type_names
        assert "float" in type_names
        assert "bool" in type_names
        assert "datetime" in type_names
        assert "date" in type_names

    def test_get_all_types_returns_field_type_info(self) -> None:
        """get_all_types should return list of FieldTypeInfo."""
        from framework_m.adapters.db.field_registry import FieldTypeInfo

        result = self.registry.get_all_types()

        assert all(isinstance(t, FieldTypeInfo) for t in result)

    def test_get_all_types_includes_ui_metadata(self) -> None:
        """Each type should have label and ui_widget."""
        result = self.registry.get_all_types()

        for type_info in result:
            assert type_info.label, f"Type {type_info.name} missing label"
            assert type_info.ui_widget, f"Type {type_info.name} missing ui_widget"

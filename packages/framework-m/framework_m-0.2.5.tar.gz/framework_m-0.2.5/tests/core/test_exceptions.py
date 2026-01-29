"""Tests for exception classes.

Tests the custom exception classes used throughout Framework M.
"""

from __future__ import annotations


class TestFrameworkError:
    """Tests for base FrameworkError."""

    def test_is_exception(self) -> None:
        """FrameworkError should be an Exception."""
        from framework_m.core.exceptions import FrameworkError

        assert issubclass(FrameworkError, Exception)


class TestDocTypeNotFoundError:
    """Tests for DocTypeNotFoundError."""

    def test_message_includes_doctype_name(self) -> None:
        """Exception message should include the doctype name."""
        from framework_m.core.exceptions import DocTypeNotFoundError

        error = DocTypeNotFoundError("MyDocType")
        assert "MyDocType" in str(error)
        assert error.doctype_name == "MyDocType"

    def test_inherits_from_framework_error(self) -> None:
        """DocTypeNotFoundError should inherit from FrameworkError."""
        from framework_m.core.exceptions import DocTypeNotFoundError, FrameworkError

        assert issubclass(DocTypeNotFoundError, FrameworkError)


class TestDuplicateDocTypeError:
    """Tests for DuplicateDocTypeError."""

    def test_message_includes_all_info(self) -> None:
        """Exception message should include doctype, existing, and new module."""
        from framework_m.core.exceptions import DuplicateDocTypeError

        error = DuplicateDocTypeError(
            doctype_name="Todo",
            existing_module="app1.doctypes",
            new_module="app2.doctypes",
        )
        message = str(error)
        assert "Todo" in message
        assert "app1.doctypes" in message
        assert "app2.doctypes" in message

    def test_minimal_message(self) -> None:
        """Exception with no module info should still work."""
        from framework_m.core.exceptions import DuplicateDocTypeError

        error = DuplicateDocTypeError(doctype_name="Todo")
        assert "Todo" in str(error)
        assert error.doctype_name == "Todo"

    def test_with_existing_module_only(self) -> None:
        """Exception with only existing_module."""
        from framework_m.core.exceptions import DuplicateDocTypeError

        error = DuplicateDocTypeError(doctype_name="Todo", existing_module="app1")
        assert "Todo" in str(error)
        assert "app1" in str(error)


class TestValidationError:
    """Tests for ValidationError."""

    def test_can_be_raised(self) -> None:
        """ValidationError should be raisable with message."""
        from framework_m.core.exceptions import ValidationError

        error = ValidationError("Field 'email' is required")
        assert "email" in str(error)

    def test_inherits_from_framework_error(self) -> None:
        """ValidationError should inherit from FrameworkError."""
        from framework_m.core.exceptions import FrameworkError, ValidationError

        assert issubclass(ValidationError, FrameworkError)


class TestPermissionDeniedError:
    """Tests for PermissionDeniedError."""

    def test_can_be_raised(self) -> None:
        """PermissionDeniedError should be raisable."""
        from framework_m.core.exceptions import PermissionDeniedError

        error = PermissionDeniedError("User lacks write permission on Invoice")
        assert "Invoice" in str(error)

    def test_inherits_from_framework_error(self) -> None:
        """PermissionDeniedError should inherit from FrameworkError."""
        from framework_m.core.exceptions import FrameworkError, PermissionDeniedError

        assert issubclass(PermissionDeniedError, FrameworkError)


class TestVersionConflictError:
    """Tests for VersionConflictError."""

    def test_message_includes_doctype_and_id(self) -> None:
        """Exception message should include doctype and doc_id."""
        from framework_m.core.exceptions import VersionConflictError

        error = VersionConflictError(doctype_name="Invoice", doc_id="INV-001")
        message = str(error)
        assert "Invoice" in message
        assert "INV-001" in message
        assert error.doctype_name == "Invoice"
        assert error.doc_id == "INV-001"


class TestDuplicateNameError:
    """Tests for DuplicateNameError."""

    def test_message_includes_doctype_and_name(self) -> None:
        """Exception message should include doctype and name."""
        from framework_m.core.exceptions import DuplicateNameError

        error = DuplicateNameError(doctype_name="Customer", name="CUST-001")
        message = str(error)
        assert "Customer" in message
        assert "CUST-001" in message
        assert error.doctype_name == "Customer"
        assert error.name == "CUST-001"


class TestRepositoryError:
    """Tests for RepositoryError."""

    def test_is_framework_error(self) -> None:
        """RepositoryError should inherit from FrameworkError."""
        from framework_m.core.exceptions import FrameworkError, RepositoryError

        assert issubclass(RepositoryError, FrameworkError)


class TestEntityNotFoundError:
    """Tests for EntityNotFoundError."""

    def test_message_includes_doctype_and_id(self) -> None:
        """Exception message should include doctype and entity_id."""
        from framework_m.core.exceptions import EntityNotFoundError

        error = EntityNotFoundError(doctype_name="Order", entity_id="ORD-123")
        message = str(error)
        assert "Order" in message
        assert "ORD-123" in message
        assert error.doctype_name == "Order"
        assert error.entity_id == "ORD-123"


class TestDatabaseError:
    """Tests for DatabaseError."""

    def test_message_includes_operation(self) -> None:
        """DatabaseError should include operation and message."""
        from framework_m.core.exceptions import DatabaseError

        error = DatabaseError(operation="INSERT", message="Connection refused")
        message = str(error)
        assert "INSERT" in message
        assert "Connection refused" in message
        assert error.operation == "INSERT"


class TestIntegrityError:
    """Tests for IntegrityError."""

    def test_message_includes_description(self) -> None:
        """IntegrityError should include the constraint message."""
        from framework_m.core.exceptions import IntegrityError

        error = IntegrityError(message="unique constraint on email failed")
        assert "unique constraint" in str(error)


class TestExceptionImports:
    """Tests for exception module imports."""

    def test_all_exceptions_importable(self) -> None:
        """All exceptions should be importable from core.exceptions."""
        from framework_m.core.exceptions import (
            DatabaseError,
            DocTypeNotFoundError,
            DuplicateDocTypeError,
            DuplicateNameError,
            EntityNotFoundError,
            FrameworkError,
            IntegrityError,
            PermissionDeniedError,
            RepositoryError,
            ValidationError,
            VersionConflictError,
        )

        assert DocTypeNotFoundError is not None
        assert DuplicateDocTypeError is not None
        assert ValidationError is not None
        assert PermissionDeniedError is not None
        assert DuplicateNameError is not None
        assert RepositoryError is not None
        assert EntityNotFoundError is not None
        assert DatabaseError is not None
        assert IntegrityError is not None
        assert FrameworkError is not None
        assert VersionConflictError is not None

"""Framework M exceptions.

This module defines custom exceptions used throughout the framework.
"""


class FrameworkError(Exception):
    """Base exception for all framework errors."""

    pass


class DuplicateDocTypeError(FrameworkError):
    """Raised when attempting to register a DocType with a name that already exists.

    Framework M enforces globally unique DocType names across all installed apps.
    This prevents naming collisions and ambiguity in the modular monolith pattern.

    Attributes:
        doctype_name: The duplicate DocType name
        existing_module: Module where the existing DocType is defined
        new_module: Module attempting to register the duplicate
    """

    def __init__(
        self,
        doctype_name: str,
        existing_module: str | None = None,
        new_module: str | None = None,
    ) -> None:
        self.doctype_name = doctype_name
        self.existing_module = existing_module
        self.new_module = new_module

        message = f"DocType '{doctype_name}' is already registered"
        if existing_module:
            message += f" from '{existing_module}'"
        if new_module:
            message += f". Cannot register from '{new_module}'"

        super().__init__(message)


class DocTypeNotFoundError(FrameworkError):
    """Raised when a DocType is not found in the registry."""

    def __init__(self, doctype_name: str) -> None:
        self.doctype_name = doctype_name
        super().__init__(f"DocType '{doctype_name}' not found in registry")


class ValidationError(FrameworkError):
    """Raised when document validation fails."""

    pass


class PermissionDeniedError(FrameworkError):
    """Raised when a user lacks permission for an operation."""

    pass


class AuthenticationError(FrameworkError):
    """Raised when authentication fails.

    Examples:
        - Invalid credentials (wrong password)
        - Expired or invalid token
        - User not found
    """

    pass


class VersionConflictError(FrameworkError):
    """Raised when optimistic concurrency check fails."""

    def __init__(self, doctype_name: str, doc_id: str) -> None:
        self.doctype_name = doctype_name
        self.doc_id = doc_id
        super().__init__(
            f"Version conflict: {doctype_name} '{doc_id}' was modified by another user"
        )


class DuplicateNameError(FrameworkError):
    """Raised when attempting to create a document with a duplicate name."""

    def __init__(self, doctype_name: str, name: str) -> None:
        self.doctype_name = doctype_name
        self.name = name
        super().__init__(f"{doctype_name} with name '{name}' already exists")


# =============================================================================
# Repository Exceptions
# =============================================================================


class RepositoryError(FrameworkError):
    """Base exception for repository-related errors."""

    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found in the repository."""

    def __init__(self, doctype_name: str, entity_id: str) -> None:
        self.doctype_name = doctype_name
        self.entity_id = entity_id
        super().__init__(f"{doctype_name} with id '{entity_id}' not found")


class DatabaseError(RepositoryError):
    """Raised when a database operation fails."""

    def __init__(self, operation: str, message: str) -> None:
        self.operation = operation
        super().__init__(f"Database {operation} failed: {message}")


class IntegrityError(RepositoryError):
    """Raised when a database integrity constraint is violated."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Integrity constraint violation: {message}")


__all__ = [
    "AuthenticationError",
    "DatabaseError",
    "DocTypeNotFoundError",
    "DuplicateDocTypeError",
    "DuplicateNameError",
    "EntityNotFoundError",
    "FrameworkError",
    "IntegrityError",
    "PermissionDeniedError",
    "RepositoryError",
    "ValidationError",
    "VersionConflictError",
]

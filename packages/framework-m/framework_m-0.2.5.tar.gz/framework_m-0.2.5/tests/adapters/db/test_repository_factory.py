"""Tests for RepositoryFactory and custom repositories."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Column, MetaData, String, Table

from framework_m import DocType, Field
from framework_m.adapters.db.repository_factory import RepositoryFactory
from framework_m.core.interfaces.repository import RepositoryProtocol

# =============================================================================
# Test DocTypes and Custom Repositories
# =============================================================================


class VirtualDoc(DocType):
    """A virtual DocType backed by custom repository."""

    title: str = Field(description="Document title")
    content: str = Field(default="", description="Document content")

    class Meta:
        """Metadata for VirtualDoc."""

        repository_class = "tests.adapters.db.test_repository_factory.FileRepository"


class RegularDoc(DocType):
    """A regular DocType using default repository."""

    name_field: str = Field(description="Name")


class FileRepository(RepositoryProtocol["VirtualDoc"]):
    """Mock file-based repository for testing.

    Uses name (string) as identifier with a UUID->name mapping.
    """

    def __init__(self) -> None:
        """Initialize with in-memory storage."""
        self._storage: dict[str, dict[str, Any]] = {}  # name -> data
        self._uuid_to_name: dict[UUID, str] = {}  # uuid -> name

    async def get(self, id: UUID) -> VirtualDoc | None:
        """Get a document by ID (UUID mapped to name)."""
        name = self._uuid_to_name.get(id)
        if name is None:
            return None
        data = self._storage.get(name)
        if data is None:
            return None
        return VirtualDoc(**data)

    async def save(self, entity: VirtualDoc, version: int | None = None) -> VirtualDoc:
        """Save a document using name as key."""
        # Generate name if not provided
        if entity.name is None:
            entity.name = f"VDOC-{uuid4().hex[:8].upper()}"

        # Create a UUID for this document
        doc_uuid = uuid4()
        self._uuid_to_name[doc_uuid] = entity.name
        self._storage[entity.name] = entity.model_dump()

        # Store the UUID on the returned entity for testing
        return entity

    async def delete(self, id: UUID) -> None:
        """Delete a document by ID."""
        name = self._uuid_to_name.pop(id, None)
        if name:
            self._storage.pop(name, None)

    async def exists(self, id: UUID) -> bool:
        """Check if document exists by ID."""
        return id in self._uuid_to_name

    async def count(self, filters: Any = None) -> int:
        """Count documents."""
        return len(self._storage)

    async def list_entities(
        self,
        filters: Any = None,
        order_by: Any = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[VirtualDoc]:
        """List documents."""
        items = [VirtualDoc(**data) for data in self._storage.values()]
        return items[offset : offset + limit]

    async def bulk_save(self, entities: Sequence[VirtualDoc]) -> Sequence[VirtualDoc]:
        """Bulk save documents."""
        for entity in entities:
            await self.save(entity)
        return entities

    # Helper method for testing
    def get_uuid_for_name(self, name: str) -> UUID | None:
        """Get UUID for a document name (test helper)."""
        for uuid, doc_name in self._uuid_to_name.items():
            if doc_name == name:
                return uuid
        return None


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def metadata() -> MetaData:
    """Create SQLAlchemy MetaData with test tables."""
    meta = MetaData()
    # Create a test table for RegularDoc
    Table(
        "regulardoc",
        meta,
        Column("id", String, primary_key=True),
        Column("name", String, unique=True),
        Column("name_field", String),
    )
    return meta


@pytest.fixture
def session_factory() -> MagicMock:
    """Create mock SessionFactory."""
    return MagicMock()


@pytest.fixture
def repo_factory(metadata: MetaData, session_factory: MagicMock) -> RepositoryFactory:
    """Create a RepositoryFactory instance for testing."""
    return RepositoryFactory(metadata, session_factory)


# =============================================================================
# Tests
# =============================================================================


class TestRepositoryFactoryConstruction:
    """Tests for RepositoryFactory construction."""

    def test_repository_factory_accepts_metadata_and_session_factory(
        self, metadata: MetaData, session_factory: MagicMock
    ) -> None:
        """RepositoryFactory should accept metadata and session_factory args."""
        factory = RepositoryFactory(metadata, session_factory)
        assert factory.metadata is metadata
        assert factory.session_factory is session_factory

    def test_repository_factory_has_empty_repos_initially(
        self, repo_factory: RepositoryFactory
    ) -> None:
        """RepositoryFactory should have no cached repos initially."""
        assert repo_factory.list_overrides() == []


class TestRepositoryOverride:
    """Tests for repository override functionality."""

    def test_register_override(self, repo_factory: RepositoryFactory) -> None:
        """register_override() should store a custom repository class."""
        repo_factory.register_override("VirtualDoc", FileRepository)
        assert repo_factory.has_override("VirtualDoc")

    def test_has_override_returns_false_for_unregistered(
        self, repo_factory: RepositoryFactory
    ) -> None:
        """has_override() should return False for unregistered DocTypes."""
        assert repo_factory.has_override("NonExistent") is False

    def test_get_override_returns_class(self, repo_factory: RepositoryFactory) -> None:
        """get_override() should return the registered repository class."""
        repo_factory.register_override("VirtualDoc", FileRepository)
        repo_class = repo_factory.get_override("VirtualDoc")
        assert repo_class is FileRepository

    def test_get_override_raises_for_unregistered(
        self, repo_factory: RepositoryFactory
    ) -> None:
        """get_override() should raise KeyError for unregistered DocTypes."""
        with pytest.raises(KeyError):
            repo_factory.get_override("NonExistent")


class TestGetRepository:
    """Tests for get_repository method."""

    def test_get_repository_returns_none_for_missing_table(
        self, repo_factory: RepositoryFactory
    ) -> None:
        """get_repository() should return None if table not in metadata."""
        # VirtualDoc table doesn't exist in metadata
        repo = repo_factory.get_repository(VirtualDoc)
        assert repo is None

    def test_get_repository_returns_repository_for_existing_table(
        self, metadata: MetaData, session_factory: MagicMock
    ) -> None:
        """get_repository() should return GenericRepository if table exists."""
        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.core.registry import MetaRegistry

        # Clear and register RegularDoc
        MetaRegistry.get_instance()._doctypes.clear()
        MetaRegistry.get_instance().register_doctype(RegularDoc)

        factory = RepositoryFactory(metadata, session_factory)
        repo = factory.get_repository(RegularDoc)

        assert isinstance(repo, GenericRepository)
        assert repo.model is RegularDoc

    def test_get_repository_caches_instances(
        self, metadata: MetaData, session_factory: MagicMock
    ) -> None:
        """get_repository() should cache and return same instance."""
        from framework_m.core.registry import MetaRegistry

        MetaRegistry.get_instance()._doctypes.clear()
        MetaRegistry.get_instance().register_doctype(RegularDoc)

        factory = RepositoryFactory(metadata, session_factory)
        repo1 = factory.get_repository(RegularDoc)
        repo2 = factory.get_repository(RegularDoc)

        assert repo1 is repo2


class TestListOverrides:
    """Tests for listing overrides."""

    def test_list_overrides_empty(self, repo_factory: RepositoryFactory) -> None:
        """list_overrides() should return empty list when no overrides."""
        assert repo_factory.list_overrides() == []

    def test_list_overrides_returns_all(self, repo_factory: RepositoryFactory) -> None:
        """list_overrides() should return all registered DocType names."""
        repo_factory.register_override("VirtualDoc", FileRepository)
        repo_factory.register_override("AnotherDoc", FileRepository)

        overrides = repo_factory.list_overrides()
        assert set(overrides) == {"VirtualDoc", "AnotherDoc"}


class TestCustomRepository:
    """Tests for custom repository functionality."""

    @pytest.mark.asyncio
    async def test_custom_repository_works(
        self, repo_factory: RepositoryFactory
    ) -> None:
        """Custom repository should implement RepositoryProtocol correctly."""
        repo_factory.register_override("VirtualDoc", FileRepository)

        # Get override and instantiate
        repo_class = repo_factory.get_override("VirtualDoc")
        repo = repo_class()
        assert isinstance(repo, FileRepository)

        # Test save
        doc = VirtualDoc(title="Test", content="Hello", name="TEST-001")
        await repo.save(doc)

        # Get UUID for the saved doc
        doc_uuid = repo.get_uuid_for_name("TEST-001")
        assert doc_uuid is not None

        # Test get
        retrieved = await repo.get(doc_uuid)
        assert retrieved is not None
        assert retrieved.title == "Test"

        # Test exists
        assert await repo.exists(doc_uuid) is True

        # Test delete
        await repo.delete(doc_uuid)
        assert await repo.exists(doc_uuid) is False


class TestRepositoryFactoryImport:
    """Tests for RepositoryFactory imports."""

    def test_import_repository_factory(self) -> None:
        """RepositoryFactory should be importable."""
        from framework_m.adapters.db.repository_factory import RepositoryFactory

        assert RepositoryFactory is not None

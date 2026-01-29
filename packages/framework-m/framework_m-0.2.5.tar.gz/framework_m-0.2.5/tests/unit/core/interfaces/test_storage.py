"""Tests for StorageProtocol interface compliance."""

from datetime import UTC, datetime

import pytest

from framework_m.adapters.storage import InMemoryStorageAdapter
from framework_m.core.interfaces.storage import (
    FileMetadata,
    StorageProtocol,
)


class TestFileMetadata:
    """Tests for FileMetadata model."""

    def test_file_metadata_creation(self) -> None:
        """FileMetadata should create with all required fields."""
        metadata = FileMetadata(
            path="uploads/file.txt",
            size=1024,
            content_type="text/plain",
            modified=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            etag="abc123",
        )
        assert metadata.path == "uploads/file.txt"
        assert metadata.size == 1024
        assert metadata.content_type == "text/plain"
        assert metadata.etag == "abc123"

    def test_file_metadata_content_type_optional(self) -> None:
        """FileMetadata content_type should be optional."""
        metadata = FileMetadata(
            path="uploads/file.bin",
            size=512,
            modified=datetime.now(UTC),
        )
        assert metadata.content_type is None

    def test_file_metadata_etag_optional(self) -> None:
        """FileMetadata etag should be optional."""
        metadata = FileMetadata(
            path="uploads/file.txt",
            size=256,
            modified=datetime.now(UTC),
        )
        assert metadata.etag is None


class TestStorageProtocol:
    """Tests for StorageProtocol interface."""

    def test_protocol_has_save_file_method(self) -> None:
        """StorageProtocol should define save_file method."""
        assert hasattr(StorageProtocol, "save_file")

    def test_protocol_has_get_file_method(self) -> None:
        """StorageProtocol should define get_file method."""
        assert hasattr(StorageProtocol, "get_file")

    def test_protocol_has_delete_file_method(self) -> None:
        """StorageProtocol should define delete_file method."""
        assert hasattr(StorageProtocol, "delete_file")

    def test_protocol_has_list_files_method(self) -> None:
        """StorageProtocol should define list_files method."""
        assert hasattr(StorageProtocol, "list_files")

    def test_protocol_has_get_metadata_method(self) -> None:
        """StorageProtocol should define get_metadata method."""
        assert hasattr(StorageProtocol, "get_metadata")

    def test_protocol_has_get_url_method(self) -> None:
        """StorageProtocol should define get_url method."""
        assert hasattr(StorageProtocol, "get_url")

    def test_protocol_has_copy_method(self) -> None:
        """StorageProtocol should define copy method."""
        assert hasattr(StorageProtocol, "copy")

    def test_protocol_has_move_method(self) -> None:
        """StorageProtocol should define move method."""
        assert hasattr(StorageProtocol, "move")

    def test_protocol_has_exists_method(self) -> None:
        """StorageProtocol should define exists method."""
        assert hasattr(StorageProtocol, "exists")


# =============================================================================
# Tests for InMemoryStorageAdapter
# =============================================================================


class TestInMemoryStorageAdapter:
    """Tests for InMemoryStorageAdapter."""

    @pytest.fixture
    def storage(self) -> InMemoryStorageAdapter:
        """Create a storage adapter instance."""
        return InMemoryStorageAdapter()

    @pytest.mark.asyncio
    async def test_save_and_get_file(self, storage: InMemoryStorageAdapter) -> None:
        """save_file() and get_file() should store and retrieve content."""
        content = b"Hello, World!"
        path = await storage.save_file("test.txt", content, "text/plain")
        result = await storage.get_file(path)
        assert result == content

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, storage: InMemoryStorageAdapter) -> None:
        """get_file() should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            await storage.get_file("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_delete_file(self, storage: InMemoryStorageAdapter) -> None:
        """delete_file() should remove a file."""
        await storage.save_file("test.txt", b"content")
        await storage.delete_file("test.txt")
        assert await storage.exists("test.txt") is False

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, storage: InMemoryStorageAdapter) -> None:
        """delete_file() should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            await storage.delete_file("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_exists_true(self, storage: InMemoryStorageAdapter) -> None:
        """exists() should return True for existing file."""
        await storage.save_file("test.txt", b"content")
        assert await storage.exists("test.txt") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, storage: InMemoryStorageAdapter) -> None:
        """exists() should return False for missing file."""
        assert await storage.exists("nonexistent.txt") is False

    @pytest.mark.asyncio
    async def test_list_files(self, storage: InMemoryStorageAdapter) -> None:
        """list_files() should return files matching prefix."""
        await storage.save_file("uploads/a.txt", b"a")
        await storage.save_file("uploads/b.txt", b"b")
        await storage.save_file("other/c.txt", b"c")
        files = await storage.list_files("uploads/")
        assert "uploads/a.txt" in files
        assert "uploads/b.txt" in files
        assert "other/c.txt" not in files

    @pytest.mark.asyncio
    async def test_get_metadata(self, storage: InMemoryStorageAdapter) -> None:
        """get_metadata() should return FileMetadata."""
        content = b"Hello"
        await storage.save_file("test.txt", content, "text/plain")
        metadata = await storage.get_metadata("test.txt")
        assert metadata is not None
        assert metadata.path == "test.txt"
        assert metadata.size == len(content)
        assert metadata.content_type == "text/plain"

    @pytest.mark.asyncio
    async def test_get_metadata_not_found(
        self, storage: InMemoryStorageAdapter
    ) -> None:
        """get_metadata() should return None for missing file."""
        metadata = await storage.get_metadata("nonexistent.txt")
        assert metadata is None

    @pytest.mark.asyncio
    async def test_get_url(self, storage: InMemoryStorageAdapter) -> None:
        """get_url() should return a pseudo URL."""
        await storage.save_file("test.txt", b"content")
        url = await storage.get_url("test.txt")
        assert "test.txt" in url

    @pytest.mark.asyncio
    async def test_copy(self, storage: InMemoryStorageAdapter) -> None:
        """copy() should copy a file."""
        await storage.save_file("src.txt", b"content", "text/plain")
        dest = await storage.copy("src.txt", "dest.txt")
        assert dest == "dest.txt"
        assert await storage.get_file("src.txt") == b"content"
        assert await storage.get_file("dest.txt") == b"content"

    @pytest.mark.asyncio
    async def test_copy_not_found(self, storage: InMemoryStorageAdapter) -> None:
        """copy() should raise FileNotFoundError for missing source."""
        with pytest.raises(FileNotFoundError):
            await storage.copy("nonexistent.txt", "dest.txt")

    @pytest.mark.asyncio
    async def test_move(self, storage: InMemoryStorageAdapter) -> None:
        """move() should move a file."""
        await storage.save_file("src.txt", b"content")
        dest = await storage.move("src.txt", "dest.txt")
        assert dest == "dest.txt"
        assert await storage.exists("src.txt") is False
        assert await storage.get_file("dest.txt") == b"content"

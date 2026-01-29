"""Tests for LocalStorageAdapter.

Tests cover:
- File save/get/delete operations
- Path traversal protection
- Atomic writes
- Directory organization
"""

import tempfile
from pathlib import Path

import pytest

from framework_m.adapters.storage.local import LocalStorageAdapter

# =============================================================================
# Test: Import
# =============================================================================


class TestLocalStorageImport:
    """Tests for LocalStorageAdapter import."""

    def test_import_local_storage_adapter(self) -> None:
        """LocalStorageAdapter should be importable."""
        from framework_m.adapters.storage import LocalStorageAdapter

        assert LocalStorageAdapter is not None


# =============================================================================
# Test: Initialization
# =============================================================================


class TestLocalStorageInit:
    """Tests for LocalStorageAdapter initialization."""

    def test_init_creates_directory(self) -> None:
        """Init should create base directory if not exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "uploads"
            LocalStorageAdapter(base_path=str(base))
            assert base.exists()

    def test_init_with_existing_directory(self) -> None:
        """Init should work with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)
            assert storage._base_path == Path(tmpdir).resolve()


# =============================================================================
# Test: Save File
# =============================================================================


class TestLocalStorageSaveFile:
    """Tests for save_file operation."""

    @pytest.fixture
    def storage(self) -> LocalStorageAdapter:
        """Create storage with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield LocalStorageAdapter(base_path=tmpdir)

    @pytest.mark.asyncio
    async def test_save_file(self) -> None:
        """save_file should write content to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)
            content = b"Hello, World!"

            path = await storage.save_file("test.txt", content)

            assert path == "test.txt"
            assert await storage.exists("test.txt")

    @pytest.mark.asyncio
    async def test_save_file_creates_directories(self) -> None:
        """save_file should create parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)
            content = b"Nested file"

            await storage.save_file("2024/01/05/doc.pdf", content)

            assert await storage.exists("2024/01/05/doc.pdf")

    @pytest.mark.asyncio
    async def test_save_file_overwrites(self) -> None:
        """save_file should overwrite existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            await storage.save_file("test.txt", b"First")
            await storage.save_file("test.txt", b"Second")

            content = await storage.get_file("test.txt")
            assert content == b"Second"


# =============================================================================
# Test: Get File
# =============================================================================


class TestLocalStorageGetFile:
    """Tests for get_file operation."""

    @pytest.mark.asyncio
    async def test_get_file(self) -> None:
        """get_file should return file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)
            content = b"Test content"

            await storage.save_file("test.txt", content)
            result = await storage.get_file("test.txt")

            assert result == content

    @pytest.mark.asyncio
    async def test_get_file_not_found(self) -> None:
        """get_file should raise FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            with pytest.raises(FileNotFoundError):
                await storage.get_file("nonexistent.txt")


# =============================================================================
# Test: Delete File
# =============================================================================


class TestLocalStorageDeleteFile:
    """Tests for delete_file operation."""

    @pytest.mark.asyncio
    async def test_delete_file(self) -> None:
        """delete_file should remove file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            await storage.save_file("test.txt", b"Content")
            await storage.delete_file("test.txt")

            assert not await storage.exists("test.txt")

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self) -> None:
        """delete_file should raise FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            with pytest.raises(FileNotFoundError):
                await storage.delete_file("nonexistent.txt")


# =============================================================================
# Test: Exists
# =============================================================================


class TestLocalStorageExists:
    """Tests for exists operation."""

    @pytest.mark.asyncio
    async def test_exists_true(self) -> None:
        """exists should return True for existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            await storage.save_file("test.txt", b"Content")

            assert await storage.exists("test.txt") is True

    @pytest.mark.asyncio
    async def test_exists_false(self) -> None:
        """exists should return False for missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            assert await storage.exists("nonexistent.txt") is False


# =============================================================================
# Test: List Files
# =============================================================================


class TestLocalStorageListFiles:
    """Tests for list_files operation."""

    @pytest.mark.asyncio
    async def test_list_files(self) -> None:
        """list_files should return matching files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            await storage.save_file("uploads/a.txt", b"A")
            await storage.save_file("uploads/b.txt", b"B")
            await storage.save_file("other/c.txt", b"C")

            files = await storage.list_files("uploads")

            assert "uploads/a.txt" in files
            assert "uploads/b.txt" in files
            assert "other/c.txt" not in files

    @pytest.mark.asyncio
    async def test_list_files_empty(self) -> None:
        """list_files should return empty for nonexistent prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            files = await storage.list_files("nonexistent")

            assert files == []


# =============================================================================
# Test: Metadata
# =============================================================================


class TestLocalStorageMetadata:
    """Tests for get_metadata operation."""

    @pytest.mark.asyncio
    async def test_get_metadata(self) -> None:
        """get_metadata should return file info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)
            content = b"Test content"

            await storage.save_file("test.pdf", content)
            metadata = await storage.get_metadata("test.pdf")

            assert metadata is not None
            assert metadata.path == "test.pdf"
            assert metadata.size == len(content)
            assert metadata.content_type == "application/pdf"

    @pytest.mark.asyncio
    async def test_get_metadata_not_found(self) -> None:
        """get_metadata should return None for missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            metadata = await storage.get_metadata("nonexistent.txt")

            assert metadata is None


# =============================================================================
# Test: Copy/Move
# =============================================================================


class TestLocalStorageCopyMove:
    """Tests for copy and move operations."""

    @pytest.mark.asyncio
    async def test_copy(self) -> None:
        """copy should duplicate file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            await storage.save_file("src.txt", b"Content")
            await storage.copy("src.txt", "dest.txt")

            assert await storage.exists("src.txt")
            assert await storage.exists("dest.txt")
            assert await storage.get_file("dest.txt") == b"Content"

    @pytest.mark.asyncio
    async def test_move(self) -> None:
        """move should relocate file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            await storage.save_file("src.txt", b"Content")
            await storage.move("src.txt", "dest.txt")

            assert not await storage.exists("src.txt")
            assert await storage.exists("dest.txt")


# =============================================================================
# Test: Path Traversal Protection
# =============================================================================


class TestLocalStorageSecurity:
    """Tests for security features."""

    def test_path_traversal_blocked(self) -> None:
        """Path traversal attempts should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)

            with pytest.raises(ValueError, match="path traversal"):
                storage._full_path("../../../etc/passwd")

    def test_absolute_path_sanitized(self) -> None:
        """Absolute paths should be sanitized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorageAdapter(base_path=tmpdir)
            full = storage._full_path("/some/file.txt")

            # Should be relative to base_path (use resolve for /private on macOS)
            base_resolved = str(Path(tmpdir).resolve())
            assert str(full).startswith(base_resolved)

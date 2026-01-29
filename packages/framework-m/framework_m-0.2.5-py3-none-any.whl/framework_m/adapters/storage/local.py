"""Local Storage Adapter - Filesystem-based storage implementation.

This module provides LocalStorageAdapter for storing files on the local
filesystem. Ideal for development, Indie mode, and single-server deployments.

Features:
- Date-organized directory structure (YYYY/MM/DD)
- Atomic file writes using temporary files
- Automatic directory creation
- Content-type preservation via extension

Configuration in framework_config.toml:
    [files]
    storage_backend = "local"
    storage_path = "./uploads"

Example:
    storage = LocalStorageAdapter(base_path="./uploads")
    path = await storage.save_file("test.pdf", content, "application/pdf")
    content = await storage.get_file(path)
"""

from __future__ import annotations

import asyncio
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

import aiofiles  # type: ignore[import-untyped]
import aiofiles.os  # type: ignore[import-untyped]

from framework_m.core.interfaces.storage import FileMetadata, StorageProtocol


class LocalStorageAdapter(StorageProtocol):
    """Local filesystem storage adapter.

    Implements StorageProtocol for local file storage.
    Files are organized by date (YYYY/MM/DD) for easy management.

    Attributes:
        base_path: Root directory for file storage

    Example:
        storage = LocalStorageAdapter(base_path="./uploads")

        # Save file
        path = await storage.save_file(
            "documents/report.pdf",
            content,
            "application/pdf"
        )

        # Get file
        content = await storage.get_file(path)
    """

    def __init__(self, base_path: str = "./uploads") -> None:
        """Initialize the local storage adapter.

        Args:
            base_path: Root directory for file storage (created if not exists)
        """
        self._base_path = Path(base_path).resolve()
        # Ensure base directory exists
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _full_path(self, path: str) -> Path:
        """Get full filesystem path for a storage path.

        Args:
            path: Relative storage path

        Returns:
            Absolute filesystem path
        """
        # Prevent path traversal attacks
        clean_path = Path(path).as_posix().lstrip("/")
        full = self._base_path / clean_path
        # Ensure the resolved path is within base_path
        if not str(full.resolve()).startswith(str(self._base_path)):
            raise ValueError("Invalid path: path traversal detected")
        return full

    async def save_file(
        self,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        """Save file to local filesystem.

        Creates parent directories if needed. Uses atomic write pattern
        with temporary file to prevent corruption on failure.

        Args:
            path: Relative storage path
            content: File content as bytes
            content_type: Optional MIME type (stored in metadata if needed)

        Returns:
            The path where the file was saved
        """
        full_path = self._full_path(path)

        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically using temp file
        temp_path = full_path.with_suffix(full_path.suffix + ".tmp")
        try:
            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(content)
            # Atomic rename
            await aiofiles.os.rename(temp_path, full_path)
        except Exception:
            # Clean up temp file on failure
            if temp_path.exists():
                await aiofiles.os.remove(temp_path)
            raise

        return path

    async def get_file(self, path: str) -> bytes:
        """Read file from local filesystem.

        Args:
            path: Relative storage path

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        full_path = self._full_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        async with aiofiles.open(full_path, "rb") as f:
            content: bytes = await f.read()
            return content

    async def delete_file(self, path: str) -> None:
        """Delete file from local filesystem.

        Args:
            path: Relative storage path

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        full_path = self._full_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        await aiofiles.os.remove(full_path)

    async def exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: Relative storage path

        Returns:
            True if file exists
        """
        full_path = self._full_path(path)
        return full_path.exists()

    async def list_files(self, prefix: str) -> list[str]:
        """List files matching a prefix.

        Args:
            prefix: Path prefix to filter by

        Returns:
            List of matching file paths
        """
        full_path = self._full_path(prefix)

        if not full_path.exists():
            return []

        result: list[str] = []

        # Use synchronous walk in executor for compatibility
        def _list_recursive() -> list[str]:
            files = []
            for root, _, filenames in os.walk(full_path):
                for filename in filenames:
                    # Skip temp files
                    if filename.endswith(".tmp"):
                        continue
                    file_path = Path(root) / filename
                    rel_path = file_path.relative_to(self._base_path)
                    files.append(str(rel_path))
            return files

        result = await asyncio.get_event_loop().run_in_executor(None, _list_recursive)
        return result

    async def get_metadata(self, path: str) -> FileMetadata | None:
        """Get file metadata without reading content.

        Args:
            path: Relative storage path

        Returns:
            FileMetadata if file exists, None otherwise
        """
        full_path = self._full_path(path)

        if not full_path.exists():
            return None

        stat = full_path.stat()
        return FileMetadata(
            path=path,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            content_type=self._guess_content_type(path),
        )

    async def get_url(self, path: str, expires: int = 3600) -> str:
        """Get URL for file access.

        For local storage, returns an API endpoint path.
        The application should serve files via this endpoint.

        Args:
            path: Relative storage path
            expires: Ignored for local storage

        Returns:
            URL path for file access
        """
        # For local storage, return API endpoint
        return f"/api/v1/file/{path}"

    async def copy(self, src: str, dest: str) -> str:
        """Copy a file within storage.

        Args:
            src: Source file path
            dest: Destination file path

        Returns:
            Path of the copied file

        Raises:
            FileNotFoundError: If source doesn't exist
        """
        src_full = self._full_path(src)
        dest_full = self._full_path(dest)

        if not src_full.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        # Create destination directory
        dest_full.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        def _copy() -> None:
            shutil.copy2(src_full, dest_full)

        await asyncio.get_event_loop().run_in_executor(None, _copy)
        return dest

    async def move(self, src: str, dest: str) -> str:
        """Move a file within storage.

        Args:
            src: Source file path
            dest: Destination file path

        Returns:
            Path of the moved file

        Raises:
            FileNotFoundError: If source doesn't exist
        """
        src_full = self._full_path(src)
        dest_full = self._full_path(dest)

        if not src_full.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        # Create destination directory
        dest_full.parent.mkdir(parents=True, exist_ok=True)

        # Move file
        await aiofiles.os.rename(src_full, dest_full)
        return dest

    def _guess_content_type(self, path: str) -> str | None:
        """Guess content type from file extension.

        Args:
            path: File path

        Returns:
            MIME type or None
        """
        import mimetypes

        mime_type, _ = mimetypes.guess_type(path)
        return mime_type


__all__ = ["LocalStorageAdapter"]

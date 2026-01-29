"""In-Memory Storage Adapter - Testing and development storage.

This module provides InMemoryStorageAdapter for storing files in memory.
Ideal for testing and single-process development.
"""

from __future__ import annotations

from datetime import UTC, datetime

from framework_m.core.interfaces.storage import FileMetadata


class InMemoryStorageAdapter:
    """In-memory implementation of StorageProtocol.

    Uses a simple dict to store files in memory.
    Suitable for testing and single-process development.

    Example:
        storage = InMemoryStorageAdapter()
        await storage.save_file("uploads/doc.pdf", content)
        content = await storage.get_file("uploads/doc.pdf")
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._files: dict[str, bytes] = {}
        self._metadata: dict[str, FileMetadata] = {}

    async def save_file(
        self,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        """Save file content to storage."""
        self._files[path] = content
        self._metadata[path] = FileMetadata(
            path=path,
            size=len(content),
            modified=datetime.now(UTC),
            content_type=content_type,
        )
        return path

    async def get_file(self, path: str) -> bytes:
        """Retrieve file content from storage."""
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path]

    async def delete_file(self, path: str) -> None:
        """Delete a file from storage."""
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        del self._files[path]
        del self._metadata[path]

    async def exists(self, path: str) -> bool:
        """Check if a file exists in storage."""
        return path in self._files

    async def list_files(self, prefix: str) -> list[str]:
        """List files matching a prefix."""
        return [p for p in self._files if p.startswith(prefix)]

    async def get_metadata(self, path: str) -> FileMetadata | None:
        """Get metadata for a file."""
        return self._metadata.get(path)

    async def get_url(self, path: str, expires: int = 3600) -> str:
        """Generate a URL for file access."""
        # For in-memory, return a pseudo URL
        return f"mem://{path}?expires={expires}"

    async def copy(self, src: str, dest: str) -> str:
        """Copy a file within storage."""
        if src not in self._files:
            raise FileNotFoundError(f"Source file not found: {src}")
        content = self._files[src]
        await self.save_file(dest, content, self._metadata[src].content_type)
        return dest

    async def move(self, src: str, dest: str) -> str:
        """Move a file within storage."""
        await self.copy(src, dest)
        await self.delete_file(src)
        return dest


__all__ = ["InMemoryStorageAdapter"]

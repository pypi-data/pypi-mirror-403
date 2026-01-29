"""Storage Protocol - Core interface for file storage.

This module defines the StorageProtocol for file storage operations.
Supports various backends: Local filesystem, S3, GCS, Azure Blob, etc.
"""

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel


class FileMetadata(BaseModel):
    """Metadata for a stored file.

    Contains information about a file in storage without the actual content.

    Attributes:
        path: Full path/key of the file in storage
        size: File size in bytes
        content_type: MIME type (e.g., "text/plain", "image/png")
        modified: Last modification timestamp
        etag: Entity tag for cache validation (optional)
    """

    path: str
    size: int
    modified: datetime
    content_type: str | None = None
    etag: str | None = None


class StorageProtocol(Protocol):
    """Protocol defining the contract for file storage.

    This is the primary port for file operations in the hexagonal architecture.
    Implementations handle different storage backends.

    Implementations include:
    - LocalStorageAdapter: Local filesystem storage
    - S3StorageAdapter: Amazon S3 / compatible object storage
    - GCSStorageAdapter: Google Cloud Storage

    Example usage:
        storage: StorageProtocol = container.get(StorageProtocol)

        # Save a file
        path = await storage.save_file(
            "uploads/doc.pdf",
            content,
            content_type="application/pdf"
        )

        # Get presigned URL for download
        url = await storage.get_url(path, expires=3600)
    """

    async def save_file(
        self,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        """Save file content to storage.

        Args:
            path: Destination path/key for the file
            content: File content as bytes
            content_type: Optional MIME type

        Returns:
            The actual path where the file was saved
        """
        ...

    async def get_file(self, path: str) -> bytes:
        """Retrieve file content from storage.

        Args:
            path: Path/key of the file

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        ...

    async def delete_file(self, path: str) -> None:
        """Delete a file from storage.

        Args:
            path: Path/key of the file to delete

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        ...

    async def exists(self, path: str) -> bool:
        """Check if a file exists in storage.

        Args:
            path: Path/key to check

        Returns:
            True if file exists, False otherwise
        """
        ...

    async def list_files(self, prefix: str) -> list[str]:
        """List files matching a prefix.

        Args:
            prefix: Path prefix to filter by (e.g., "uploads/user-001/")

        Returns:
            List of file paths matching the prefix
        """
        ...

    async def get_metadata(self, path: str) -> FileMetadata | None:
        """Get metadata for a file without fetching content.

        More efficient than get_file when you only need metadata.

        Args:
            path: Path/key of the file

        Returns:
            FileMetadata if file exists, None otherwise
        """
        ...

    async def get_url(self, path: str, expires: int = 3600) -> str:
        """Generate a presigned URL for file access.

        For S3/cloud storage, generates a time-limited URL.
        For local storage, may return a direct path or API endpoint.

        Args:
            path: Path/key of the file
            expires: URL expiration time in seconds (default: 1 hour)

        Returns:
            URL for accessing the file
        """
        ...

    async def copy(self, src: str, dest: str) -> str:
        """Copy a file within storage.

        Args:
            src: Source file path
            dest: Destination file path

        Returns:
            Path of the copied file
        """
        ...

    async def move(self, src: str, dest: str) -> str:
        """Move a file within storage.

        Equivalent to copy + delete.

        Args:
            src: Source file path
            dest: Destination file path

        Returns:
            Path of the moved file
        """
        ...


__all__ = [
    "FileMetadata",
    "StorageProtocol",
]

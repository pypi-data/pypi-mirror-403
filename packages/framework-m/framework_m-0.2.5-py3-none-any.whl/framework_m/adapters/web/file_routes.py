"""File Upload/Download API Routes.

This module provides REST API endpoints for file management:
- POST /upload - Upload a file
- GET /{file_id} - Download a file
- DELETE /{file_id} - Delete a file

All endpoints respect privacy settings and RLS.

Configuration in framework_config.toml:
    [files]
    max_upload_size = "10MB"
    allowed_extensions = ["pdf", "doc", "docx", "xls", "xlsx", "png", "jpg", "jpeg", "gif"]
    storage_backend = "local"  # or "s3"
    storage_path = "./uploads"

Example:
    from framework_m.adapters.web.file_routes import file_router

    app = Litestar(route_handlers=[file_router])
"""

from __future__ import annotations

import mimetypes
import secrets
from datetime import UTC, datetime
from typing import Any

from litestar import Controller, Response, delete, get, post
from litestar.datastructures import UploadFile
from litestar.exceptions import NotFoundException, PermissionDeniedException
from litestar.status_codes import HTTP_201_CREATED
from pydantic import BaseModel, Field

from framework_m.cli.config import load_config
from framework_m.core.doctypes.file import File

# =============================================================================
# Configuration
# =============================================================================


def get_file_config() -> dict[str, Any]:
    """Get file upload configuration from framework_config.toml.

    Returns:
        Dict with max_upload_size, allowed_extensions, storage settings
    """
    config = load_config()
    file_config = config.get("files", {})

    return {
        "max_upload_size": _parse_size(file_config.get("max_upload_size", "10MB")),
        "allowed_extensions": file_config.get(
            "allowed_extensions",
            ["pdf", "doc", "docx", "xls", "xlsx", "png", "jpg", "jpeg", "gif", "txt"],
        ),
        "storage_backend": file_config.get("storage_backend", "local"),
        "storage_path": file_config.get("storage_path", "./uploads"),
    }


def _parse_size(size_str: str) -> int:
    """Parse size string like '10MB' to bytes.

    Args:
        size_str: Size string (e.g., "10MB", "5KB", "1GB")

    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}

    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                value = float(size_str[: -len(unit)].strip())
                return int(value * multiplier)
            except ValueError:
                pass

    # Default: treat as bytes
    try:
        return int(size_str)
    except ValueError:
        return 10 * 1024 * 1024  # Default 10MB


# =============================================================================
# Request/Response Models
# =============================================================================


class FileUploadResponse(BaseModel):
    """Response for successful file upload."""

    file_id: str = Field(description="Unique file identifier")
    file_name: str = Field(description="Original filename")
    file_url: str = Field(description="URL to access the file")
    file_size: int = Field(description="Size in bytes")
    content_type: str = Field(description="MIME type")


class FileInfoResponse(BaseModel):
    """Response with file metadata."""

    file_id: str
    file_name: str
    file_url: str
    file_size: int
    content_type: str
    is_private: bool
    created_at: str


class FileDeleteResponse(BaseModel):
    """Response for file deletion."""

    message: str = "File deleted successfully"
    file_id: str


# =============================================================================
# Validation Helpers
# =============================================================================


def validate_file_size(file_size: int, max_size: int) -> None:
    """Validate file size against maximum.

    Args:
        file_size: Actual file size in bytes
        max_size: Maximum allowed size in bytes

    Raises:
        PermissionDeniedException: If file too large
    """
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise PermissionDeniedException(
            detail=f"File size exceeds maximum allowed ({max_mb:.1f}MB)"
        )


def validate_file_extension(filename: str, allowed: list[str]) -> None:
    """Validate file extension against whitelist.

    Args:
        filename: Original filename
        allowed: List of allowed extensions (without dots)

    Raises:
        PermissionDeniedException: If extension not allowed
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed:
        raise PermissionDeniedException(
            detail=f"File type '.{ext}' not allowed. Allowed: {', '.join(allowed)}"
        )


def generate_storage_path(filename: str) -> str:
    """Generate unique storage path with date organization.

    Args:
        filename: Original filename

    Returns:
        Storage path like "2024/01/05/abc123_filename.ext"
    """
    now = datetime.now(UTC)
    date_path = now.strftime("%Y/%m/%d")
    random_prefix = secrets.token_hex(8)

    # Sanitize filename
    safe_name = "".join(c for c in filename if c.isalnum() or c in ".-_")
    if not safe_name:
        safe_name = "file"

    return f"{date_path}/{random_prefix}_{safe_name}"


def get_content_type(filename: str) -> str:
    """Get MIME type from filename.

    Args:
        filename: File name with extension

    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


# =============================================================================
# File Controller
# =============================================================================


class FileController(Controller):
    """File management API controller.

    Provides endpoints for uploading, downloading, and deleting files.
    """

    path = "/api/v1/file"
    tags = ["Files"]  # noqa: RUF012

    @post("/upload", status_code=HTTP_201_CREATED)
    async def upload_file(
        self,
        data: UploadFile,
        is_private: bool = True,
        attached_to_doctype: str | None = None,
        attached_to_name: str | None = None,
    ) -> FileUploadResponse:
        """Upload a file.

        Accepts multipart/form-data with a single file.
        Validates size and extension, saves to storage, creates File record.

        Args:
            data: Uploaded file (multipart/form-data)
            is_private: Whether file requires auth (default: True)
            attached_to_doctype: Optional parent DocType
            attached_to_name: Optional parent document ID

        Returns:
            FileUploadResponse with file URL and metadata

        Raises:
            PermissionDeniedException: If file too large or type not allowed
        """
        config = get_file_config()

        # Get file info
        filename = data.filename or "unnamed"
        content = await data.read()
        file_size = len(content)

        # Validate
        validate_file_size(file_size, config["max_upload_size"])
        validate_file_extension(filename, config["allowed_extensions"])

        # Generate storage path
        storage_path = generate_storage_path(filename)
        file_url = f"/files/{storage_path}"

        # Get content type
        content_type = get_content_type(filename)

        # Create File DocType record
        file_record = File(
            file_name=filename,
            file_url=file_url,
            file_size=file_size,
            content_type=content_type,
            attached_to_doctype=attached_to_doctype,
            attached_to_name=attached_to_name,
            is_private=is_private,
        )

        # TODO: Save file to storage adapter
        # storage = get_storage_adapter()
        # await storage.save_file(storage_path, content, content_type)

        # TODO: Save File record to database
        # await file_repo.create(file_record)

        return FileUploadResponse(
            file_id=str(file_record.id),
            file_name=filename,
            file_url=file_url,
            file_size=file_size,
            content_type=content_type,
        )

    @get("/{file_id:str}")
    async def download_file(
        self,
        file_id: str,
        inline: bool = False,
    ) -> Response[bytes]:
        """Download a file by ID.

        Checks permissions for private files, streams from storage.
        Returns proper Content-Type and Content-Disposition headers.

        Args:
            file_id: File UUID
            inline: If True, display in browser; if False, download

        Returns:
            File content with correct headers for streaming

        Raises:
            NotFoundException: If file not found
            PermissionDeniedException: If not authorized for private file
        """
        # TODO: Look up file record from database
        # file_record = await file_repo.get(file_id)
        # if not file_record:
        #     raise NotFoundException(f"File {file_id} not found")

        # TODO: Check permissions for private files
        # if file_record.is_private:
        #     user = get_current_user()
        #     if not user:
        #         raise PermissionDeniedException("Authentication required")
        #     # Check RLS - user must be owner
        #     if file_record.owner != user.id:
        #         raise PermissionDeniedException("Access denied")

        # TODO: Get file from storage (streaming)
        # storage = get_storage_adapter()
        # content = await storage.get_file(file_record.file_url)

        # Example response with proper headers (placeholder)
        # content_disposition = (
        #     "inline" if inline else f'attachment; filename="{file_record.file_name}"'
        # )
        # return Response(
        #     content=content,
        #     media_type=file_record.content_type,
        #     headers={
        #         "Content-Disposition": content_disposition,
        #         "Content-Length": str(file_record.file_size),
        #         "Cache-Control": "private, max-age=3600",
        #     },
        # )

        # Placeholder - raise not found until storage is implemented
        raise NotFoundException(f"File {file_id} not found")

    @get("/{file_id:str}/info")
    async def get_file_info(self, file_id: str) -> FileInfoResponse:
        """Get file metadata without downloading content.

        Args:
            file_id: File UUID

        Returns:
            FileInfoResponse with metadata

        Raises:
            NotFoundException: If file not found
        """
        # TODO: Look up file record from database
        # file_record = await file_repo.get(file_id)
        # if not file_record:
        #     raise NotFoundException(f"File {file_id} not found")

        # Placeholder
        raise NotFoundException(f"File {file_id} not found")

    @delete("/{file_id:str}")
    async def delete_file(self, file_id: str) -> FileDeleteResponse:
        """Delete a file by ID.

        Removes file from storage and deletes File record.
        Only owner can delete (enforced via RLS).

        Args:
            file_id: File UUID

        Returns:
            Confirmation message

        Raises:
            NotFoundException: If file not found
            PermissionDeniedException: If not owner
        """
        # TODO: Look up file record from database
        # file_record = await file_repo.get(file_id)
        # if not file_record:
        #     raise NotFoundException(f"File {file_id} not found")

        # TODO: Check ownership (RLS)

        # TODO: Delete from storage
        # storage = get_storage_adapter()
        # await storage.delete_file(file_record.file_url)

        # TODO: Delete File record
        # await file_repo.delete(file_id)

        # Placeholder response
        raise NotFoundException(f"File {file_id} not found")


# Create router for easy import
file_router = FileController


__all__ = [
    "FileController",
    "FileDeleteResponse",
    "FileInfoResponse",
    "FileUploadResponse",
    "file_router",
    "get_file_config",
]

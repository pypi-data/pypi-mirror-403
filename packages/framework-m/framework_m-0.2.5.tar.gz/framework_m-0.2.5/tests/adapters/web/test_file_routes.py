"""Tests for File Upload/Download API Routes.

Tests cover:
- File configuration
- Validation helpers
- File upload API
"""

from unittest.mock import patch

import pytest

# =============================================================================
# Test: File Config
# =============================================================================


class TestFileConfig:
    """Tests for file upload configuration."""

    def test_import_get_file_config(self) -> None:
        """get_file_config should be importable."""
        from framework_m.adapters.web.file_routes import get_file_config

        assert get_file_config is not None

    def test_default_config(self) -> None:
        """get_file_config should return defaults when not configured."""
        from framework_m.adapters.web.file_routes import get_file_config

        with patch("framework_m.adapters.web.file_routes.load_config", return_value={}):
            config = get_file_config()

        assert config["max_upload_size"] == 10 * 1024 * 1024  # 10MB
        assert "pdf" in config["allowed_extensions"]
        assert config["storage_backend"] == "local"

    def test_custom_config(self) -> None:
        """get_file_config should read from config file."""
        from framework_m.adapters.web.file_routes import get_file_config

        mock_config = {
            "files": {
                "max_upload_size": "5MB",
                "allowed_extensions": ["pdf", "png"],
                "storage_backend": "s3",
            }
        }
        with patch(
            "framework_m.adapters.web.file_routes.load_config",
            return_value=mock_config,
        ):
            config = get_file_config()

        assert config["max_upload_size"] == 5 * 1024 * 1024
        assert config["allowed_extensions"] == ["pdf", "png"]
        assert config["storage_backend"] == "s3"


# =============================================================================
# Test: Size Parsing
# =============================================================================


class TestSizeParsing:
    """Tests for size string parsing."""

    def test_parse_megabytes(self) -> None:
        """_parse_size should parse MB."""
        from framework_m.adapters.web.file_routes import _parse_size

        assert _parse_size("10MB") == 10 * 1024 * 1024

    def test_parse_kilobytes(self) -> None:
        """_parse_size should parse KB."""
        from framework_m.adapters.web.file_routes import _parse_size

        assert _parse_size("500KB") == 500 * 1024

    def test_parse_gigabytes(self) -> None:
        """_parse_size should parse GB."""
        from framework_m.adapters.web.file_routes import _parse_size

        assert _parse_size("1GB") == 1024 * 1024 * 1024

    def test_parse_bytes(self) -> None:
        """_parse_size should parse plain bytes."""
        from framework_m.adapters.web.file_routes import _parse_size

        assert _parse_size("1024B") == 1024

    def test_parse_lowercase(self) -> None:
        """_parse_size should handle lowercase."""
        from framework_m.adapters.web.file_routes import _parse_size

        assert _parse_size("10mb") == 10 * 1024 * 1024


# =============================================================================
# Test: Validation Helpers
# =============================================================================


class TestValidation:
    """Tests for validation helpers."""

    def test_validate_file_size_ok(self) -> None:
        """validate_file_size should pass for valid size."""
        from framework_m.adapters.web.file_routes import validate_file_size

        # Should not raise
        validate_file_size(1000, 10000)

    def test_validate_file_size_too_large(self) -> None:
        """validate_file_size should reject large files."""
        from litestar.exceptions import PermissionDeniedException

        from framework_m.adapters.web.file_routes import validate_file_size

        with pytest.raises(PermissionDeniedException):
            validate_file_size(20000, 10000)

    def test_validate_extension_allowed(self) -> None:
        """validate_file_extension should pass for allowed types."""
        from framework_m.adapters.web.file_routes import validate_file_extension

        # Should not raise
        validate_file_extension("document.pdf", ["pdf", "doc"])

    def test_validate_extension_not_allowed(self) -> None:
        """validate_file_extension should reject unknown types."""
        from litestar.exceptions import PermissionDeniedException

        from framework_m.adapters.web.file_routes import validate_file_extension

        with pytest.raises(PermissionDeniedException):
            validate_file_extension("script.exe", ["pdf", "doc"])


# =============================================================================
# Test: Path Generation
# =============================================================================


class TestPathGeneration:
    """Tests for storage path generation."""

    def test_generate_storage_path_format(self) -> None:
        """generate_storage_path should return date-based path."""
        from framework_m.adapters.web.file_routes import generate_storage_path

        path = generate_storage_path("test.pdf")

        # Should have date format and random prefix
        parts = path.split("/")
        assert len(parts) == 4  # YYYY/MM/DD/file
        assert parts[0].isdigit() and len(parts[0]) == 4  # Year
        assert parts[1].isdigit() and len(parts[1]) == 2  # Month
        assert parts[2].isdigit() and len(parts[2]) == 2  # Day
        assert "test.pdf" in parts[3]

    def test_generate_storage_path_unique(self) -> None:
        """generate_storage_path should generate unique paths."""
        from framework_m.adapters.web.file_routes import generate_storage_path

        path1 = generate_storage_path("test.pdf")
        path2 = generate_storage_path("test.pdf")

        assert path1 != path2  # Random prefix makes them unique


# =============================================================================
# Test: Content Type Detection
# =============================================================================


class TestContentType:
    """Tests for content type detection."""

    def test_get_content_type_pdf(self) -> None:
        """get_content_type should detect PDF."""
        from framework_m.adapters.web.file_routes import get_content_type

        assert get_content_type("doc.pdf") == "application/pdf"

    def test_get_content_type_png(self) -> None:
        """get_content_type should detect PNG."""
        from framework_m.adapters.web.file_routes import get_content_type

        assert get_content_type("image.png") == "image/png"

    def test_get_content_type_unknown(self) -> None:
        """get_content_type should default for unknown."""
        from framework_m.adapters.web.file_routes import get_content_type

        # Use a truly unknown extension
        assert get_content_type("file.qqqxxx") == "application/octet-stream"


# =============================================================================
# Test: Response Models
# =============================================================================


class TestResponseModels:
    """Tests for response models."""

    def test_file_upload_response(self) -> None:
        """FileUploadResponse should accept all fields."""
        from framework_m.adapters.web.file_routes import FileUploadResponse

        response = FileUploadResponse(
            file_id="abc123",
            file_name="test.pdf",
            file_url="/files/2024/01/test.pdf",
            file_size=1024,
            content_type="application/pdf",
        )
        assert response.file_id == "abc123"
        assert response.file_name == "test.pdf"

    def test_file_delete_response(self) -> None:
        """FileDeleteResponse should have correct defaults."""
        from framework_m.adapters.web.file_routes import FileDeleteResponse

        response = FileDeleteResponse(file_id="abc123")
        assert response.message == "File deleted successfully"
        assert response.file_id == "abc123"


# =============================================================================
# Test: Controller Import
# =============================================================================


class TestFileController:
    """Tests for FileController."""

    def test_import_file_controller(self) -> None:
        """FileController should be importable."""
        from framework_m.adapters.web.file_routes import FileController

        assert FileController is not None

    def test_import_file_router(self) -> None:
        """file_router should be importable."""
        from framework_m.adapters.web.file_routes import file_router

        assert file_router is not None

    def test_controller_path(self) -> None:
        """FileController should have correct path."""
        from framework_m.adapters.web.file_routes import FileController

        assert FileController.path == "/api/v1/file"

    def test_controller_has_upload_endpoint(self) -> None:
        """FileController should have upload_file method."""
        from framework_m.adapters.web.file_routes import FileController

        assert hasattr(FileController, "upload_file")

    def test_controller_has_download_endpoint(self) -> None:
        """FileController should have download_file method."""
        from framework_m.adapters.web.file_routes import FileController

        assert hasattr(FileController, "download_file")

    def test_controller_has_get_file_info_endpoint(self) -> None:
        """FileController should have get_file_info method."""
        from framework_m.adapters.web.file_routes import FileController

        assert hasattr(FileController, "get_file_info")

    def test_controller_has_delete_endpoint(self) -> None:
        """FileController should have delete_file method."""
        from framework_m.adapters.web.file_routes import FileController

        assert hasattr(FileController, "delete_file")


class TestFileInfoResponse:
    """Tests for FileInfoResponse model."""

    def test_file_info_response(self) -> None:
        """FileInfoResponse should accept all fields."""
        from framework_m.adapters.web.file_routes import FileInfoResponse

        response = FileInfoResponse(
            file_id="abc123",
            file_name="test.pdf",
            file_url="/files/2024/01/test.pdf",
            file_size=1024,
            content_type="application/pdf",
            is_private=True,
            created_at="2024-01-05T12:00:00Z",
        )
        assert response.file_id == "abc123"
        assert response.is_private is True
        assert response.created_at == "2024-01-05T12:00:00Z"

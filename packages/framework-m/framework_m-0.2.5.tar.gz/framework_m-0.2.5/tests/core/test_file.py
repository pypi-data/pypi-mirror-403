"""Tests for File DocType.

Tests cover:
- File DocType import and creation
- Field validation
- Meta configuration
"""

from framework_m.core.doctypes.file import File

# =============================================================================
# Test: File Import
# =============================================================================


class TestFileImport:
    """Tests for File DocType import."""

    def test_import_file_doctype(self) -> None:
        """File should be importable."""
        from framework_m.core.doctypes.file import File

        assert File is not None


# =============================================================================
# Test: File Creation
# =============================================================================


class TestFileCreation:
    """Tests for File DocType creation."""

    def test_create_file_minimal(self) -> None:
        """File should create with required fields."""
        file = File(
            file_name="document.pdf",
            file_url="/files/2024/01/abc123.pdf",
            file_size=1024,
        )
        assert file.file_name == "document.pdf"
        assert file.file_url == "/files/2024/01/abc123.pdf"
        assert file.file_size == 1024

    def test_create_file_with_content_type(self) -> None:
        """File should accept content_type."""
        file = File(
            file_name="image.png",
            file_url="/files/img.png",
            file_size=2048,
            content_type="image/png",
        )
        assert file.content_type == "image/png"

    def test_create_file_default_content_type(self) -> None:
        """File should have default content_type."""
        file = File(
            file_name="data.bin",
            file_url="/files/data.bin",
            file_size=512,
        )
        assert file.content_type == "application/octet-stream"

    def test_create_file_with_attachment(self) -> None:
        """File should accept attached_to fields."""
        file = File(
            file_name="invoice.pdf",
            file_url="/files/invoice.pdf",
            file_size=4096,
            attached_to_doctype="Invoice",
            attached_to_name="INV-001",
        )
        assert file.attached_to_doctype == "Invoice"
        assert file.attached_to_name == "INV-001"

    def test_create_file_is_private_default(self) -> None:
        """File should default to private."""
        file = File(
            file_name="secret.txt",
            file_url="/files/secret.txt",
            file_size=100,
        )
        assert file.is_private is True

    def test_create_file_public(self) -> None:
        """File can be set to public."""
        file = File(
            file_name="public.txt",
            file_url="/files/public.txt",
            file_size=100,
            is_private=False,
        )
        assert file.is_private is False


# =============================================================================
# Test: File Meta
# =============================================================================


class TestFileMeta:
    """Tests for File DocType Meta configuration."""

    def test_file_has_table_name(self) -> None:
        """File should have table_name configured."""
        assert File.Meta.table_name == "files"

    def test_file_requires_auth_false(self) -> None:
        """File should not require auth (for public files)."""
        assert File.Meta.requires_auth is False

    def test_file_apply_rls_true(self) -> None:
        """File should have RLS enabled."""
        assert File.Meta.apply_rls is True

    def test_file_rls_field(self) -> None:
        """File should use owner for RLS."""
        assert File.Meta.rls_field == "owner"

    def test_file_permissions(self) -> None:
        """File should have permissions configured."""
        perms = File.Meta.permissions
        assert "read" in perms
        assert "write" in perms
        assert "create" in perms
        assert "delete" in perms


# =============================================================================
# Test: File Serialization
# =============================================================================


class TestFileSerialization:
    """Tests for File serialization."""

    def test_file_to_dict(self) -> None:
        """File should serialize to dict."""
        file = File(
            file_name="test.pdf",
            file_url="/files/test.pdf",
            file_size=1000,
            content_type="application/pdf",
            is_private=True,
        )
        data = file.model_dump()
        assert data["file_name"] == "test.pdf"
        assert data["file_url"] == "/files/test.pdf"
        assert data["file_size"] == 1000
        assert data["content_type"] == "application/pdf"
        assert data["is_private"] is True

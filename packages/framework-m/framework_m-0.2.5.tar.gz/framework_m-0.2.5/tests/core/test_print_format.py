"""Tests for PrintFormat DocType.

Tests cover:
- PrintFormat model creation
- Field validation
- Meta configuration
"""

import pytest

from framework_m.core.doctypes.print_format import PrintFormat

# =============================================================================
# Test: Import
# =============================================================================


class TestPrintFormatImport:
    """Tests for PrintFormat import."""

    def test_import_print_format(self) -> None:
        """PrintFormat should be importable."""
        from framework_m.core.doctypes.print_format import PrintFormat

        assert PrintFormat is not None


# =============================================================================
# Test: Model Creation
# =============================================================================


class TestPrintFormatCreation:
    """Tests for PrintFormat model creation."""

    def test_create_minimal(self) -> None:
        """PrintFormat should work with required fields only."""
        format_ = PrintFormat(
            name="Standard Invoice",
            doctype="Invoice",
            template="invoice.html",
        )

        assert format_.name == "Standard Invoice"
        assert format_.doctype == "Invoice"
        assert format_.template == "invoice.html"
        assert format_.is_default is False

    def test_create_with_is_default(self) -> None:
        """PrintFormat should accept is_default flag."""
        format_ = PrintFormat(
            name="Default",
            doctype="Invoice",
            template="invoice.html",
            is_default=True,
        )

        assert format_.is_default is True

    def test_create_with_css(self) -> None:
        """PrintFormat should accept custom CSS."""
        format_ = PrintFormat(
            name="Styled",
            doctype="Invoice",
            template="invoice.html",
            css=".header { color: blue; }",
        )

        assert format_.css == ".header { color: blue; }"

    def test_create_with_header_footer(self) -> None:
        """PrintFormat should accept header/footer HTML."""
        format_ = PrintFormat(
            name="With Header",
            doctype="Invoice",
            template="invoice.html",
            header_html="<div>Company Name</div>",
            footer_html="<div>Page {page}</div>",
        )

        assert format_.header_html is not None
        assert format_.footer_html is not None

    def test_default_page_size(self) -> None:
        """PrintFormat should default to A4 page size."""
        format_ = PrintFormat(
            name="Test",
            doctype="Invoice",
            template="test.html",
        )

        assert format_.page_size == "A4"

    def test_default_orientation(self) -> None:
        """PrintFormat should default to portrait orientation."""
        format_ = PrintFormat(
            name="Test",
            doctype="Invoice",
            template="test.html",
        )

        assert format_.orientation == "portrait"


# =============================================================================
# Test: Validation
# =============================================================================


class TestPrintFormatValidation:
    """Tests for field validation."""

    def test_valid_page_sizes(self) -> None:
        """page_size should accept valid values."""
        for size in ["A4", "Letter", "Legal", "A3", "A5"]:
            format_ = PrintFormat(
                name="Test",
                doctype="Invoice",
                template="test.html",
                page_size=size,
            )
            assert format_.page_size == size

    def test_invalid_page_size(self) -> None:
        """page_size should reject invalid values."""
        with pytest.raises(ValueError):
            PrintFormat(
                name="Test",
                doctype="Invoice",
                template="test.html",
                page_size="Tabloid",
            )

    def test_valid_orientations(self) -> None:
        """orientation should accept valid values."""
        for orient in ["portrait", "landscape"]:
            format_ = PrintFormat(
                name="Test",
                doctype="Invoice",
                template="test.html",
                orientation=orient,
            )
            assert format_.orientation == orient

    def test_invalid_orientation(self) -> None:
        """orientation should reject invalid values."""
        with pytest.raises(ValueError):
            PrintFormat(
                name="Test",
                doctype="Invoice",
                template="test.html",
                orientation="sideways",
            )


# =============================================================================
# Test: Meta Configuration
# =============================================================================


class TestPrintFormatMeta:
    """Tests for Meta class configuration."""

    def test_meta_table_name(self) -> None:
        """Meta should have correct table_name."""
        assert PrintFormat.Meta.table_name == "print_formats"

    def test_meta_requires_auth(self) -> None:
        """Meta should require authentication."""
        assert PrintFormat.Meta.requires_auth is True

    def test_meta_no_rls(self) -> None:
        """Meta should not apply RLS (all can read)."""
        assert PrintFormat.Meta.apply_rls is False

    def test_meta_all_can_read(self) -> None:
        """Meta should allow all users to read."""
        assert "All" in PrintFormat.Meta.permissions["read"]

    def test_meta_admin_only_write(self) -> None:
        """Meta should allow only System Manager to write."""
        assert "System Manager" in PrintFormat.Meta.permissions["write"]
        assert "System Manager" in PrintFormat.Meta.permissions["create"]

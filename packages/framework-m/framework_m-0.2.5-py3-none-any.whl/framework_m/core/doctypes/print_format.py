"""PrintFormat DocType - Document print templates.

This module defines the PrintFormat DocType for Framework M's print system.

The PrintFormat DocType stores configuration for document printing:
- Which DocType the format applies to
- Template path (Jinja2 template)
- Default format flag for auto-selection

Multiple print formats can exist per DocType, allowing users to choose
different layouts (e.g., "Standard Invoice", "Pro Forma Invoice").

Security:
- Only admins can create/modify print formats
- All users can read (to use in printing)

Example:
    format = PrintFormat(
        name="Standard Invoice",
        doctype="Invoice",
        template="templates/invoice_standard.html",
        is_default=True,
    )
"""

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class PrintFormat(BaseDocType):
    """Print format configuration DocType.

    Stores print template configuration for a DocType.

    Attributes:
        name: Display name for the format
        doctype: Target DocType this format applies to
        template: Path to Jinja2 template file
        is_default: If True, this is the default format for the DocType
        css: Optional custom CSS for styling
        header_html: Optional custom header HTML
        footer_html: Optional custom footer HTML
        page_size: Page size for PDF (A4, Letter, etc.)
        orientation: Page orientation (portrait, landscape)

    Example:
        format = PrintFormat(
            name="Invoice Pro Forma",
            doctype="Invoice",
            template="invoice_proforma.html",
        )
    """

    # Required fields
    name: str = Field(
        ...,
        description="Display name for the print format",
        min_length=1,
        max_length=255,
    )

    doctype: str = Field(
        ...,
        description="Target DocType this format applies to",
        min_length=1,
    )

    template: str = Field(
        ...,
        description="Path to Jinja2 template file",
        min_length=1,
    )

    # Optional fields
    is_default: bool = Field(
        default=False,
        description="If True, this is the default format for the DocType",
    )

    css: str | None = Field(
        default=None,
        description="Optional custom CSS for styling",
    )

    header_html: str | None = Field(
        default=None,
        description="Optional custom header HTML",
    )

    footer_html: str | None = Field(
        default=None,
        description="Optional custom footer HTML",
    )

    page_size: str = Field(
        default="A4",
        description="Page size for PDF (A4, Letter, Legal)",
        pattern=r"^(A4|Letter|Legal|A3|A5)$",
    )

    orientation: str = Field(
        default="portrait",
        description="Page orientation (portrait, landscape)",
        pattern=r"^(portrait|landscape)$",
    )

    class Meta:
        """DocType metadata."""

        table_name = "print_formats"
        requires_auth = True
        apply_rls = False  # All users can read formats

        # Permissions - admins manage, all read
        permissions = {  # noqa: RUF012
            "read": ["All"],
            "write": ["System Manager"],
            "create": ["System Manager"],
            "delete": ["System Manager"],
        }


__all__ = ["PrintFormat"]

"""Print Protocol - Core interface for document rendering.

This module defines the PrintProtocol for rendering documents
to various output formats like PDF, HTML, etc.

Uses templates (Jinja2) and can delegate to external services
like Gotenberg for PDF generation.
"""

from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel


class PrintFormat(StrEnum):
    """Supported output formats for print rendering."""

    PDF = "pdf"
    HTML = "html"
    TEXT = "text"


class PrintProtocol(Protocol):
    """Protocol defining the contract for document printing/rendering.

    This is the primary port for document output in the hexagonal architecture.
    Separates template rendering from format conversion.

    Implementations include:
    - JinjaPrintAdapter: Renders Jinja2 templates to HTML
    - GotenbergAdapter: Converts HTML to PDF via Gotenberg service

    Example usage:
        printer: PrintProtocol = container.get(PrintProtocol)

        # Get available templates
        templates = await printer.get_templates("Invoice")

        # Render to PDF
        pdf_bytes = await printer.render(
            doc=invoice,
            template="standard",
            format=PrintFormat.PDF
        )
    """

    async def render(
        self,
        doc: BaseModel,
        template: str,
        format: PrintFormat | str = PrintFormat.PDF,
        context: dict[str, Any] | None = None,
    ) -> bytes:
        """Render a document to the specified format.

        Args:
            doc: The Pydantic model/DocType to render
            template: Template name (resolved to file path)
            format: Output format (pdf, html, text)
            context: Additional context for template rendering

        Returns:
            Rendered output as bytes
        """
        ...

    async def get_templates(self, doctype: str) -> list[str]:
        """Get available print templates for a DocType.

        Scans template directories for matching templates.

        Args:
            doctype: DocType name

        Returns:
            List of template names
        """
        ...


__all__ = [
    "PrintFormat",
    "PrintProtocol",
]

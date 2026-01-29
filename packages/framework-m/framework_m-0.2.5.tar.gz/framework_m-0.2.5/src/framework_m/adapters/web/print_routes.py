"""Print API Routes - Document printing endpoints.

This module provides REST API endpoints for printing documents:
- GET /api/v1/print/{doctype}/{id} - Render document as HTML or PDF

Usage:
    GET /api/v1/print/Invoice/INV-001?format=pdf
    GET /api/v1/print/Invoice/INV-001?format=html&print_format=ProForma
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Literal

from litestar import Controller, Response, get
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel, Field

# =============================================================================
# Response Models
# =============================================================================


class PrintErrorResponse(BaseModel):
    """Error response for print operations."""

    error: str = Field(description="Error message")
    detail: str | None = Field(default=None, description="Error detail")


# =============================================================================
# Print Controller
# =============================================================================


class PrintController(Controller):
    """Print API controller.

    Provides endpoints for rendering documents as HTML or PDF.

    Attributes:
        path: Base path for all endpoints
        tags: OpenAPI tags for documentation
    """

    path = "/api/v1/print"
    tags = ["Print"]  # noqa: RUF012

    @get("/{doctype:str}/{doc_id:str}")
    async def print_document(
        self,
        doctype: str,
        doc_id: str,
        format: Literal["pdf", "html"] = "pdf",
        print_format: str | None = None,
    ) -> Response[Any]:
        """Print a document as HTML or PDF.

        Renders the specified document using the appropriate print format
        and returns either HTML or PDF content.

        Args:
            doctype: DocType name (e.g., "Invoice")
            doc_id: Document ID (e.g., "INV-001")
            format: Output format - "pdf" or "html" (default: "pdf")
            print_format: Optional print format name (uses default if not specified)

        Returns:
            Response with HTML or PDF content

        Raises:
            NotFoundException: If document not found
            PermissionDeniedException: If not authorized to view document
        """
        # TODO: Load document from repository
        # doc = await self._repository.get(doctype, doc_id)
        # For now, use mock document
        doc = {
            "id": doc_id,
            "doctype": doctype,
            "name": f"{doctype} {doc_id}",
            "status": "Draft",
        }

        # TODO: Check read permission
        # await self._permission.check_read(request.user, doc)

        # TODO: Load print format from repository
        # If print_format specified, load it; otherwise get default
        template_name = print_format or f"{doctype.lower()}.html"

        # Get template directory (configurable)
        template_dir = Path(tempfile.gettempdir()) / "framework_m_templates"
        template_dir.mkdir(exist_ok=True)

        # Create default template if not exists
        template_path = template_dir / template_name
        if not template_path.exists():
            # Create a simple default template
            template_path.write_text(self._get_default_template(doctype))

        # Import adapters
        from framework_m.adapters.print import JinjaPrintAdapter

        # Render HTML
        jinja = JinjaPrintAdapter(template_dir=str(template_dir))
        html = await jinja.render_html(doc, template_name)

        if format == "html":
            return Response(
                content=html,
                status_code=HTTP_200_OK,
                media_type="text/html",
            )

        # Convert to PDF
        from framework_m.adapters.print import GotenbergPrintAdapter

        try:
            async with GotenbergPrintAdapter() as gotenberg:
                if not await gotenberg.is_available():
                    # Gotenberg not available, return HTML with warning
                    return Response(
                        content=html,
                        status_code=HTTP_200_OK,
                        media_type="text/html",
                        headers={
                            "X-Print-Warning": "PDF service unavailable, returning HTML"
                        },
                    )

                pdf_bytes = await gotenberg.html_to_pdf(html)
                return Response(
                    content=pdf_bytes,
                    status_code=HTTP_200_OK,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f'inline; filename="{doctype}_{doc_id}.pdf"',
                    },
                )
        except Exception:
            # If PDF fails, fallback to HTML
            return Response(
                content=html,
                status_code=HTTP_200_OK,
                media_type="text/html",
                headers={"X-Print-Warning": "PDF generation failed, returning HTML"},
            )

    def _get_default_template(self, doctype: str) -> str:
        """Generate a default print template."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{{{ doc.name }}}}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .field {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #666; }}
        .value {{ margin-left: 10px; }}
    </style>
</head>
<body>
    <h1>{doctype}</h1>
    {{% for key, value in doc.items() %}}
    <div class="field">
        <span class="label">{{{{ key }}}}:</span>
        <span class="value">{{{{ value }}}}</span>
    </div>
    {{% endfor %}}
</body>
</html>
"""


__all__ = ["PrintController", "PrintErrorResponse"]

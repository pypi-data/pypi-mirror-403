"""Print Adapters - Document rendering implementations.

This module provides adapters for rendering documents to HTML and PDF:
- JinjaPrintAdapter: Render documents to HTML using Jinja2 templates
- GotenbergPrintAdapter: Convert HTML to PDF via Gotenberg service

Configuration in framework_config.toml:
    [print]
    template_dir = "./templates"
    gotenberg_url = "http://localhost:3000"

Example:
    from framework_m.adapters.print import JinjaPrintAdapter, GotenbergPrintAdapter

    # Render to HTML
    jinja = JinjaPrintAdapter(template_dir="./templates")
    html = await jinja.render_html(invoice, "invoice.html")

    # Convert to PDF
    gotenberg = GotenbergPrintAdapter(gotenberg_url="http://localhost:3000")
    pdf = await gotenberg.html_to_pdf(html)
"""

from framework_m.adapters.print.gotenberg_adapter import (
    PAGE_SIZES,
    GotenbergConfig,
    GotenbergPrintAdapter,
)
from framework_m.adapters.print.jinja_adapter import (
    JinjaPrintAdapter,
    Printable,
    RenderContext,
)

__all__ = [
    "PAGE_SIZES",
    "GotenbergConfig",
    "GotenbergPrintAdapter",
    "JinjaPrintAdapter",
    "Printable",
    "RenderContext",
]

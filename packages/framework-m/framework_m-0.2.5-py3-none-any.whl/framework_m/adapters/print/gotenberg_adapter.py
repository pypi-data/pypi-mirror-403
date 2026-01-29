"""Gotenberg PDF Adapter - PDF rendering via Gotenberg service.

This module provides the GotenbergPrintAdapter for converting HTML to PDF
using the Gotenberg container service.

Gotenberg is a Docker-based PDF generation service that uses Chromium
for high-fidelity HTML to PDF conversion.

Features:
- Async HTTP calls to Gotenberg
- Page size and orientation support
- Header/footer HTML support
- Configurable margins

Configuration in framework_config.toml:
    [print]
    gotenberg_url = "http://localhost:3000"

Usage:
    from framework_m.adapters.print import GotenbergPrintAdapter

    adapter = GotenbergPrintAdapter(gotenberg_url="http://localhost:3000")
    pdf_bytes = await adapter.html_to_pdf(html_content)

Docker:
    docker run -d -p 3000:3000 gotenberg/gotenberg:8
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field

# =============================================================================
# Configuration
# =============================================================================


class GotenbergConfig(BaseModel):
    """Configuration for Gotenberg PDF adapter.

    Attributes:
        url: Gotenberg service URL
        timeout: Request timeout in seconds
        page_size: Page size (A4, Letter, etc.)
        orientation: portrait or landscape
        margin_top: Top margin in inches
        margin_bottom: Bottom margin in inches
        margin_left: Left margin in inches
        margin_right: Right margin in inches
    """

    url: str = Field(
        default="http://localhost:3000",
        description="Gotenberg service URL",
    )
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds",
    )
    page_size: str = Field(
        default="A4",
        description="Page size (A4, Letter, Legal)",
    )
    orientation: str = Field(
        default="portrait",
        description="Page orientation",
    )
    margin_top: float = Field(
        default=0.5,
        description="Top margin in inches",
    )
    margin_bottom: float = Field(
        default=0.5,
        description="Bottom margin in inches",
    )
    margin_left: float = Field(
        default=0.5,
        description="Left margin in inches",
    )
    margin_right: float = Field(
        default=0.5,
        description="Right margin in inches",
    )


# Page size dimensions in inches (width, height)
PAGE_SIZES: dict[str, tuple[float, float]] = {
    "A4": (8.27, 11.69),
    "Letter": (8.5, 11),
    "Legal": (8.5, 14),
    "A3": (11.69, 16.54),
    "A5": (5.83, 8.27),
}


# =============================================================================
# Gotenberg Print Adapter
# =============================================================================


class GotenbergPrintAdapter:
    """PDF renderer using Gotenberg service.

    Converts HTML to PDF by sending requests to a Gotenberg container.

    Attributes:
        config: Gotenberg configuration
        client: HTTP client for API calls

    Example:
        adapter = GotenbergPrintAdapter(gotenberg_url="http://localhost:3000")
        pdf = await adapter.html_to_pdf("<h1>Invoice</h1>")
    """

    def __init__(
        self,
        gotenberg_url: str = "http://localhost:3000",
        config: GotenbergConfig | None = None,
    ) -> None:
        """Initialize the Gotenberg adapter.

        Args:
            gotenberg_url: URL of Gotenberg service
            config: Optional full configuration
        """
        if config:
            self._config = config
        else:
            self._config = GotenbergConfig(url=gotenberg_url)

        self._client = httpx.AsyncClient(timeout=self._config.timeout)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> GotenbergPrintAdapter:
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self.close()

    async def html_to_pdf(
        self,
        html: str,
        page_size: str | None = None,
        orientation: str | None = None,
        header_html: str | None = None,
        footer_html: str | None = None,
    ) -> bytes:
        """Convert HTML to PDF.

        Args:
            html: HTML content to convert
            page_size: Override page size (A4, Letter, etc.)
            orientation: Override orientation (portrait, landscape)
            header_html: Optional header HTML
            footer_html: Optional footer HTML

        Returns:
            PDF file as bytes

        Raises:
            httpx.HTTPStatusError: If Gotenberg returns an error
        """
        # Get page dimensions
        size = page_size or self._config.page_size
        orient = orientation or self._config.orientation

        width, height = PAGE_SIZES.get(size, PAGE_SIZES["A4"])

        # Swap dimensions for landscape
        if orient == "landscape":
            width, height = height, width

        # Build form data for Gotenberg
        files: dict[str, Any] = {
            "index.html": ("index.html", html, "text/html"),
        }

        if header_html:
            files["header.html"] = ("header.html", header_html, "text/html")

        if footer_html:
            files["footer.html"] = ("footer.html", footer_html, "text/html")

        data = {
            "paperWidth": str(width),
            "paperHeight": str(height),
            "marginTop": str(self._config.margin_top),
            "marginBottom": str(self._config.margin_bottom),
            "marginLeft": str(self._config.margin_left),
            "marginRight": str(self._config.margin_right),
        }

        # Send to Gotenberg
        url = f"{self._config.url}/forms/chromium/convert/html"
        response = await self._client.post(url, data=data, files=files)
        response.raise_for_status()

        return response.content

    async def is_available(self) -> bool:
        """Check if Gotenberg service is available.

        Returns:
            True if service is running and responding
        """
        try:
            response = await self._client.get(f"{self._config.url}/health")
            return response.status_code == 200
        except httpx.RequestError:
            return False


__all__ = [
    "PAGE_SIZES",
    "GotenbergConfig",
    "GotenbergPrintAdapter",
]

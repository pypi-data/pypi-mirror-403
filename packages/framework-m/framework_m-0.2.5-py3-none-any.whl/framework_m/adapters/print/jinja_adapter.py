"""Jinja Print Adapter - HTML rendering using Jinja2 templates.

This module provides the JinjaPrintAdapter for rendering documents to HTML
using Jinja2 templates. This is the core of Framework M's print system.

Features:
- Async template loading and rendering
- Configurable template directories
- Built-in filters and functions for documents
- Safe HTML escaping by default

Usage:
    from framework_m.adapters.print import JinjaPrintAdapter

    adapter = JinjaPrintAdapter(template_dir="./templates")
    html = await adapter.render_html(document, "invoice.html")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel

# =============================================================================
# Protocol for Documents
# =============================================================================


class Printable(Protocol):
    """Protocol for printable documents.

    Any document that can be printed must implement this protocol.
    """

    def model_dump(self) -> dict[str, Any]:
        """Return document as dictionary."""
        ...


# =============================================================================
# Render Context
# =============================================================================


class RenderContext(BaseModel):
    """Context passed to templates during rendering.

    Provides additional context beyond the document data.

    Attributes:
        doc: The document being rendered
        print_format: PrintFormat configuration (if available)
        company: Company information (if available)
        user: Current user information (if available)
    """

    doc: dict[str, Any]
    print_format: dict[str, Any] | None = None
    company: dict[str, Any] | None = None
    user: dict[str, Any] | None = None


# =============================================================================
# Jinja Print Adapter
# =============================================================================


class JinjaPrintAdapter:
    """Jinja2-based HTML renderer for documents.

    Loads templates from the configured directory and renders them
    with document context.

    Attributes:
        template_dir: Path to template directory
        env: Jinja2 environment

    Example:
        adapter = JinjaPrintAdapter(template_dir="./templates")
        html = await adapter.render_html(invoice, "invoice.html")
    """

    def __init__(
        self,
        template_dir: str | Path = "./templates",
        auto_escape: bool = True,
    ) -> None:
        """Initialize the Jinja adapter.

        Args:
            template_dir: Path to template directory
            auto_escape: Enable HTML escaping (default True)
        """
        self._template_dir = Path(template_dir)

        # Create Jinja2 environment
        self._env = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=select_autoescape(["html", "xml"]) if auto_escape else False,
            enable_async=True,
        )

        # Add custom filters
        self._register_filters()

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""
        self._env.filters["currency"] = self._filter_currency
        self._env.filters["date"] = self._filter_date
        self._env.filters["datetime"] = self._filter_datetime

    @staticmethod
    def _filter_currency(value: float | int, symbol: str = "$") -> str:
        """Format number as currency."""
        if value is None:
            return ""
        return f"{symbol}{value:,.2f}"

    @staticmethod
    def _filter_date(value: Any, format_str: str = "%Y-%m-%d") -> str:
        """Format date value."""
        if value is None:
            return ""
        if hasattr(value, "strftime"):
            return str(value.strftime(format_str))
        return str(value)

    @staticmethod
    def _filter_datetime(value: Any, format_str: str = "%Y-%m-%d %H:%M") -> str:
        """Format datetime value."""
        if value is None:
            return ""
        if hasattr(value, "strftime"):
            return str(value.strftime(format_str))
        return str(value)

    async def render_html(
        self,
        doc: Printable | dict[str, Any],
        template_name: str,
        context: RenderContext | None = None,
    ) -> str:
        """Render a document to HTML using a template.

        Args:
            doc: Document to render (Pydantic model or dict)
            template_name: Name of the template file
            context: Optional additional context

        Returns:
            Rendered HTML string

        Raises:
            jinja2.TemplateNotFound: If template doesn't exist
        """
        # Get template
        template = self._env.get_template(template_name)

        # Build context
        doc_data = doc if isinstance(doc, dict) else doc.model_dump()

        render_context: dict[str, Any] = {
            "doc": doc_data,
        }

        if context:
            render_context["print_format"] = context.print_format
            render_context["company"] = context.company
            render_context["user"] = context.user

        # Render template
        html = await template.render_async(**render_context)
        return html

    async def render_html_string(
        self,
        template_string: str,
        doc: Printable | dict[str, Any],
        context: RenderContext | None = None,
    ) -> str:
        """Render a document using an inline template string.

        Args:
            template_string: Jinja2 template as string
            doc: Document to render
            context: Optional additional context

        Returns:
            Rendered HTML string
        """
        template = self._env.from_string(template_string)

        doc_data = doc if isinstance(doc, dict) else doc.model_dump()

        render_context: dict[str, Any] = {
            "doc": doc_data,
        }

        if context:
            render_context["print_format"] = context.print_format
            render_context["company"] = context.company
            render_context["user"] = context.user

        html = await template.render_async(**render_context)
        return html


__all__ = [
    "JinjaPrintAdapter",
    "Printable",
    "RenderContext",
]

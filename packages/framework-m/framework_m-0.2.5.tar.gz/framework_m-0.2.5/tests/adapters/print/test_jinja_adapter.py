"""Tests for Jinja Print Adapter.

Tests cover:
- JinjaPrintAdapter initialization
- HTML rendering
- Custom filters
"""

import tempfile
from pathlib import Path

import pytest

from framework_m.adapters.print.jinja_adapter import (
    JinjaPrintAdapter,
    RenderContext,
)

# =============================================================================
# Test: Import
# =============================================================================


class TestJinjaPrintImport:
    """Tests for Jinja adapter imports."""

    def test_import_jinja_print_adapter(self) -> None:
        """JinjaPrintAdapter should be importable."""
        from framework_m.adapters.print import JinjaPrintAdapter

        assert JinjaPrintAdapter is not None

    def test_import_render_context(self) -> None:
        """RenderContext should be importable."""
        from framework_m.adapters.print import RenderContext

        assert RenderContext is not None


# =============================================================================
# Test: Initialization
# =============================================================================


class TestJinjaPrintInit:
    """Tests for JinjaPrintAdapter initialization."""

    def test_init_with_template_dir(self) -> None:
        """Adapter should accept template directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = JinjaPrintAdapter(template_dir=tmpdir)
            assert adapter._template_dir == Path(tmpdir)

    def test_init_creates_environment(self) -> None:
        """Adapter should create Jinja2 environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = JinjaPrintAdapter(template_dir=tmpdir)
            assert adapter._env is not None


# =============================================================================
# Test: render_html
# =============================================================================


class TestRenderHtml:
    """Tests for render_html method."""

    @pytest.mark.asyncio
    async def test_render_simple_template(self) -> None:
        """render_html should render a simple template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create template
            template_path = Path(tmpdir) / "test.html"
            template_path.write_text("<h1>{{ doc.title }}</h1>")

            adapter = JinjaPrintAdapter(template_dir=tmpdir)
            html = await adapter.render_html({"title": "Hello"}, "test.html")

            assert "<h1>Hello</h1>" in html

    @pytest.mark.asyncio
    async def test_render_with_dict(self) -> None:
        """render_html should work with dict documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "invoice.html"
            template_path.write_text("<p>Total: {{ doc.total }}</p>")

            adapter = JinjaPrintAdapter(template_dir=tmpdir)
            html = await adapter.render_html({"total": 100}, "invoice.html")

            assert "<p>Total: 100</p>" in html

    @pytest.mark.asyncio
    async def test_render_with_context(self) -> None:
        """render_html should pass context to template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "test.html"
            template_path.write_text("<p>{{ company.name }}</p>")

            adapter = JinjaPrintAdapter(template_dir=tmpdir)
            context = RenderContext(
                doc={},
                company={"name": "Acme Inc"},
            )
            html = await adapter.render_html({}, "test.html", context=context)

            assert "<p>Acme Inc</p>" in html


# =============================================================================
# Test: render_html_string
# =============================================================================


class TestRenderHtmlString:
    """Tests for render_html_string method."""

    @pytest.mark.asyncio
    async def test_render_inline_template(self) -> None:
        """render_html_string should render inline template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = JinjaPrintAdapter(template_dir=tmpdir)

            html = await adapter.render_html_string(
                "<p>{{ doc.name }}</p>",
                {"name": "Test"},
            )

            assert "<p>Test</p>" in html


# =============================================================================
# Test: Custom Filters
# =============================================================================


class TestCustomFilters:
    """Tests for custom Jinja2 filters."""

    @pytest.mark.asyncio
    async def test_currency_filter(self) -> None:
        """currency filter should format numbers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = JinjaPrintAdapter(template_dir=tmpdir)

            html = await adapter.render_html_string(
                "{{ doc.amount | currency }}",
                {"amount": 1234.56},
            )

            assert "$1,234.56" in html

    @pytest.mark.asyncio
    async def test_currency_filter_custom_symbol(self) -> None:
        """currency filter should accept custom symbol."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = JinjaPrintAdapter(template_dir=tmpdir)

            html = await adapter.render_html_string(
                "{{ doc.amount | currency('€') }}",
                {"amount": 100},
            )

            assert "€100.00" in html

    @pytest.mark.asyncio
    async def test_date_filter(self) -> None:
        """date filter should format dates."""
        from datetime import date

        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = JinjaPrintAdapter(template_dir=tmpdir)

            html = await adapter.render_html_string(
                "{{ doc.date | date }}",
                {"date": date(2024, 1, 15)},
            )

            assert "2024-01-15" in html

    @pytest.mark.asyncio
    async def test_currency_filter_none(self) -> None:
        """currency filter should handle None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = JinjaPrintAdapter(template_dir=tmpdir)

            html = await adapter.render_html_string(
                "{{ doc.amount | currency }}",
                {"amount": None},
            )

            assert html.strip() == ""

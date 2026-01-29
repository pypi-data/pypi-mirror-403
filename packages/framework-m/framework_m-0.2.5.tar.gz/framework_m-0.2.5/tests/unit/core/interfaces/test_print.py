"""Tests for PrintProtocol interface compliance."""

from framework_m.core.interfaces.print import (
    PrintFormat,
    PrintProtocol,
)


class TestPrintFormat:
    """Tests for PrintFormat enum."""

    def test_print_format_values(self) -> None:
        """PrintFormat should have common output formats."""
        assert PrintFormat.PDF.value == "pdf"
        assert PrintFormat.HTML.value == "html"
        assert PrintFormat.TEXT.value == "text"


class TestPrintProtocol:
    """Tests for PrintProtocol interface."""

    def test_protocol_has_render_method(self) -> None:
        """PrintProtocol should define render method."""
        assert hasattr(PrintProtocol, "render")

    def test_protocol_has_get_templates_method(self) -> None:
        """PrintProtocol should define get_templates method."""
        assert hasattr(PrintProtocol, "get_templates")

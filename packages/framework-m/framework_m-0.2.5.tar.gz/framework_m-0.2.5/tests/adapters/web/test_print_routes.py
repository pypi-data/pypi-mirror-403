"""Tests for Print API Routes.

Tests cover:
- PrintController endpoint presence and configuration
- Response models
- print_document method
- _get_default_template helper
"""

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from framework_m.adapters.web.print_routes import (
    PrintController,
    PrintErrorResponse,
)

# =============================================================================
# Test: Import
# =============================================================================


class TestPrintRoutesImport:
    """Tests for Print routes import."""

    def test_import_print_controller(self) -> None:
        """PrintController should be importable."""
        from framework_m.adapters.web.print_routes import PrintController

        assert PrintController is not None

    def test_import_error_response(self) -> None:
        """PrintErrorResponse should be importable."""
        from framework_m.adapters.web.print_routes import PrintErrorResponse

        assert PrintErrorResponse is not None


# =============================================================================
# Test: PrintController
# =============================================================================


class TestPrintController:
    """Tests for PrintController."""

    def test_controller_path(self) -> None:
        """Controller should have correct path."""
        assert PrintController.path == "/api/v1/print"

    def test_controller_tags(self) -> None:
        """Controller should have Print tag."""
        assert "Print" in PrintController.tags

    def test_controller_has_print_document(self) -> None:
        """Controller should have print_document method."""
        assert hasattr(PrintController, "print_document")


# =============================================================================
# Test: PrintErrorResponse
# =============================================================================


class TestPrintErrorResponse:
    """Tests for PrintErrorResponse model."""

    def test_create_minimal(self) -> None:
        """PrintErrorResponse should work with required fields."""
        response = PrintErrorResponse(error="Not found")

        assert response.error == "Not found"
        assert response.detail is None

    def test_create_with_detail(self) -> None:
        """PrintErrorResponse should accept detail."""
        response = PrintErrorResponse(
            error="Permission denied",
            detail="User does not have access",
        )

        assert response.error == "Permission denied"
        assert response.detail == "User does not have access"

    def test_model_json_schema(self) -> None:
        """PrintErrorResponse should have valid JSON schema."""
        schema = PrintErrorResponse.model_json_schema()

        assert "error" in schema["properties"]
        assert "detail" in schema["properties"]


# =============================================================================
# Test: Template Generation
# =============================================================================


class TestPrintControllerTemplate:
    """Tests for PrintController._get_default_template()."""

    def test_get_default_template_invoice(self) -> None:
        """_get_default_template should generate Invoice template."""
        # Access the method directly from the class
        template = PrintController._get_default_template(None, "Invoice")

        assert "Invoice" in template
        assert "<!DOCTYPE html>" in template
        assert "{{ doc.name }}" in template

    def test_get_default_template_contains_styles(self) -> None:
        """_get_default_template should include CSS styles."""
        template = PrintController._get_default_template(None, "Order")

        assert "<style>" in template
        assert "font-family" in template

    def test_get_default_template_contains_jinja(self) -> None:
        """_get_default_template should include Jinja loop."""
        template = PrintController._get_default_template(None, "Report")

        assert "{% for key, value in doc.items() %}" in template
        assert "{% endfor %}" in template


# =============================================================================
# Test: print_document Integration Tests with TestClient
# =============================================================================


class TestPrintDocumentIntegration:
    """Integration tests for print_document endpoint using Litestar TestClient."""

    @pytest.fixture
    def app(self) -> "Litestar":
        """Create test app with print routes."""
        from litestar import Litestar

        return Litestar(route_handlers=[PrintController])

    @pytest.fixture
    def client(self, app: "Litestar") -> "TestClient":
        """Create test client."""
        from litestar.testing import TestClient

        return TestClient(app)

    def test_print_document_html_endpoint(self, client: "TestClient") -> None:
        """GET /api/v1/print/{doctype}/{id}?format=html should return HTML."""
        response = client.get("/api/v1/print/Invoice/INV-001?format=html")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        # Should contain HTML content
        assert "<!DOCTYPE html>" in response.text or "<html" in response.text.lower()

    def test_print_document_default_format_is_pdf(self, client: "TestClient") -> None:
        """GET /api/v1/print/{doctype}/{id} should default to PDF, fallback to HTML."""
        response = client.get("/api/v1/print/Invoice/INV-001")

        # Should return 200 (either PDF or HTML fallback)
        assert response.status_code == 200
        # Check content type - either PDF or HTML fallback
        content_type = response.headers.get("content-type", "")
        assert "application/pdf" in content_type or "text/html" in content_type

    def test_print_document_creates_doc_mock(self, client: "TestClient") -> None:
        """print_document should create a mock document with correct ID."""
        response = client.get("/api/v1/print/SalesOrder/SO-123?format=html")

        assert response.status_code == 200
        # The mock includes the doc_id in the rendered output
        assert "SO-123" in response.text or "SalesOrder" in response.text

    def test_print_document_various_doctypes(self, client: TestClient) -> None:
        """print_document should work with various doctype names."""
        # Test with different doctypes
        response1 = client.get("/api/v1/print/Invoice/INV-001?format=html")
        response2 = client.get("/api/v1/print/PurchaseOrder/PO-001?format=html")

        assert response1.status_code == 200
        assert response2.status_code == 200

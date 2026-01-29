"""Tests for Link Field Data Leakage Prevention.

TDD tests for preventing data leakage when serializing docs with Link fields:
- Link fields should NOT auto-include linked doc data
- Linked doc data requires separate API call (with permission check)
- Optional ?expand param checks permission before expanding

Per CONTRIBUTING.md: Write failing tests FIRST, then implement.
"""

from typing import ClassVar
from uuid import UUID

import pytest

from framework_m.core.domain.base_doctype import BaseDocType, Field
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes - With Link Fields
# =============================================================================


class Customer(BaseDocType):
    """Customer DocType - to be linked from Invoice."""

    customer_name: str = Field(description="Customer name")
    email: str = Field(default="", description="Customer email")
    internal_notes: str = Field(
        default="", description="Internal notes - should not leak"
    )

    class Meta:
        api_resource: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager"],
            "write": ["Manager"],
        }


class InvoiceWithLink(BaseDocType):
    """Invoice DocType with Link field to Customer."""

    customer_id: UUID | None = Field(
        default=None,
        description="Link to Customer (stores UUID, not full object)",
        json_schema_extra={
            "link": "Customer"
        },  # Metadata indicating this is a Link field
    )
    total: float = Field(default=0.0)

    class Meta:
        api_resource: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager"],
            "write": ["Manager"],
        }


# =============================================================================
# Tests: Link Field Serialization (No Auto-Include)
# =============================================================================


class TestLinkFieldNoAutoInclude:
    """Test that Link fields do NOT auto-include linked doc data."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Customer)
        registry.register_doctype(InvoiceWithLink)
        yield
        registry.clear()

    def test_link_field_stores_uuid_not_object(self) -> None:
        """Link field should store UUID reference, not embedded object."""
        from uuid import uuid4

        customer_id = uuid4()
        invoice = InvoiceWithLink(customer_id=customer_id, total=100.0)

        # Link field should be UUID, not Customer object
        assert isinstance(invoice.customer_id, UUID)
        assert invoice.customer_id == customer_id

    def test_link_field_serializes_to_uuid_string(self) -> None:
        """When serialized, Link field should be UUID string, not nested object."""
        from uuid import uuid4

        customer_id = uuid4()
        invoice = InvoiceWithLink(customer_id=customer_id, total=100.0)

        # Serialize to dict
        data = invoice.model_dump()

        # Should be UUID string, not nested Customer data
        assert data["customer_id"] == customer_id
        # Should NOT have customer name, email, etc.
        assert "customer_name" not in data
        assert "email" not in data

    def test_link_field_json_schema_has_link_metadata(self) -> None:
        """Link field should have metadata indicating it's a Link field."""
        field_info = InvoiceWithLink.model_fields["customer_id"]

        # Check for link metadata
        extra = field_info.json_schema_extra
        assert extra is not None
        assert isinstance(extra, dict)
        assert extra.get("link") == "Customer"

    def test_linked_doc_not_embedded_in_response(self) -> None:
        """API response should not embed linked document data."""
        from uuid import uuid4

        customer_id = uuid4()
        invoice = InvoiceWithLink(customer_id=customer_id, total=100.0)

        # When serialized for API, only the UUID should be returned
        json_data = invoice.model_dump_json()

        # Should contain the UUID string
        assert str(customer_id) in json_data

        # Should NOT contain customer-specific fields
        assert "customer_name" not in json_data
        assert "internal_notes" not in json_data


# =============================================================================
# Tests: Separate API Call for Linked Data
# =============================================================================


class TestSeparateApiForLinkedData:
    """Test that linked doc data requires separate API call."""

    def test_get_linked_doc_requires_permission(self) -> None:
        """Getting linked doc data should check permissions.

        Design principle: To get Customer data from an Invoice,
        you need:
        1. READ permission on Invoice (to see the invoice)
        2. READ permission on Customer (to see customer details)

        If you only have Invoice permission, customer_id is visible
        but you cannot fetch Customer details.
        """
        # This is a design test - the implementation would
        # require calling GET /api/v1/Customer/{customer_id}
        # which would check Customer read permission
        assert True  # Placeholder for design documentation


# =============================================================================
# Tests: Optional Expand Parameter
# =============================================================================


class TestExpandParameter:
    """Test optional ?expand parameter for Link expansion.

    Design:
    - GET /api/v1/Invoice/123 returns customer_id as UUID
    - GET /api/v1/Invoice/123?expand=customer_id checks Customer read permission
      and includes Customer data if permitted
    """

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Customer)
        registry.register_doctype(InvoiceWithLink)
        yield
        registry.clear()

    def test_expand_parameter_documented_design(self) -> None:
        """Document the expand parameter design.

        When ?expand=field is used:
        1. Identify the Link field
        2. Get the linked DocType from field metadata
        3. Check if user has READ permission on linked DocType
        4. If permitted, fetch and include linked doc data
        5. If not permitted, return 403 or omit the field

        This is an OPTIONAL feature for convenience.
        """
        # Verify link metadata is present
        field_info = InvoiceWithLink.model_fields["customer_id"]
        extra = field_info.json_schema_extra
        assert isinstance(extra, dict)
        assert "link" in extra

        # The implementation would check this metadata
        # and use it to determine the linked DocType
        linked_doctype = extra["link"]
        assert linked_doctype == "Customer"


class TestLinkFieldDesignPrinciples:
    """Document and test Link field design principles."""

    def test_link_field_pattern(self) -> None:
        """Link fields should follow this pattern:

        1. Store UUID reference, not embedded object
        2. Use json_schema_extra={"link": "DocTypeName"} for metadata
        3. Never auto-expand in serialization
        4. Expansion requires explicit ?expand param with permission check

        This prevents data leakage by ensuring all data access
        goes through the permission system.
        """
        # Pattern demonstration
        from uuid import uuid4

        # Create a Link field value
        customer_id = uuid4()

        # Create invoice with link
        invoice = InvoiceWithLink(customer_id=customer_id, total=500.0)

        # Serialize - should only have UUID, not nested data
        data = invoice.model_dump(mode="json")
        assert str(customer_id) in str(data["customer_id"])

        # Field metadata should indicate it's a Link
        meta = InvoiceWithLink.model_fields["customer_id"].json_schema_extra
        assert meta == {"link": "Customer"}

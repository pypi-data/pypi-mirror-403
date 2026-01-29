"""Tests for Mixins - DocStatus and SubmittableMixin."""

import warnings

from framework_m import DocType
from framework_m.core.domain.mixins import DocStatus, SubmittableMixin


class TestDocStatus:
    """Tests for DocStatus enum."""

    def test_docstatus_draft_value(self) -> None:
        """DRAFT should have value 0."""
        assert DocStatus.DRAFT.value == 0

    def test_docstatus_submitted_value(self) -> None:
        """SUBMITTED should have value 1."""
        assert DocStatus.SUBMITTED.value == 1

    def test_docstatus_cancelled_value(self) -> None:
        """CANCELLED should have value 2."""
        assert DocStatus.CANCELLED.value == 2

    def test_docstatus_comparison(self) -> None:
        """DocStatus values should be comparable."""
        assert DocStatus.DRAFT < DocStatus.SUBMITTED
        assert DocStatus.SUBMITTED < DocStatus.CANCELLED


# Suppress expected Pydantic warning about field shadowing
# This is intentional for mypy compatibility with mixins
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Field name.*shadows.*")

    class SubmittableInvoice(DocType, SubmittableMixin):
        """Test DocType with SubmittableMixin."""

        customer: str
        total: float = 0.0
        docstatus: DocStatus = DocStatus.DRAFT


class TestSubmittableMixin:
    """Tests for SubmittableMixin functionality."""

    def test_default_docstatus_is_draft(self) -> None:
        """New submittable doc should have DRAFT status."""
        invoice = SubmittableInvoice(customer="Test Customer")

        assert invoice.docstatus == DocStatus.DRAFT

    def test_is_submitted_when_draft(self) -> None:
        """is_submitted should return False for draft."""
        invoice = SubmittableInvoice(customer="Test")

        assert invoice.is_submitted() is False

    def test_is_submitted_when_submitted(self) -> None:
        """is_submitted should return True for submitted."""
        invoice = SubmittableInvoice(customer="Test", docstatus=DocStatus.SUBMITTED)

        assert invoice.is_submitted() is True

    def test_is_cancelled_when_draft(self) -> None:
        """is_cancelled should return False for draft."""
        invoice = SubmittableInvoice(customer="Test")

        assert invoice.is_cancelled() is False

    def test_is_cancelled_when_cancelled(self) -> None:
        """is_cancelled should return True for cancelled."""
        invoice = SubmittableInvoice(customer="Test", docstatus=DocStatus.CANCELLED)

        assert invoice.is_cancelled() is True

    def test_can_edit_when_draft(self) -> None:
        """can_edit should return True for draft."""
        invoice = SubmittableInvoice(customer="Test")

        assert invoice.can_edit() is True

    def test_can_edit_when_submitted(self) -> None:
        """can_edit should return False for submitted."""
        invoice = SubmittableInvoice(customer="Test", docstatus=DocStatus.SUBMITTED)

        assert invoice.can_edit() is False

    def test_can_edit_when_cancelled(self) -> None:
        """can_edit should return False for cancelled."""
        invoice = SubmittableInvoice(customer="Test", docstatus=DocStatus.CANCELLED)

        assert invoice.can_edit() is False

    def test_docstatus_serialization(self) -> None:
        """docstatus should serialize to integer value."""
        invoice = SubmittableInvoice(customer="Test", docstatus=DocStatus.SUBMITTED)
        data = invoice.model_dump()

        assert data["docstatus"] == 1

    def test_docstatus_from_int(self) -> None:
        """docstatus should be settable from integer."""
        invoice = SubmittableInvoice(customer="Test", docstatus=1)  # type: ignore[arg-type]

        assert invoice.docstatus == DocStatus.SUBMITTED


class TestMixinImports:
    """Tests for mixin imports."""

    def test_import_docstatus(self) -> None:
        """DocStatus should be importable."""
        from framework_m.core.domain.mixins import DocStatus

        assert DocStatus is not None

    def test_import_submittable_mixin(self) -> None:
        """SubmittableMixin should be importable."""
        from framework_m.core.domain.mixins import SubmittableMixin

        assert SubmittableMixin is not None

"""Mixins - Reusable components for DocTypes.

This module provides mixins that add common functionality to DocTypes:
- SubmittableMixin: For documents with workflow states (draft/submitted/cancelled)
"""

from enum import IntEnum

from pydantic import Field


class DocStatus(IntEnum):
    """Document status for submittable DocTypes.

    Follows the standard workflow:
    DRAFT (0) -> SUBMITTED (1) -> CANCELLED (2)

    Submitted documents are immutable. Cancelled documents can be amended
    to create a new draft.
    """

    DRAFT = 0
    SUBMITTED = 1
    CANCELLED = 2


class SubmittableMixin:
    """
    Mixin for DocTypes that support submit/cancel workflow.

    Add this mixin to DocTypes that need to be "submitted" (locked)
    after approval and can be "cancelled" later.

    Example:
        class Invoice(DocType, SubmittableMixin):
            customer: str
            total: float

        invoice = Invoice(customer="Acme Corp", total=1000)
        invoice.can_edit()  # True (draft)

        invoice.docstatus = DocStatus.SUBMITTED
        invoice.can_edit()  # False (submitted)
    """

    docstatus: DocStatus = Field(default=DocStatus.DRAFT)

    def is_submitted(self) -> bool:
        """Check if document is in submitted state."""
        return self.docstatus == DocStatus.SUBMITTED

    def is_cancelled(self) -> bool:
        """Check if document is in cancelled state."""
        return self.docstatus == DocStatus.CANCELLED

    def can_edit(self) -> bool:
        """
        Check if document can be edited.

        Only draft documents can be edited. Submitted and cancelled
        documents are immutable.
        """
        return self.docstatus == DocStatus.DRAFT


__all__ = [
    "DocStatus",
    "SubmittableMixin",
]

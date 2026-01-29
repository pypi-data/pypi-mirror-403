"""Tests for document lifecycle events."""

from datetime import UTC, datetime

# =============================================================================
# Test: Document Event Types Import
# =============================================================================


class TestDocEventImport:
    """Tests for document event type imports."""

    def test_import_doc_created(self) -> None:
        """DocCreated should be importable."""
        from framework_m.core.events import DocCreated

        assert DocCreated is not None

    def test_import_doc_updated(self) -> None:
        """DocUpdated should be importable."""
        from framework_m.core.events import DocUpdated

        assert DocUpdated is not None

    def test_import_doc_deleted(self) -> None:
        """DocDeleted should be importable."""
        from framework_m.core.events import DocDeleted

        assert DocDeleted is not None

    def test_import_doc_submitted(self) -> None:
        """DocSubmitted should be importable."""
        from framework_m.core.events import DocSubmitted

        assert DocSubmitted is not None

    def test_import_doc_cancelled(self) -> None:
        """DocCancelled should be importable."""
        from framework_m.core.events import DocCancelled

        assert DocCancelled is not None


# =============================================================================
# Test: DocCreated Event
# =============================================================================


class TestDocCreated:
    """Tests for DocCreated event."""

    def test_doc_created_with_required_fields(self) -> None:
        """DocCreated should be creatable with required fields."""
        from framework_m.core.events import DocCreated

        event = DocCreated(
            doctype="Invoice",
            doc_name="INV-001",
        )

        assert event.doctype == "Invoice"
        assert event.doc_name == "INV-001"
        assert event.type == "doc.created"
        assert event.user_id is None

    def test_doc_created_with_user_id(self) -> None:
        """DocCreated should accept user_id."""
        from framework_m.core.events import DocCreated

        event = DocCreated(
            doctype="Invoice",
            doc_name="INV-001",
            user_id="user-001",
        )

        assert event.user_id == "user-001"

    def test_doc_created_has_timestamp(self) -> None:
        """DocCreated should have auto-generated timestamp."""
        from framework_m.core.events import DocCreated

        before = datetime.now(UTC)
        event = DocCreated(doctype="Todo", doc_name="TODO-001")
        after = datetime.now(UTC)

        assert before <= event.timestamp <= after

    def test_doc_created_has_auto_id(self) -> None:
        """DocCreated should have auto-generated ID."""
        from framework_m.core.events import DocCreated

        event = DocCreated(doctype="Todo", doc_name="TODO-001")

        assert event.id is not None
        assert len(event.id) > 0


# =============================================================================
# Test: DocUpdated Event
# =============================================================================


class TestDocUpdated:
    """Tests for DocUpdated event."""

    def test_doc_updated_with_changes(self) -> None:
        """DocUpdated should accept changed_fields."""
        from framework_m.core.events import DocUpdated

        event = DocUpdated(
            doctype="Invoice",
            doc_name="INV-001",
            changed_fields=["status", "total"],
        )

        assert event.type == "doc.updated"
        assert event.changed_fields == ["status", "total"]


# =============================================================================
# Test: DocDeleted Event
# =============================================================================


class TestDocDeleted:
    """Tests for DocDeleted event."""

    def test_doc_deleted_basic(self) -> None:
        """DocDeleted should store doctype and doc_name."""
        from framework_m.core.events import DocDeleted

        event = DocDeleted(
            doctype="Invoice",
            doc_name="INV-001",
        )

        assert event.type == "doc.deleted"
        assert event.doctype == "Invoice"
        assert event.doc_name == "INV-001"


# =============================================================================
# Test: DocSubmitted Event
# =============================================================================


class TestDocSubmitted:
    """Tests for DocSubmitted event."""

    def test_doc_submitted_basic(self) -> None:
        """DocSubmitted should store submission info."""
        from framework_m.core.events import DocSubmitted

        event = DocSubmitted(
            doctype="Invoice",
            doc_name="INV-001",
        )

        assert event.type == "doc.submitted"


# =============================================================================
# Test: DocCancelled Event
# =============================================================================


class TestDocCancelled:
    """Tests for DocCancelled event."""

    def test_doc_cancelled_with_reason(self) -> None:
        """DocCancelled should accept reason."""
        from framework_m.core.events import DocCancelled

        event = DocCancelled(
            doctype="Invoice",
            doc_name="INV-001",
            reason="Customer requested cancellation",
        )

        assert event.type == "doc.cancelled"
        assert event.reason == "Customer requested cancellation"

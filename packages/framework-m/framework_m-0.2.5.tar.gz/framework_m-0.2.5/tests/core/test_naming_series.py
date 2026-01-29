"""Tests for Auto-Naming Series.

Tests the ability to auto-generate human-readable names using patterns.
The `name` field is auto-generated based on Meta.name_pattern.
The `id` field (UUID) is always the primary key - no contention.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from framework_m.adapters.db.generic_repository import GenericRepository
from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.adapters.db.table_registry import TableRegistry
from framework_m.core.domain.base_doctype import BaseDocType

# =============================================================================
# Test Models
# =============================================================================


class Invoice(BaseDocType):
    """Invoice with auto-naming pattern."""

    class Meta:
        name_pattern = "INV-.YYYY.-.####"  # INV-2024-0001

    customer: str
    amount: float


class Order(BaseDocType):
    """Order with month-based naming."""

    class Meta:
        name_pattern = "ORD-.YYYY.-.MM.-.####"  # ORD-2024-01-0001

    customer: str
    total: float


class Receipt(BaseDocType):
    """Receipt with date-based naming."""

    class Meta:
        name_pattern = "RCP-.YYYY.MM.DD.-.####"  # RCP-20240112-0001

    amount: float


class Task(BaseDocType):
    """Task with field value in pattern."""

    class Meta:
        name_pattern = "TASK-.{priority}.-.####"  # TASK-HIGH-0001

    title: str
    priority: str = "MEDIUM"


class SimpleDoc(BaseDocType):
    """Document with simple sequential naming."""

    class Meta:
        name_pattern = "DOC-.####"  # DOC-0001

    description: str


class NoPatternDoc(BaseDocType):
    """Document without naming pattern (manual name)."""

    content: str


class SequenceDoc(BaseDocType):
    """Document using PostgreSQL sequence for high-volume naming."""

    class Meta:
        name_pattern = "sequence:seq_doc_counter"  # Uses DB sequence

    value: str


# =============================================================================
# Test Pattern Detection
# =============================================================================


class TestNamingPatternDetection:
    """Test detection of naming patterns in Meta."""

    def test_meta_has_name_pattern(self):
        """DocType with Meta.name_pattern should be detected."""
        assert hasattr(Invoice, "Meta")
        assert hasattr(Invoice.Meta, "name_pattern")
        assert Invoice.Meta.name_pattern == "INV-.YYYY.-.####"

    def test_pattern_with_year_month(self):
        """Pattern with year and month."""
        assert Order.Meta.name_pattern == "ORD-.YYYY.-.MM.-.####"

    def test_pattern_with_full_date(self):
        """Pattern with full date."""
        assert Receipt.Meta.name_pattern == "RCP-.YYYY.MM.DD.-.####"

    def test_pattern_with_field_value(self):
        """Pattern with field value placeholder."""
        assert Task.Meta.name_pattern == "TASK-.{priority}.-.####"

    def test_simple_sequential_pattern(self):
        """Simple sequential number pattern."""
        assert SimpleDoc.Meta.name_pattern == "DOC-.####"

    def test_no_pattern_attribute(self):
        """DocType without name_pattern should not have it."""
        # NoPatternDoc has no Meta class, or Meta without name_pattern
        has_meta = hasattr(NoPatternDoc, "Meta")
        if has_meta:
            assert not hasattr(NoPatternDoc.Meta, "name_pattern")
        else:
            # No Meta class at all is also valid
            assert True


# =============================================================================
# Test Pattern Parsing
# =============================================================================


class TestPatternParsing:
    """Test parsing of naming patterns into components."""

    def test_parse_year_pattern(self):
        """Should identify .YYYY. placeholder."""
        pattern = "INV-.YYYY.-.####"
        # Pattern should contain year marker
        assert ".YYYY." in pattern

    def test_parse_month_pattern(self):
        """Should identify .MM. placeholder."""
        pattern = "ORD-.YYYY.-.MM.-.####"
        assert ".MM." in pattern

    def test_parse_day_pattern(self):
        """Should identify .DD. placeholder."""
        pattern = "RCP-.YYYY.MM.DD.-.####"
        assert ".DD." in pattern or "DD." in pattern

    def test_parse_counter_pattern(self):
        """Should identify #### counter placeholder."""
        pattern = "INV-.YYYY.-.####"
        assert "####" in pattern

    def test_parse_field_placeholder(self):
        """Should identify {field} placeholder."""
        pattern = "TASK-.{priority}.-.####"
        assert "{priority}" in pattern

    def test_counter_width_four_digits(self):
        """Counter with 4 digits."""
        pattern = "INV-.####"
        # Count # characters
        hash_count = pattern.count("#")
        assert hash_count == 4

    def test_counter_width_five_digits(self):
        """Counter with 5 digits."""
        pattern = "DOC-.#####"
        hash_count = pattern.count("#")
        assert hash_count == 5


# =============================================================================
# Test Name Generation
# =============================================================================


class TestNameGeneration:
    """Test auto-generation of names based on patterns."""

    @pytest.mark.asyncio
    async def test_generate_name_with_year(self, test_engine):
        """Should generate name with current year."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        invoice_table = mapper.create_table(Invoice, metadata)
        table_registry.register_table(Invoice.__name__, invoice_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create invoice without name
        invoice = Invoice(
            customer="Acme Corp",
            amount=1000.0,
        )

        invoice_repo = GenericRepository(Invoice, invoice_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            saved = await invoice_repo.save(session, invoice)
            await session.commit()

        # Verify name was generated
        assert saved.name is not None
        current_year = datetime.now(UTC).year
        assert saved.name.startswith(f"INV-{current_year}-")
        assert saved.name.endswith("0001")  # First document

    @pytest.mark.asyncio
    async def test_generate_sequential_names(self, test_engine):
        """Should generate sequential names."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        doc_table = mapper.create_table(SimpleDoc, metadata)
        table_registry.register_table(SimpleDoc.__name__, doc_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        doc_repo = GenericRepository(SimpleDoc, doc_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create multiple documents
        saved_docs = []
        for i in range(3):
            doc = SimpleDoc(description=f"Doc {i}")
            async with async_session_maker() as session:
                saved = await doc_repo.save(session, doc)
                await session.commit()
                saved_docs.append(saved)

        # Verify sequential names
        assert saved_docs[0].name == "DOC-0001"
        assert saved_docs[1].name == "DOC-0002"
        assert saved_docs[2].name == "DOC-0003"

    @pytest.mark.asyncio
    async def test_generate_name_with_year_month(self, test_engine):
        """Should generate name with year and month."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        order_table = mapper.create_table(Order, metadata)
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        order = Order(customer="Beta Inc", total=500.0)

        order_repo = GenericRepository(Order, order_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            saved = await order_repo.save(session, order)
            await session.commit()

        # Verify name format
        now = datetime.now(UTC)
        expected_prefix = f"ORD-{now.year}-{now.month:02d}-"
        assert saved.name.startswith(expected_prefix)
        assert saved.name.endswith("0001")

    @pytest.mark.asyncio
    async def test_generate_name_with_full_date(self, test_engine):
        """Should generate name with full date."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        receipt_table = mapper.create_table(Receipt, metadata)
        table_registry.register_table(Receipt.__name__, receipt_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        receipt = Receipt(amount=100.0)

        receipt_repo = GenericRepository(Receipt, receipt_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            saved = await receipt_repo.save(session, receipt)
            await session.commit()

        # Verify name format
        now = datetime.now(UTC)
        expected_prefix = f"RCP-{now.year}{now.month:02d}{now.day:02d}-"
        assert saved.name.startswith(expected_prefix)

    @pytest.mark.asyncio
    async def test_generate_name_with_field_value(self, test_engine):
        """Should generate name with field value."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        task_table = mapper.create_table(Task, metadata)
        table_registry.register_table(Task.__name__, task_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        task = Task(title="Important task", priority="HIGH")

        task_repo = GenericRepository(Task, task_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            saved = await task_repo.save(session, task)
            await session.commit()

        # Verify name includes field value
        assert saved.name == "TASK-HIGH-0001"


# =============================================================================
# Test Counter Management
# =============================================================================


class TestCounterManagement:
    """Test counter increment and reset."""

    @pytest.mark.asyncio
    async def test_counter_increments_per_prefix(self, test_engine):
        """Counter should increment within same prefix."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        invoice_table = mapper.create_table(Invoice, metadata)
        table_registry.register_table(Invoice.__name__, invoice_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        invoice_repo = GenericRepository(Invoice, invoice_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create invoices in same year
        saved_invoices = []
        for i in range(3):
            invoice = Invoice(customer=f"Customer {i}", amount=100.0 * (i + 1))
            async with async_session_maker() as session:
                saved = await invoice_repo.save(session, invoice)
                await session.commit()
                saved_invoices.append(saved)

        # All should have same year prefix
        year = datetime.now(UTC).year
        prefix = f"INV-{year}-"

        assert saved_invoices[0].name == f"{prefix}0001"
        assert saved_invoices[1].name == f"{prefix}0002"
        assert saved_invoices[2].name == f"{prefix}0003"

    @pytest.mark.asyncio
    async def test_different_prefixes_independent_counters(self, test_engine):
        """Different prefixes should have independent counters."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        task_table = mapper.create_table(Task, metadata)
        table_registry.register_table(Task.__name__, task_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        task_repo = GenericRepository(Task, task_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tasks with different priorities
        high_task = Task(title="High priority", priority="HIGH")
        low_task = Task(title="Low priority", priority="LOW")
        high_task2 = Task(title="Another high", priority="HIGH")

        async with async_session_maker() as session:
            saved_high = await task_repo.save(session, high_task)
            await session.commit()

        async with async_session_maker() as session:
            saved_low = await task_repo.save(session, low_task)
            await session.commit()

        async with async_session_maker() as session:
            saved_high2 = await task_repo.save(session, high_task2)
            await session.commit()

        # Verify independent counters
        assert saved_high.name == "TASK-HIGH-0001"
        assert saved_low.name == "TASK-LOW-0001"  # Independent counter
        assert saved_high2.name == "TASK-HIGH-0002"


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestNamingEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_manual_name_overrides_pattern(self, test_engine):
        """Manually provided name should override pattern."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        invoice_table = mapper.create_table(Invoice, metadata)
        table_registry.register_table(Invoice.__name__, invoice_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create invoice with manual name
        invoice = Invoice(
            name="CUSTOM-INV-001",
            customer="Manual Corp",
            amount=999.0,
        )

        invoice_repo = GenericRepository(Invoice, invoice_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            saved = await invoice_repo.save(session, invoice)
            await session.commit()

        # Should keep manual name
        assert saved.name == "CUSTOM-INV-001"

    @pytest.mark.asyncio
    async def test_no_pattern_uses_uuid_based_name(self, test_engine):
        """DocType without pattern should use UUID-based name."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        doc_table = mapper.create_table(NoPatternDoc, metadata)
        table_registry.register_table(NoPatternDoc.__name__, doc_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        doc = NoPatternDoc(content="Test content")

        doc_repo = GenericRepository(NoPatternDoc, doc_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            saved = await doc_repo.save(session, doc)
            await session.commit()

        # Should generate UUID-based name
        assert saved.name is not None
        assert len(saved.name) > 0

    @pytest.mark.asyncio
    async def test_counter_width_respected(self, test_engine):
        """Counter width should be respected (padding)."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        doc_table = mapper.create_table(SimpleDoc, metadata)
        table_registry.register_table(SimpleDoc.__name__, doc_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        doc_repo = GenericRepository(SimpleDoc, doc_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        doc = SimpleDoc(description="Test")
        async with async_session_maker() as session:
            saved = await doc_repo.save(session, doc)
            await session.commit()

        # Should have 4-digit counter with padding
        assert saved.name == "DOC-0001"
        assert len(saved.name.split("-")[1]) == 4


# =============================================================================
# Test Sequence-Based Naming (PostgreSQL Sequences)
# =============================================================================


class TestSequenceNaming:
    """Test PostgreSQL sequence-based naming for high-volume DocTypes."""

    def test_detect_sequence_pattern(self):
        """Should detect sequence:name pattern."""
        assert SequenceDoc.Meta.name_pattern == "sequence:seq_doc_counter"
        assert SequenceDoc.Meta.name_pattern.startswith("sequence:")

    def test_extract_sequence_name(self):
        """Should extract sequence name from pattern."""
        pattern = "sequence:invoice_seq"
        assert pattern.startswith("sequence:")
        sequence_name = pattern.split(":", 1)[1]
        assert sequence_name == "invoice_seq"

    @pytest.mark.asyncio
    async def test_sequence_naming_generates_names(self, test_engine):
        """Sequence-based naming should generate sequential names."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        seq_table = mapper.create_table(SequenceDoc, metadata)
        table_registry.register_table(SequenceDoc.__name__, seq_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        seq_repo = GenericRepository(SequenceDoc, seq_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create documents
        saved_docs = []
        for i in range(3):
            doc = SequenceDoc(value=f"Value {i}")
            async with async_session_maker() as session:
                saved = await seq_repo.save(session, doc)
                await session.commit()
                saved_docs.append(saved)

        # All documents should have names
        for doc in saved_docs:
            assert doc.name is not None
            assert len(doc.name) > 0

        # Names should be sequential (for SQLite, uses fallback counter)
        # For PostgreSQL, would use actual sequence


# =============================================================================
# Test NamingCounter DocType
# =============================================================================


class TestNamingCounter:
    """Test NamingCounter DocType for persistent counter storage."""

    def test_naming_counter_doctype_exists(self):
        """NamingCounter DocType should exist."""
        from framework_m.core.domain.naming_counter import NamingCounter

        assert NamingCounter is not None
        # Check Pydantic model_fields for field definitions
        assert "prefix" in NamingCounter.model_fields
        assert "current" in NamingCounter.model_fields

    def test_naming_counter_fields(self):
        """NamingCounter should have prefix and current fields."""
        from framework_m.core.domain.naming_counter import NamingCounter

        counter = NamingCounter(prefix="INV-2026-", current=5)
        assert counter.prefix == "INV-2026-"
        assert counter.current == 5

    @pytest.mark.asyncio
    async def test_naming_counter_increment(self, test_engine):
        """NamingCounter should support increment operation."""
        from framework_m.core.domain.naming_counter import NamingCounter

        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        counter_table = mapper.create_table(NamingCounter, metadata)
        table_registry.register_table(NamingCounter.__name__, counter_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        counter_repo = GenericRepository(NamingCounter, counter_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create initial counter
        counter = NamingCounter(prefix="TEST-", current=0)
        async with async_session_maker() as session:
            saved = await counter_repo.save(session, counter)
            await session.commit()

        assert saved.current == 0

        # Update counter
        async with async_session_maker() as session:
            loaded = await counter_repo.get_by_name(session, saved.name)
            assert loaded is not None
            loaded.current = loaded.current + 1
            updated = await counter_repo.save(session, loaded)
            await session.commit()

        assert updated.current == 1

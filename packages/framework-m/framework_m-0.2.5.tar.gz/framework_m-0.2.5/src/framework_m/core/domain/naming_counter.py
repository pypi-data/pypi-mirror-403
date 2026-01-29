"""NamingCounter DocType - Persistent counter storage for naming series.

This DocType stores counter values for naming patterns, enabling
optimistic counter management without row-level locking.
"""

from framework_m.core.domain.base_doctype import BaseDocType, Field


class NamingCounter(BaseDocType):
    """Counter storage for naming series.

    Stores the current counter value for each prefix, enabling
    persistent and queryable counter management.

    Example:
        # Counter for INV-2026- prefix
        counter = NamingCounter(prefix="INV-2026-", current=42)

        # Next invoice will be INV-2026-0043

    Note:
        Uses optimistic updates - no SELECT FOR UPDATE needed.
        On conflict, retry with incremented value.
    """

    class Meta:
        """NamingCounter metadata - no auto-naming for counter itself."""

        api_resource = False  # Internal DocType, no API

    # The prefix for which this counter applies (e.g., "INV-2026-")
    prefix: str = Field(description="Naming series prefix")

    # Current counter value (0 means no documents with this prefix yet)
    current: int = Field(default=0, description="Current counter value")

    @classmethod
    def get_counter_name(cls, prefix: str) -> str:
        """Generate a unique name for a counter based on its prefix.

        Args:
            prefix: The naming prefix (e.g., "INV-2026-")

        Returns:
            A unique name for the counter
        """
        # Replace special characters to make a valid name
        safe_prefix = prefix.replace("-", "_").replace(".", "_")
        return f"COUNTER-{safe_prefix}"

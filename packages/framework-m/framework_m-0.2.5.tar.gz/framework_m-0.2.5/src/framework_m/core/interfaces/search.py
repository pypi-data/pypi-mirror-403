"""Search Protocol - Core interface for full-text search.

This module defines the SearchProtocol for full-text search
and indexing operations.

Supports various backends: Meilisearch, Elasticsearch, Whoosh, etc.
"""

from typing import Any, Protocol

from pydantic import BaseModel, computed_field


class SearchResult(BaseModel):
    """Result from a search query.

    Contains matching items with pagination metadata.

    Attributes:
        items: List of matching documents
        total: Total count of matches
        limit: Maximum results per page
        offset: Number of results skipped
        facets: Optional facet/aggregation results
        highlights: Optional highlighted snippets per doc ID
    """

    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int
    facets: dict[str, dict[str, int]] | None = None
    highlights: dict[str, dict[str, str]] | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_more(self) -> bool:
        """Check if more results exist beyond current page."""
        return self.offset + len(self.items) < self.total


class SearchProtocol(Protocol):
    """Protocol defining the contract for full-text search.

    This is the primary port for search operations in the hexagonal
    architecture. Implementations handle different search engines.

    Implementations include:
    - MeilisearchAdapter: Meilisearch search engine
    - ElasticsearchAdapter: Elasticsearch/OpenSearch
    - WhooshAdapter: Pure Python search (for development)

    Example usage:
        search: SearchProtocol = container.get(SearchProtocol)

        # Index a document
        await search.index("Todo", "todo-001", {"title": "Buy milk"})

        # Search
        result = await search.search("Todo", "milk", limit=10)
        for item in result.items:
            print(item["title"])
    """

    async def index(
        self,
        doctype: str,
        doc_id: str,
        doc: dict[str, Any],
    ) -> None:
        """Index a document for searching.

        Args:
            doctype: DocType name (used as index name)
            doc_id: Document identifier
            doc: Document data to index
        """
        ...

    async def delete_index(
        self,
        doctype: str,
        doc_id: str,
    ) -> None:
        """Remove a document from the search index.

        Args:
            doctype: DocType name
            doc_id: Document identifier
        """
        ...

    async def search(
        self,
        doctype: str,
        query: str,
        *,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResult:
        """Search for documents.

        Args:
            doctype: DocType name to search in
            query: Search query string
            filters: Optional field filters
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            SearchResult with matching documents
        """
        ...

    async def reindex(self, doctype: str) -> int:
        """Rebuild the entire index for a DocType.

        Fetches all documents from the repository and re-indexes them.

        Args:
            doctype: DocType name to reindex

        Returns:
            Number of documents indexed
        """
        ...


__all__ = [
    "SearchProtocol",
    "SearchResult",
]

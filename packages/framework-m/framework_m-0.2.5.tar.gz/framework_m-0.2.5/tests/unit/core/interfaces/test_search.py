"""Tests for SearchProtocol interface compliance."""

from framework_m.core.interfaces.search import (
    SearchProtocol,
    SearchResult,
)


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_search_result_creation(self) -> None:
        """SearchResult should create with required fields."""
        result = SearchResult(
            items=[{"id": "1", "title": "Test"}],
            total=10,
            limit=20,
            offset=0,
        )
        assert len(result.items) == 1
        assert result.total == 10

    def test_search_result_with_facets(self) -> None:
        """SearchResult should support facets."""
        result = SearchResult(
            items=[],
            total=0,
            limit=20,
            offset=0,
            facets={"status": {"draft": 5, "published": 10}},
        )
        assert result.facets == {"status": {"draft": 5, "published": 10}}

    def test_search_result_with_highlights(self) -> None:
        """SearchResult should support highlights."""
        result = SearchResult(
            items=[{"id": "1"}],
            total=1,
            limit=20,
            offset=0,
            highlights={"1": {"title": "Test <em>match</em>"}},
        )
        assert result.highlights is not None and "1" in result.highlights

    def test_search_result_has_more(self) -> None:
        """SearchResult.has_more should indicate more results available."""
        result = SearchResult(
            items=[{"id": "1"}],
            total=10,
            limit=1,
            offset=0,
        )
        assert result.has_more is True


class TestSearchProtocol:
    """Tests for SearchProtocol interface."""

    def test_protocol_has_index_method(self) -> None:
        """SearchProtocol should define index method."""
        assert hasattr(SearchProtocol, "index")

    def test_protocol_has_delete_index_method(self) -> None:
        """SearchProtocol should define delete_index method."""
        assert hasattr(SearchProtocol, "delete_index")

    def test_protocol_has_search_method(self) -> None:
        """SearchProtocol should define search method."""
        assert hasattr(SearchProtocol, "search")

    def test_protocol_has_reindex_method(self) -> None:
        """SearchProtocol should define reindex method."""
        assert hasattr(SearchProtocol, "reindex")

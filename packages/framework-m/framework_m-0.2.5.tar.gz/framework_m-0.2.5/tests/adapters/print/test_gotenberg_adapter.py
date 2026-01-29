"""Tests for Gotenberg Print Adapter.

Tests cover:
- GotenbergPrintAdapter initialization
- GotenbergConfig model
- Page sizes and dimensions
"""

import pytest

from framework_m.adapters.print.gotenberg_adapter import (
    PAGE_SIZES,
    GotenbergConfig,
    GotenbergPrintAdapter,
)

# =============================================================================
# Test: Import
# =============================================================================


class TestGotenbergImport:
    """Tests for Gotenberg adapter imports."""

    def test_import_gotenberg_adapter(self) -> None:
        """GotenbergPrintAdapter should be importable."""
        from framework_m.adapters.print import GotenbergPrintAdapter

        assert GotenbergPrintAdapter is not None

    def test_import_gotenberg_config(self) -> None:
        """GotenbergConfig should be importable."""
        from framework_m.adapters.print import GotenbergConfig

        assert GotenbergConfig is not None

    def test_import_page_sizes(self) -> None:
        """PAGE_SIZES should be importable."""
        from framework_m.adapters.print import PAGE_SIZES

        assert PAGE_SIZES is not None


# =============================================================================
# Test: GotenbergConfig
# =============================================================================


class TestGotenbergConfig:
    """Tests for GotenbergConfig model."""

    def test_default_values(self) -> None:
        """Config should have sensible defaults."""
        config = GotenbergConfig()

        assert config.url == "http://localhost:3000"
        assert config.timeout == 30.0
        assert config.page_size == "A4"
        assert config.orientation == "portrait"

    def test_custom_values(self) -> None:
        """Config should accept custom values."""
        config = GotenbergConfig(
            url="http://gotenberg:3000",
            page_size="Letter",
            orientation="landscape",
        )

        assert config.url == "http://gotenberg:3000"
        assert config.page_size == "Letter"
        assert config.orientation == "landscape"

    def test_margin_defaults(self) -> None:
        """Config should have default margins."""
        config = GotenbergConfig()

        assert config.margin_top == 0.5
        assert config.margin_bottom == 0.5
        assert config.margin_left == 0.5
        assert config.margin_right == 0.5


# =============================================================================
# Test: PAGE_SIZES
# =============================================================================


class TestPageSizes:
    """Tests for page size constants."""

    def test_a4_dimensions(self) -> None:
        """A4 should have correct dimensions."""
        width, height = PAGE_SIZES["A4"]
        assert width == pytest.approx(8.27, abs=0.01)
        assert height == pytest.approx(11.69, abs=0.01)

    def test_letter_dimensions(self) -> None:
        """Letter should have correct dimensions."""
        width, height = PAGE_SIZES["Letter"]
        assert width == 8.5
        assert height == 11

    def test_all_sizes_defined(self) -> None:
        """All expected page sizes should be defined."""
        expected = ["A4", "Letter", "Legal", "A3", "A5"]
        for size in expected:
            assert size in PAGE_SIZES


# =============================================================================
# Test: GotenbergPrintAdapter
# =============================================================================


class TestGotenbergPrintAdapter:
    """Tests for GotenbergPrintAdapter class."""

    def test_init_with_url(self) -> None:
        """Adapter should accept URL."""
        adapter = GotenbergPrintAdapter(gotenberg_url="http://test:3000")
        assert adapter._config.url == "http://test:3000"

    def test_init_with_config(self) -> None:
        """Adapter should accept full config."""
        config = GotenbergConfig(
            url="http://custom:3000",
            page_size="Letter",
        )
        adapter = GotenbergPrintAdapter(config=config)

        assert adapter._config.url == "http://custom:3000"
        assert adapter._config.page_size == "Letter"

    def test_has_html_to_pdf_method(self) -> None:
        """Adapter should have html_to_pdf method."""
        assert hasattr(GotenbergPrintAdapter, "html_to_pdf")

    def test_has_is_available_method(self) -> None:
        """Adapter should have is_available method."""
        assert hasattr(GotenbergPrintAdapter, "is_available")

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Adapter should work as context manager."""
        async with GotenbergPrintAdapter() as adapter:
            assert adapter is not None

    @pytest.mark.asyncio
    async def test_is_available_returns_false_when_not_running(self) -> None:
        """is_available should return False when Gotenberg is not running."""
        adapter = GotenbergPrintAdapter(gotenberg_url="http://localhost:9999")
        result = await adapter.is_available()
        await adapter.close()

        assert result is False


# =============================================================================
# Test: html_to_pdf with mocked HTTP
# =============================================================================


class TestHtmlToPdf:
    """Tests for html_to_pdf method with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_html_to_pdf_success(self) -> None:
        """html_to_pdf should return PDF bytes on success."""
        from unittest.mock import AsyncMock, patch

        adapter = GotenbergPrintAdapter()

        # Mock the httpx post
        mock_response = AsyncMock()
        mock_response.content = b"%PDF-1.4 mock pdf content"
        mock_response.raise_for_status = AsyncMock()

        with patch.object(adapter._client, "post", return_value=mock_response):
            result = await adapter.html_to_pdf("<h1>Test</h1>")

        assert result == b"%PDF-1.4 mock pdf content"
        await adapter.close()

    @pytest.mark.asyncio
    async def test_html_to_pdf_with_page_size(self) -> None:
        """html_to_pdf should use custom page size."""
        from unittest.mock import AsyncMock, patch

        adapter = GotenbergPrintAdapter()

        mock_response = AsyncMock()
        mock_response.content = b"pdf"
        mock_response.raise_for_status = AsyncMock()

        with patch.object(
            adapter._client, "post", return_value=mock_response
        ) as mock_post:
            await adapter.html_to_pdf("<h1>Test</h1>", page_size="Letter")

        # Check that post was called
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["data"]["paperWidth"] == "8.5"
        assert call_kwargs.kwargs["data"]["paperHeight"] == "11"
        await adapter.close()

    @pytest.mark.asyncio
    async def test_html_to_pdf_landscape_orientation(self) -> None:
        """html_to_pdf should swap dimensions for landscape."""
        from unittest.mock import AsyncMock, patch

        adapter = GotenbergPrintAdapter()

        mock_response = AsyncMock()
        mock_response.content = b"pdf"
        mock_response.raise_for_status = AsyncMock()

        with patch.object(
            adapter._client, "post", return_value=mock_response
        ) as mock_post:
            await adapter.html_to_pdf("<h1>Test</h1>", orientation="landscape")

        call_kwargs = mock_post.call_args
        # A4 landscape: width and height should be swapped
        assert float(call_kwargs.kwargs["data"]["paperWidth"]) > float(
            call_kwargs.kwargs["data"]["paperHeight"]
        )
        await adapter.close()

    @pytest.mark.asyncio
    async def test_html_to_pdf_with_header(self) -> None:
        """html_to_pdf should include header HTML."""
        from unittest.mock import AsyncMock, patch

        adapter = GotenbergPrintAdapter()

        mock_response = AsyncMock()
        mock_response.content = b"pdf"
        mock_response.raise_for_status = AsyncMock()

        with patch.object(
            adapter._client, "post", return_value=mock_response
        ) as mock_post:
            await adapter.html_to_pdf(
                "<h1>Body</h1>",
                header_html="<div>Header</div>",
            )

        call_kwargs = mock_post.call_args
        files = call_kwargs.kwargs["files"]
        assert "header.html" in files
        await adapter.close()

    @pytest.mark.asyncio
    async def test_html_to_pdf_with_footer(self) -> None:
        """html_to_pdf should include footer HTML."""
        from unittest.mock import AsyncMock, patch

        adapter = GotenbergPrintAdapter()

        mock_response = AsyncMock()
        mock_response.content = b"pdf"
        mock_response.raise_for_status = AsyncMock()

        with patch.object(
            adapter._client, "post", return_value=mock_response
        ) as mock_post:
            await adapter.html_to_pdf(
                "<h1>Body</h1>",
                footer_html="<div>Page Footer</div>",
            )

        call_kwargs = mock_post.call_args
        files = call_kwargs.kwargs["files"]
        assert "footer.html" in files
        await adapter.close()

    @pytest.mark.asyncio
    async def test_html_to_pdf_unknown_page_size_falls_back_to_a4(self) -> None:
        """html_to_pdf should fall back to A4 for unknown page size."""
        from unittest.mock import AsyncMock, patch

        adapter = GotenbergPrintAdapter()

        mock_response = AsyncMock()
        mock_response.content = b"pdf"
        mock_response.raise_for_status = AsyncMock()

        with patch.object(
            adapter._client, "post", return_value=mock_response
        ) as mock_post:
            await adapter.html_to_pdf("<h1>Test</h1>", page_size="Unknown")

        call_kwargs = mock_post.call_args
        # Falls back to A4
        assert call_kwargs.kwargs["data"]["paperWidth"] == "8.27"
        await adapter.close()


class TestIsAvailable:
    """Tests for is_available method."""

    @pytest.mark.asyncio
    async def test_is_available_returns_true_on_200(self) -> None:
        """is_available should return True when health returns 200."""
        from unittest.mock import AsyncMock, patch

        adapter = GotenbergPrintAdapter()

        mock_response = AsyncMock()
        mock_response.status_code = 200

        with patch.object(adapter._client, "get", return_value=mock_response):
            result = await adapter.is_available()

        assert result is True
        await adapter.close()

    @pytest.mark.asyncio
    async def test_is_available_returns_false_on_500(self) -> None:
        """is_available should return False when health returns non-200."""
        from unittest.mock import AsyncMock, patch

        adapter = GotenbergPrintAdapter()

        mock_response = AsyncMock()
        mock_response.status_code = 500

        with patch.object(adapter._client, "get", return_value=mock_response):
            result = await adapter.is_available()

        assert result is False
        await adapter.close()

    @pytest.mark.asyncio
    async def test_is_available_handles_request_error(self) -> None:
        """is_available should return False on request error."""
        from unittest.mock import patch

        import httpx

        adapter = GotenbergPrintAdapter()

        with patch.object(
            adapter._client, "get", side_effect=httpx.RequestError("Connection failed")
        ):
            result = await adapter.is_available()

        assert result is False
        await adapter.close()

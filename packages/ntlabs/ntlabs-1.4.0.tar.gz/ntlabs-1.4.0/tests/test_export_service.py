"""
Tests for ntlabs.export module.

Tests export styles, generators, and service.
Note: PDF/Excel tests require optional dependencies (reportlab, openpyxl).
"""

import io
import zipfile

import pytest

from ntlabs.export import (
    CSVExporter,
    ExcelStyle,
    # Service
    ExportService,
    # Styles
    PDFStyle,
    # CSV
    generate_csv,
)

# =============================================================================
# Style Tests
# =============================================================================


class TestExportStyles:
    """Tests for export styles."""

    def test_pdf_style_values(self):
        """Test PDFStyle enum values."""
        assert PDFStyle.REPORT.value == "report"
        assert PDFStyle.MEDICAL.value == "medical"
        assert PDFStyle.INVESTIGATION.value == "investigation"
        assert PDFStyle.SIMPLE.value == "simple"
        assert PDFStyle.INVOICE.value == "invoice"

    def test_excel_style_values(self):
        """Test ExcelStyle enum values."""
        assert ExcelStyle.DEFAULT.value == "default"
        assert ExcelStyle.FINANCIAL.value == "financial"
        assert ExcelStyle.MEDICAL.value == "medical"
        assert ExcelStyle.DASHBOARD.value == "dashboard"


# =============================================================================
# CSV Export Tests
# =============================================================================


class TestCSVExport:
    """Tests for CSV export."""

    def test_generate_csv_list_of_dicts(self):
        """Test CSV generation from list of dicts."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = generate_csv(data)
        assert isinstance(result, bytes)
        text = result.decode("utf-8-sig")
        assert "name" in text
        assert "Alice" in text
        assert "Bob" in text

    def test_generate_csv_list_of_lists(self):
        """Test CSV generation from list of lists."""
        data = [
            ["Name", "Age"],
            ["Alice", 30],
            ["Bob", 25],
        ]
        result = generate_csv(data)
        assert isinstance(result, bytes)
        text = result.decode("utf-8-sig")
        assert "Name" in text
        assert "Alice" in text

    def test_generate_csv_custom_delimiter(self):
        """Test CSV generation with custom delimiter."""
        data = [{"a": 1, "b": 2}]
        result = generate_csv(data, delimiter=";")
        text = result.decode("utf-8-sig")
        assert ";" in text

    def test_generate_csv_encoding(self):
        """Test CSV generation with specific encoding."""
        data = [{"name": "José", "city": "São Paulo"}]
        result = generate_csv(data, encoding="utf-8-sig")
        text = result.decode("utf-8-sig")
        assert "José" in text
        assert "São Paulo" in text

    def test_csv_exporter_brazilian_format(self):
        """Test Brazilian CSV format (semicolon, comma decimal)."""
        exporter = CSVExporter(delimiter=";", decimal_separator=",")
        data = [{"nome": "Teste", "valor": 1234.56}]
        result = exporter.export(data)
        text = result.decode("utf-8-sig")
        # Brazilian format uses semicolon separator between fields
        assert ";" in text
        assert "nome" in text
        assert "valor" in text
        # Decimal separator should be comma
        assert "1234,56" in text


# =============================================================================
# Export Service Tests
# =============================================================================


class TestExportService:
    """Tests for ExportService."""

    def test_service_initialization(self):
        """Test ExportService initialization."""
        service = ExportService(
            default_author="Test Author",
            pdf_style=PDFStyle.REPORT,
            excel_style=ExcelStyle.DEFAULT,
        )
        assert service.default_author == "Test Author"
        assert service.pdf_style == PDFStyle.REPORT

    def test_service_default_values(self):
        """Test ExportService default values."""
        service = ExportService()
        assert service.default_author is None
        assert service.pdf_style == PDFStyle.REPORT
        assert service.excel_style == ExcelStyle.DEFAULT

    def test_to_csv(self):
        """Test to_csv method."""
        service = ExportService()
        data = [{"id": 1, "name": "Test"}]
        result = service.to_csv(data)
        assert isinstance(result, bytes)
        assert b"id" in result
        assert b"Test" in result

    def test_to_csv_brazilian_format(self):
        """Test to_csv with Brazilian format."""
        service = ExportService()
        data = [{"id": 1, "value": 1000}]
        result = service.to_csv(data, brazilian_format=True)
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_to_zip(self):
        """Test to_zip method."""
        service = ExportService()
        files = [
            {"filename": "file1.txt", "content": b"Content 1"},
            {"filename": "file2.txt", "content": "Content 2"},
        ]
        result = await service.to_zip(files)

        # Verify it's a valid ZIP
        assert isinstance(result, bytes)
        buffer = io.BytesIO(result)
        with zipfile.ZipFile(buffer, "r") as zf:
            names = zf.namelist()
            assert "file1.txt" in names
            assert "file2.txt" in names
            assert zf.read("file1.txt") == b"Content 1"
            assert zf.read("file2.txt") == b"Content 2"

    @pytest.mark.asyncio
    async def test_to_zip_empty(self):
        """Test to_zip with empty files list."""
        service = ExportService()
        result = await service.to_zip([])
        assert isinstance(result, bytes)
        buffer = io.BytesIO(result)
        with zipfile.ZipFile(buffer, "r") as zf:
            assert len(zf.namelist()) == 0


# =============================================================================
# PDF Export Tests (require reportlab)
# =============================================================================


class TestPDFExport:
    """Tests for PDF export (requires reportlab)."""

    @pytest.mark.skip(reason="Requires reportlab package")
    @pytest.mark.asyncio
    async def test_to_pdf_basic(self):
        """Test basic PDF generation."""
        service = ExportService()
        result = await service.to_pdf(
            title="Test Report",
            content="# Summary\n\nThis is a test report.",
        )
        assert isinstance(result, bytes)
        # PDF magic bytes
        assert result[:4] == b"%PDF"

    @pytest.mark.skip(reason="Requires reportlab package")
    @pytest.mark.asyncio
    async def test_to_pdf_with_metadata(self):
        """Test PDF generation with metadata."""
        service = ExportService()
        result = await service.to_pdf(
            title="Report",
            content="Content",
            metadata={"Department": "Engineering"},
            author="Test Author",
        )
        assert isinstance(result, bytes)


# =============================================================================
# Excel Export Tests (require openpyxl)
# =============================================================================


class TestExcelExport:
    """Tests for Excel export (requires openpyxl)."""

    @pytest.mark.skip(reason="Requires openpyxl package")
    @pytest.mark.asyncio
    async def test_to_excel_basic(self):
        """Test basic Excel generation."""
        service = ExportService()
        data = [{"name": "Alice", "age": 30}]
        result = await service.to_excel(sheets=data, title="Test")
        assert isinstance(result, bytes)
        # XLSX magic bytes (ZIP format)
        assert result[:2] == b"PK"

    @pytest.mark.skip(reason="Requires openpyxl package")
    @pytest.mark.asyncio
    async def test_to_excel_multiple_sheets(self):
        """Test Excel generation with multiple sheets."""
        service = ExportService()
        sheets = {
            "Users": [{"name": "Alice"}],
            "Products": [{"name": "Widget"}],
        }
        result = await service.to_excel(sheets=sheets, title="Multi-sheet")
        assert isinstance(result, bytes)

    @pytest.mark.skip(reason="Requires openpyxl package")
    @pytest.mark.asyncio
    async def test_to_multiple_formats(self):
        """Test exporting to multiple formats."""
        service = ExportService()
        data = [{"id": 1, "name": "Test"}]
        results = await service.to_multiple_formats(
            data=data,
            title="Export",
            formats=["xlsx", "csv"],
        )
        assert "xlsx" in results
        assert "csv" in results
        assert isinstance(results["csv"], bytes)

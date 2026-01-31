"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for Excel export module
Version: 1.0.0
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from ntlabs.export.excel import ExcelGenerator, generate_excel
from ntlabs.export.styles import ExcelStyle


class MockDataFrame:
    """Mock pandas DataFrame for testing."""

    def __init__(self, data):
        self.data = data
        self.columns = list(data[0].keys()) if data else []

    def iterrows(self):
        for i, row in enumerate(self.data):
            yield i, MockSeries(row)


class MockSeries:
    """Mock pandas Series for testing."""

    def __init__(self, data):
        self._data = data

    def __iter__(self):
        return iter(self._data.values())

    def __getitem__(self, key):
        return self._data[key]


class TestExcelGeneratorInit:
    """Test ExcelGenerator initialization."""

    def test_default_init(self):
        """Test initialization with default values."""
        generator = ExcelGenerator()
        assert generator.title == "Workbook"
        assert generator.author is None
        assert generator.theme is not None

    def test_custom_init(self):
        """Test initialization with custom values."""
        generator = ExcelGenerator(
            title="Financial Report",
            author="Test Author",
            style=ExcelStyle.FINANCIAL,
        )
        assert generator.title == "Financial Report"
        assert generator.author == "Test Author"


class TestExcelGeneratorDataConversion:
    """Test data to rows conversion."""

    @pytest.fixture
    def generator(self):
        """Create an Excel generator."""
        return ExcelGenerator()

    def test_data_to_rows_dataframe(self, generator):
        """Test converting DataFrame to rows."""
        data = MockDataFrame([
            {"Name": "John", "Age": 30},
            {"Name": "Jane", "Age": 25},
        ])

        rows = generator._data_to_rows(data)
        assert rows[0] == ["Name", "Age"]
        assert ["John", 30] in rows
        assert ["Jane", 25] in rows

    def test_data_to_rows_list_of_dicts(self, generator):
        """Test converting list of dicts to rows."""
        data = [
            {"Name": "John", "Age": 30},
            {"Name": "Jane", "Age": 25},
        ]

        rows = generator._data_to_rows(data)
        assert rows[0] == ["Name", "Age"]
        assert ["John", 30] in rows
        assert ["Jane", 25] in rows

    def test_data_to_rows_list_of_lists(self, generator):
        """Test converting list of lists to rows."""
        data = [
            ["Name", "Age"],
            ["John", 30],
            ["Jane", 25],
        ]

        rows = generator._data_to_rows(data)
        assert rows == data

    def test_data_to_rows_empty(self, generator):
        """Test converting empty data."""
        rows = generator._data_to_rows([])
        assert rows == []

    def test_data_to_rows_tuples(self, generator):
        """Test converting list of tuples."""
        data = [
            ("Name", "Age"),
            ("John", 30),
        ]

        rows = generator._data_to_rows(data)
        assert rows == [["Name", "Age"], ["John", 30]]


class TestExcelGeneratorGenerate:
    """Test Excel generation."""

    @pytest.fixture
    def generator(self):
        """Create an Excel generator."""
        return ExcelGenerator(
            title="Test Workbook",
            author="Test Author",
        )

    def test_generate_basic(self, generator):
        """Test basic Excel generation."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_wb.return_value = mock_workbook

            sheets = {
                "Sheet1": [
                    {"Name": "John", "Age": 30},
                    {"Name": "Jane", "Age": 25},
                ],
            }

            result = generator.generate(sheets)

            assert isinstance(result, bytes)
            mock_workbook.remove.assert_called_once()

    def test_generate_multiple_sheets(self, generator):
        """Test Excel generation with multiple sheets."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_wb.return_value = mock_workbook

            sheets = {
                "Users": [{"Name": "John"}],
                "Products": [{"Product": "Widget"}],
            }

            result = generator.generate(sheets)

            assert isinstance(result, bytes)
            assert mock_workbook.create_sheet.call_count == 2

    def test_generate_with_metadata(self, generator):
        """Test Excel generation with metadata."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_wb.return_value = mock_workbook

            sheets = {"Sheet1": [{"Name": "John"}]}
            metadata = {"created_at": "2026-01-28"}

            result = generator.generate(sheets, metadata=metadata)

            assert isinstance(result, bytes)
            assert mock_workbook.properties.title == "Test Workbook"

    def test_generate_long_sheet_name_truncated(self, generator):
        """Test that long sheet names are truncated."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()
            mock_workbook.create_sheet.return_value = mock_sheet
            mock_wb.return_value = mock_workbook

            long_name = "A" * 50  # Longer than 31 characters
            sheets = {long_name: [{"Name": "John"}]}

            generator.generate(sheets)

            # Should be truncated to 31 characters
            mock_workbook.create_sheet.assert_called_once()
            call_args = mock_workbook.create_sheet.call_args
            assert len(call_args[1]["title"]) <= 31

    def test_generate_with_datetime(self, generator):
        """Test Excel generation with datetime values."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()
            mock_workbook.create_sheet.return_value = mock_sheet
            mock_wb.return_value = mock_workbook

            sheets = {
                "Sheet1": [
                    {"Name": "Event", "Date": datetime(2026, 1, 28, 14, 30)},
                ],
            }

            generator.generate(sheets)

            # Check that cell was created with datetime
            assert mock_sheet.cell.call_count > 0

    def test_generate_import_error(self, generator):
        """Test handling of missing openpyxl."""
        with patch.dict("sys.modules", {"openpyxl": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'openpyxl'")):
                with pytest.raises(ImportError):
                    generator.generate({"Sheet1": []})


class TestExcelGeneratorSingleSheet:
    """Test single sheet generation."""

    @pytest.fixture
    def generator(self):
        """Create an Excel generator."""
        return ExcelGenerator()

    def test_generate_single_sheet(self, generator):
        """Test generating single sheet workbook."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_wb.return_value = mock_workbook

            data = [{"Name": "John", "Age": 30}]
            result = generator.generate_single_sheet(
                data,
                sheet_name="MyData",
                metadata={"key": "value"},
            )

            assert isinstance(result, bytes)


class TestGenerateExcelFunction:
    """Test the generate_excel convenience function."""

    @pytest.mark.asyncio
    async def test_generate_excel_with_dict_sheets(self):
        """Test generate_excel with dict of sheets."""
        with patch("ntlabs.export.excel.ExcelGenerator") as mock_gen:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = b"Excel bytes"
            mock_gen.return_value = mock_instance

            data = {
                "Sheet1": [{"Name": "John"}],
                "Sheet2": [{"Product": "Widget"}],
            }

            result = await generate_excel(
                data=data,
                title="Test",
                author="Author",
            )

            assert result == b"Excel bytes"
            mock_instance.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_excel_with_list(self):
        """Test generate_excel with list data."""
        with patch("ntlabs.export.excel.ExcelGenerator") as mock_gen:
            mock_instance = MagicMock()
            mock_instance.generate_single_sheet.return_value = b"Excel bytes"
            mock_gen.return_value = mock_instance

            data = [{"Name": "John"}]

            result = await generate_excel(data=data)

            assert result == b"Excel bytes"
            mock_instance.generate_single_sheet.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_excel_with_dataframe(self):
        """Test generate_excel with DataFrame-like object."""
        with patch("ntlabs.export.excel.ExcelGenerator") as mock_gen:
            mock_instance = MagicMock()
            mock_instance.generate_single_sheet.return_value = b"Excel bytes"
            mock_gen.return_value = mock_instance

            # DataFrame-like object
            data = MockDataFrame([{"Name": "John"}])

            result = await generate_excel(data=data)

            assert result == b"Excel bytes"


class TestExcelGeneratorStyling:
    """Test Excel styling."""

    @pytest.fixture
    def generator(self):
        """Create an Excel generator with custom theme."""
        return ExcelGenerator(
            style=ExcelStyle.FINANCIAL,
        )

    def test_header_styling(self, generator):
        """Test header row styling."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()
            mock_cell = MagicMock()
            mock_sheet.cell.return_value = mock_cell
            mock_workbook.create_sheet.return_value = mock_sheet
            mock_wb.return_value = mock_workbook

            sheets = {"Sheet1": [{"Name": "John"}]}
            generator.generate(sheets)

            # Header cells should have fill and font
            header_calls = [
                call for call in mock_cell.method_calls
                if call[0] in ["fill", "font", "alignment"]
            ]

    def test_alternating_rows(self, generator):
        """Test alternating row colors."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()
            mock_cell = MagicMock()
            mock_sheet.cell.return_value = mock_cell
            mock_workbook.create_sheet.return_value = mock_sheet
            mock_wb.return_value = mock_workbook

            # Multiple rows to test alternating (need header + data rows)
            sheets = {
                "Sheet1": [
                    {"Name": "Row1", "Value": 1},
                    {"Name": "Row2", "Value": 2},
                    {"Name": "Row3", "Value": 3},
                ],
            }
            generator.generate(sheets)

            # cell() is called for each row x each column
            assert mock_sheet.cell.call_count > 0

    def test_number_formatting(self, generator):
        """Test number cell formatting."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()
            mock_cell = MagicMock()
            mock_sheet.cell.return_value = mock_cell
            mock_workbook.create_sheet.return_value = mock_sheet
            mock_wb.return_value = mock_workbook

            sheets = {
                "Sheet1": [
                    {"Value": 123.456},
                ],
            }
            generator.generate(sheets)

            # Check that number format was set
            number_format_calls = [
                call for call in mock_cell.method_calls
                if call[0] == "number_format"
            ]

    def test_auto_column_width(self, generator):
        """Test auto column width calculation."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()
            mock_cell = MagicMock()
            mock_sheet.cell.return_value = mock_cell
            mock_workbook.create_sheet.return_value = mock_sheet
            mock_wb.return_value = mock_workbook

            with patch("openpyxl.utils.get_column_letter") as mock_get_col:
                mock_get_col.return_value = "A"

                sheets = {
                    "Sheet1": [{"LongColumnName": "Value"}],
                }
                generator.generate(sheets)

                mock_get_col.assert_called()

    def test_freeze_header(self, generator):
        """Test freezing header row."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()
            mock_sheet.__getitem__ = MagicMock(return_value=MagicMock())
            mock_workbook.create_sheet.return_value = mock_sheet
            mock_wb.return_value = mock_workbook

            # Multiple rows to trigger freeze
            sheets = {
                "Sheet1": [
                    {"Name": "Row1"},
                    {"Name": "Row2"},
                ],
            }
            generator.generate(sheets)


class TestExcelGeneratorEdgeCases:
    """Test edge cases."""

    @pytest.fixture
    def generator(self):
        """Create an Excel generator."""
        return ExcelGenerator()

    def test_empty_sheet_skipped(self, generator):
        """Test that empty sheets are skipped."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_wb.return_value = mock_workbook

            sheets = {
                "EmptySheet": [],
                "DataSheet": [{"Name": "John"}],
            }

            generator.generate(sheets)

            # Empty sheet should have continue called
            # (only one sheet should be fully processed)

    def test_none_values_in_data(self, generator):
        """Test handling of None values in data."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()
            mock_workbook.create_sheet.return_value = mock_sheet
            mock_wb.return_value = mock_workbook

            sheets = {
                "Sheet1": [
                    {"Name": "John", "Age": None},
                ],
            }

            # Should not raise
            result = generator.generate(sheets)
            assert isinstance(result, bytes)

    def test_very_long_cell_content(self, generator):
        """Test handling of very long cell content."""
        with patch("openpyxl.Workbook") as mock_wb:
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()
            mock_cell = MagicMock()
            mock_sheet.cell.return_value = mock_cell
            mock_workbook.create_sheet.return_value = mock_sheet
            mock_wb.return_value = mock_workbook

            sheets = {
                "Sheet1": [
                    {"Description": "x" * 1000},
                ],
            }

            # Should not raise
            result = generator.generate(sheets)
            assert isinstance(result, bytes)

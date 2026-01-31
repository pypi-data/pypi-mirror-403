"""
CSV export utilities.

Provides CSV generation with various encoding and formatting options.
"""

import csv
import io
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Type alias for dataframe-like objects
DataFrameLike = Any  # pandas.DataFrame


def generate_csv(
    data: DataFrameLike | list[dict] | list[list],
    encoding: str = "utf-8-sig",
    delimiter: str = ",",
    quoting: int = csv.QUOTE_MINIMAL,
    include_bom: bool = True,
) -> bytes:
    """
    Generate CSV from data.

    Args:
        data: Data to export (DataFrame, list of dicts, or list of lists)
        encoding: Output encoding (utf-8-sig recommended for Excel compatibility)
        delimiter: Field delimiter
        quoting: CSV quoting style
        include_bom: Include BOM for Excel UTF-8 detection

    Returns:
        CSV bytes

    Example:
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
        ]
        csv_bytes = generate_csv(data)
    """
    buffer = io.StringIO()

    # Convert data to rows
    rows = _data_to_rows(data)
    if not rows:
        return b""

    # Write CSV
    writer = csv.writer(buffer, delimiter=delimiter, quoting=quoting)
    for row in rows:
        writer.writerow(row)

    # Encode
    content = buffer.getvalue()

    # Add BOM if requested and using UTF-8
    if include_bom and encoding.lower().startswith("utf-8"):
        encoding = "utf-8-sig"

    return content.encode(encoding)


def _data_to_rows(data: DataFrameLike | list[dict] | list[list]) -> list[list]:
    """Convert various data formats to list of lists."""
    if not data:
        return []

    # Check if it's a pandas DataFrame
    if hasattr(data, "iterrows") and hasattr(data, "columns"):
        headers = list(data.columns)
        rows = [headers]
        for _, row in data.iterrows():
            rows.append(list(row))
        return rows

    # List of dicts
    if isinstance(data[0], dict):
        headers = list(data[0].keys())
        rows = [headers]
        for item in data:
            rows.append([item.get(h) for h in headers])
        return rows

    # List of lists (assume first row is headers or data)
    if isinstance(data[0], (list, tuple)):
        return [list(row) for row in data]

    return []


def generate_csv_string(
    data: DataFrameLike | list[dict] | list[list],
    delimiter: str = ",",
) -> str:
    """
    Generate CSV as string.

    Args:
        data: Data to export
        delimiter: Field delimiter

    Returns:
        CSV string
    """
    csv_bytes = generate_csv(data, delimiter=delimiter, include_bom=False)
    return csv_bytes.decode("utf-8")


class CSVExporter:
    """
    CSV exporter with advanced options.

    Example:
        exporter = CSVExporter(
            delimiter=";",
            decimal_separator=",",
            date_format="%d/%m/%Y",
        )
        csv_bytes = exporter.export(data)
    """

    def __init__(
        self,
        delimiter: str = ",",
        quoting: int = csv.QUOTE_MINIMAL,
        encoding: str = "utf-8-sig",
        date_format: str = "%Y-%m-%d",
        datetime_format: str = "%Y-%m-%d %H:%M:%S",
        decimal_separator: str = ".",
        thousands_separator: str = "",
        null_value: str = "",
    ):
        """
        Initialize CSV exporter.

        Args:
            delimiter: Field delimiter
            quoting: CSV quoting style
            encoding: Output encoding
            date_format: Format for date values
            datetime_format: Format for datetime values
            decimal_separator: Decimal separator for numbers
            thousands_separator: Thousands separator for numbers
            null_value: String to use for None values
        """
        self.delimiter = delimiter
        self.quoting = quoting
        self.encoding = encoding
        self.date_format = date_format
        self.datetime_format = datetime_format
        self.decimal_separator = decimal_separator
        self.thousands_separator = thousands_separator
        self.null_value = null_value

    def export(
        self,
        data: DataFrameLike | list[dict] | list[list],
    ) -> bytes:
        """
        Export data to CSV.

        Args:
            data: Data to export

        Returns:
            CSV bytes
        """
        buffer = io.StringIO()
        rows = _data_to_rows(data)

        if not rows:
            return b""

        writer = csv.writer(
            buffer,
            delimiter=self.delimiter,
            quoting=self.quoting,
        )

        for row in rows:
            formatted_row = [self._format_value(v) for v in row]
            writer.writerow(formatted_row)

        return buffer.getvalue().encode(self.encoding)

    def _format_value(self, value: Any) -> str:
        """Format a single value for CSV output."""
        from datetime import date, datetime

        if value is None:
            return self.null_value

        if isinstance(value, datetime):
            return value.strftime(self.datetime_format)

        if isinstance(value, date):
            return value.strftime(self.date_format)

        if isinstance(value, float):
            formatted = f"{value:,.2f}"
            if self.thousands_separator != ",":
                formatted = formatted.replace(",", self.thousands_separator)
            if self.decimal_separator != ".":
                formatted = formatted.replace(".", self.decimal_separator)
            return formatted

        return str(value)


# Brazilian format presets
BR_CSV_EXPORTER = CSVExporter(
    delimiter=";",
    decimal_separator=",",
    thousands_separator=".",
    date_format="%d/%m/%Y",
    datetime_format="%d/%m/%Y %H:%M:%S",
)

# US format presets
US_CSV_EXPORTER = CSVExporter(
    delimiter=",",
    decimal_separator=".",
    thousands_separator=",",
    date_format="%m/%d/%Y",
    datetime_format="%m/%d/%Y %H:%M:%S",
)

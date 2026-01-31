"""
Export service - High-level interface for document exports.

Provides a unified interface for exporting data to various formats.
"""

import io
import logging
import zipfile
from datetime import datetime
from typing import Any

from .csv import generate_csv
from .excel import ExcelGenerator
from .pdf import PDFGenerator
from .styles import ExcelStyle, PDFStyle

logger = logging.getLogger(__name__)

# Type alias
DataFrameLike = Any


class ExportService:
    """
    High-level export service.

    Supports PDF, Excel, CSV, and ZIP exports.

    Example:
        export = ExportService()

        # PDF from markdown
        pdf_bytes = await export.to_pdf(
            title="Report",
            content="# Summary\\n\\nContent...",
            style=PDFStyle.REPORT,
        )

        # Excel from data
        excel_bytes = await export.to_excel(
            title="Data Export",
            sheets={"Sheet1": data},
        )

        # CSV
        csv_bytes = export.to_csv(data)

        # ZIP multiple files
        zip_bytes = await export.to_zip([
            {"filename": "report.pdf", "content": pdf_bytes},
            {"filename": "data.xlsx", "content": excel_bytes},
        ])
    """

    def __init__(
        self,
        default_author: str | None = None,
        pdf_style: PDFStyle = PDFStyle.REPORT,
        excel_style: ExcelStyle = ExcelStyle.DEFAULT,
    ):
        """
        Initialize export service.

        Args:
            default_author: Default author for generated documents
            pdf_style: Default PDF style
            excel_style: Default Excel style
        """
        self.default_author = default_author
        self.pdf_style = pdf_style
        self.excel_style = excel_style

    async def to_pdf(
        self,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        style: PDFStyle | None = None,
        author: str | None = None,
    ) -> bytes:
        """
        Generate PDF from markdown content.

        Args:
            title: Document title
            content: Markdown content
            metadata: Document metadata
            style: PDF style (uses default if not specified)
            author: Document author (uses default if not specified)

        Returns:
            PDF bytes
        """
        generator = PDFGenerator(
            title=title,
            author=author or self.default_author,
            style=style or self.pdf_style,
        )

        # Add standard metadata
        full_metadata = {
            "Generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        if author or self.default_author:
            full_metadata["Author"] = author or self.default_author
        if metadata:
            full_metadata.update(metadata)

        return generator.generate_from_markdown(content, full_metadata)

    async def to_excel(
        self,
        sheets: (
            DataFrameLike
            | list[dict]
            | list[list]
            | dict[str, DataFrameLike | list[dict] | list[list]]
        ),
        title: str = "Export",
        metadata: dict[str, Any] | None = None,
        style: ExcelStyle | None = None,
        author: str | None = None,
    ) -> bytes:
        """
        Generate Excel from data.

        Args:
            sheets: Data to export (single dataset or dict of sheet name -> data)
            title: Workbook title
            metadata: Workbook metadata
            style: Excel style
            author: Workbook author

        Returns:
            Excel bytes
        """
        generator = ExcelGenerator(
            title=title,
            author=author or self.default_author,
            style=style or self.excel_style,
        )

        # Handle single dataset
        if not isinstance(sheets, dict) or not all(
            isinstance(k, str) for k in sheets.keys()
        ):
            sheets = {"Sheet1": sheets}

        # Check if values are sheet data vs single dict
        first_value = next(iter(sheets.values()), None)
        if isinstance(first_value, (list, tuple)) or hasattr(first_value, "iterrows"):
            pass  # It's sheet data
        else:
            # Single dict, wrap it
            sheets = {"Sheet1": sheets}

        return generator.generate(sheets=sheets, metadata=metadata)

    def to_csv(
        self,
        data: DataFrameLike | list[dict] | list[list],
        encoding: str = "utf-8-sig",
        delimiter: str = ",",
        brazilian_format: bool = False,
    ) -> bytes:
        """
        Generate CSV from data.

        Args:
            data: Data to export
            encoding: Output encoding
            delimiter: Field delimiter
            brazilian_format: Use Brazilian format (; delimiter, , decimal)

        Returns:
            CSV bytes
        """
        if brazilian_format:
            from .csv import BR_CSV_EXPORTER

            return BR_CSV_EXPORTER.export(data)

        return generate_csv(
            data=data,
            encoding=encoding,
            delimiter=delimiter,
        )

    async def to_zip(
        self,
        files: list[dict[str, str | bytes]],
        compression: int = zipfile.ZIP_DEFLATED,
    ) -> bytes:
        """
        Create ZIP archive from multiple files.

        Args:
            files: List of {"filename": str, "content": bytes}
            compression: ZIP compression method

        Returns:
            ZIP bytes

        Example:
            zip_bytes = await export.to_zip([
                {"filename": "report.pdf", "content": pdf_bytes},
                {"filename": "data.xlsx", "content": excel_bytes},
                {"filename": "summary.txt", "content": b"Summary text"},
            ])
        """
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w", compression) as zf:
            for file_info in files:
                filename = file_info["filename"]
                content = file_info["content"]

                if isinstance(content, str):
                    content = content.encode("utf-8")

                zf.writestr(filename, content)

        buffer.seek(0)
        return buffer.read()

    async def to_multiple_formats(
        self,
        data: DataFrameLike | list[dict] | list[list],
        title: str = "Export",
        formats: list[str] | None = None,
        pdf_content: str | None = None,
    ) -> dict[str, bytes]:
        """
        Export data to multiple formats.

        Args:
            data: Data to export
            title: Document title
            formats: List of formats ("xlsx", "csv", "pdf")
            pdf_content: Markdown content for PDF (required if "pdf" in formats)

        Returns:
            Dict mapping format to bytes

        Example:
            results = await export.to_multiple_formats(
                data=sales_data,
                title="Sales Report",
                formats=["xlsx", "csv", "pdf"],
                pdf_content="# Sales Report\\n\\nMonthly summary...",
            )
            # results["xlsx"], results["csv"], results["pdf"]
        """
        if formats is None:
            formats = ["xlsx", "csv"]

        results = {}

        for fmt in formats:
            fmt = fmt.lower().strip(".")

            if fmt in ("xlsx", "excel"):
                results["xlsx"] = await self.to_excel(
                    sheets=data,
                    title=title,
                )
            elif fmt == "csv":
                results["csv"] = self.to_csv(data)
            elif fmt == "pdf":
                if not pdf_content:
                    raise ValueError("pdf_content is required for PDF export")
                results["pdf"] = await self.to_pdf(
                    title=title,
                    content=pdf_content,
                )

        return results

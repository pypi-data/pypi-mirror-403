"""
NTLabs Export - Document export utilities.

This module provides document export functionality:
- PDF generation from markdown
- Excel generation from data
- CSV generation
- ZIP archives

Quick Start:
    from ntlabs.export import ExportService, PDFStyle, ExcelStyle

    export = ExportService()

    # PDF from markdown
    pdf_bytes = await export.to_pdf(
        title="Investigation Report",
        content="# Summary\\n\\nFindings...",
        style=PDFStyle.INVESTIGATION,
    )

    # Excel from data
    excel_bytes = await export.to_excel(
        sheets={
            "Summary": summary_data,
            "Details": details_data,
        },
        title="Financial Report",
        style=ExcelStyle.FINANCIAL,
    )

    # CSV
    csv_bytes = export.to_csv(data, brazilian_format=True)

    # ZIP multiple files
    zip_bytes = await export.to_zip([
        {"filename": "report.pdf", "content": pdf_bytes},
        {"filename": "data.xlsx", "content": excel_bytes},
    ])

Low-level APIs:
    from ntlabs.export import PDFGenerator, ExcelGenerator, generate_csv

    # Direct PDF generation
    generator = PDFGenerator(title="Report", style=PDFStyle.REPORT)
    pdf_bytes = generator.generate_from_markdown(content)

    # Direct Excel generation
    generator = ExcelGenerator(title="Data", style=ExcelStyle.DEFAULT)
    excel_bytes = generator.generate(sheets={"Sheet1": data})

    # Direct CSV generation
    csv_bytes = generate_csv(data, delimiter=";")
"""

from .csv import (
    BR_CSV_EXPORTER,
    US_CSV_EXPORTER,
    CSVExporter,
    generate_csv,
    generate_csv_string,
)
from .excel import ExcelGenerator, generate_excel
from .pdf import PDFGenerator, generate_pdf
from .service import ExportService
from .styles import (
    COLORS,
    Color,
    ExcelStyle,
    ExcelTheme,
    PDFStyle,
    PDFTheme,
    get_excel_theme,
    get_pdf_theme,
)

__all__ = [
    # Main service
    "ExportService",
    # Styles
    "PDFStyle",
    "ExcelStyle",
    "PDFTheme",
    "ExcelTheme",
    "Color",
    "COLORS",
    "get_pdf_theme",
    "get_excel_theme",
    # PDF
    "PDFGenerator",
    "generate_pdf",
    # Excel
    "ExcelGenerator",
    "generate_excel",
    # CSV
    "generate_csv",
    "generate_csv_string",
    "CSVExporter",
    "BR_CSV_EXPORTER",
    "US_CSV_EXPORTER",
]

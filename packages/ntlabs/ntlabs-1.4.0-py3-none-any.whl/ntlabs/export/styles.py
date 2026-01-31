"""
Export styles and themes.

Provides consistent styling for PDF and Excel exports.
"""

from dataclasses import dataclass, field
from enum import Enum


class PDFStyle(Enum):
    """Pre-defined PDF styles."""

    REPORT = "report"
    INVESTIGATION = "investigation"
    MEDICAL = "medical"
    INVOICE = "invoice"
    SIMPLE = "simple"


class ExcelStyle(Enum):
    """Pre-defined Excel styles."""

    DEFAULT = "default"
    FINANCIAL = "financial"
    MEDICAL = "medical"
    DASHBOARD = "dashboard"


@dataclass
class Color:
    """RGB color."""

    r: int
    g: int
    b: int

    def to_tuple(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    @classmethod
    def from_hex(cls, hex_color: str) -> "Color":
        hex_color = hex_color.lstrip("#")
        return cls(
            r=int(hex_color[0:2], 16),
            g=int(hex_color[2:4], 16),
            b=int(hex_color[4:6], 16),
        )


# Common colors
COLORS = {
    "primary": Color(0, 123, 255),  # Blue
    "secondary": Color(108, 117, 125),  # Gray
    "success": Color(40, 167, 69),  # Green
    "danger": Color(220, 53, 69),  # Red
    "warning": Color(255, 193, 7),  # Yellow
    "info": Color(23, 162, 184),  # Cyan
    "white": Color(255, 255, 255),
    "black": Color(0, 0, 0),
    "gray_100": Color(248, 249, 250),
    "gray_200": Color(233, 236, 239),
    "gray_500": Color(173, 181, 189),
    "gray_800": Color(52, 58, 64),
}


@dataclass
class PDFTheme:
    """PDF theme configuration."""

    # Colors
    primary_color: Color = field(default_factory=lambda: COLORS["primary"])
    secondary_color: Color = field(default_factory=lambda: COLORS["secondary"])
    text_color: Color = field(default_factory=lambda: COLORS["black"])
    header_bg_color: Color = field(default_factory=lambda: COLORS["gray_100"])
    accent_color: Color = field(default_factory=lambda: COLORS["info"])

    # Fonts
    font_family: str = "Helvetica"
    font_size_title: int = 24
    font_size_heading: int = 16
    font_size_subheading: int = 14
    font_size_body: int = 10
    font_size_small: int = 8

    # Spacing
    margin_top: float = 72  # 1 inch
    margin_bottom: float = 72
    margin_left: float = 72
    margin_right: float = 72
    line_spacing: float = 1.2

    # Header/Footer
    show_header: bool = True
    show_footer: bool = True
    show_page_numbers: bool = True

    # Logo
    logo_path: str | None = None
    logo_width: float = 100


# Pre-defined themes
PDF_THEMES: dict[PDFStyle, PDFTheme] = {
    PDFStyle.REPORT: PDFTheme(
        primary_color=COLORS["primary"],
        show_header=True,
        show_footer=True,
    ),
    PDFStyle.INVESTIGATION: PDFTheme(
        primary_color=Color.from_hex("#1a365d"),  # Dark blue
        accent_color=Color.from_hex("#c53030"),  # Alert red
        font_size_body=11,
    ),
    PDFStyle.MEDICAL: PDFTheme(
        primary_color=Color.from_hex("#2c7a7b"),  # Teal
        secondary_color=Color.from_hex("#285e61"),
        font_family="Helvetica",
    ),
    PDFStyle.INVOICE: PDFTheme(
        primary_color=Color.from_hex("#2d3748"),
        show_header=True,
        show_footer=True,
        margin_top=50,
    ),
    PDFStyle.SIMPLE: PDFTheme(
        show_header=False,
        show_footer=False,
        margin_top=50,
        margin_bottom=50,
    ),
}


@dataclass
class ExcelTheme:
    """Excel theme configuration."""

    # Colors (as hex strings for openpyxl)
    header_fill: str = "4472C4"
    header_font: str = "FFFFFF"
    alternating_row: str = "D9E2F3"
    border_color: str = "B4B4B4"

    # Fonts
    header_font_name: str = "Calibri"
    header_font_size: int = 11
    header_bold: bool = True
    body_font_name: str = "Calibri"
    body_font_size: int = 10

    # Column widths
    default_width: float = 15
    auto_width: bool = True

    # Freeze panes
    freeze_header: bool = True

    # Number formats
    currency_format: str = "R$ #,##0.00"
    date_format: str = "DD/MM/YYYY"
    datetime_format: str = "DD/MM/YYYY HH:MM"
    percentage_format: str = "0.00%"


# Pre-defined Excel themes
EXCEL_THEMES: dict[ExcelStyle, ExcelTheme] = {
    ExcelStyle.DEFAULT: ExcelTheme(),
    ExcelStyle.FINANCIAL: ExcelTheme(
        header_fill="1F4E79",
        alternating_row="DEEBF7",
        currency_format="R$ #,##0.00",
    ),
    ExcelStyle.MEDICAL: ExcelTheme(
        header_fill="2C7A7B",
        alternating_row="E6FFFA",
    ),
    ExcelStyle.DASHBOARD: ExcelTheme(
        header_fill="2D3748",
        header_font="FFFFFF",
        alternating_row="F7FAFC",
        header_bold=True,
    ),
}


def get_pdf_theme(style: PDFStyle) -> PDFTheme:
    """Get PDF theme for style."""
    return PDF_THEMES.get(style, PDF_THEMES[PDFStyle.REPORT])


def get_excel_theme(style: ExcelStyle) -> ExcelTheme:
    """Get Excel theme for style."""
    return EXCEL_THEMES.get(style, EXCEL_THEMES[ExcelStyle.DEFAULT])

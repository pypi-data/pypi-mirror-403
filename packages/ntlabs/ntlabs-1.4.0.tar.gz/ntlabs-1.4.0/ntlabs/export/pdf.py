"""
PDF generation utilities.

Provides PDF generation using ReportLab.
"""

import io
import logging
from typing import Any

from .styles import PDFStyle, PDFTheme, get_pdf_theme

logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    PDF document generator.

    Example:
        generator = PDFGenerator(
            title="Investigation Report",
            author="Sistema Argos",
            style=PDFStyle.INVESTIGATION,
        )

        pdf_bytes = generator.generate_from_markdown(
            content="# Report\\n\\nContent here...",
            metadata={"date": "2026-01-27"}
        )
    """

    def __init__(
        self,
        title: str = "Document",
        author: str | None = None,
        style: PDFStyle = PDFStyle.REPORT,
        theme: PDFTheme | None = None,
    ):
        """
        Initialize PDF generator.

        Args:
            title: Document title
            author: Document author
            style: Pre-defined style
            theme: Custom theme (overrides style)
        """
        self.title = title
        self.author = author
        self.theme = theme or get_pdf_theme(style)

    def generate_from_markdown(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> bytes:
        """
        Generate PDF from markdown content.

        Args:
            content: Markdown content
            metadata: Document metadata

        Returns:
            PDF bytes
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
            )
        except ImportError as err:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install it with: pip install reportlab"
            ) from err

        buffer = io.BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=self.theme.margin_top,
            bottomMargin=self.theme.margin_bottom,
            leftMargin=self.theme.margin_left,
            rightMargin=self.theme.margin_right,
        )

        # Get styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=self.theme.font_size_title,
            textColor=colors.Color(
                *[c / 255 for c in self.theme.primary_color.to_tuple()]
            ),
            spaceAfter=20,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=self.theme.font_size_heading,
            textColor=colors.Color(
                *[c / 255 for c in self.theme.primary_color.to_tuple()]
            ),
            spaceBefore=15,
            spaceAfter=10,
        )

        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["Normal"],
            fontSize=self.theme.font_size_body,
            leading=self.theme.font_size_body * self.theme.line_spacing,
            alignment=TA_JUSTIFY,
        )

        # Build content
        story = []

        # Title
        story.append(Paragraph(self.title, title_style))

        # Metadata
        if metadata:
            meta_text = " | ".join(f"<b>{k}:</b> {v}" for k, v in metadata.items())
            story.append(Paragraph(meta_text, styles["Normal"]))

        story.append(Spacer(1, 20))

        # Parse markdown content
        elements = self._parse_markdown(content, heading_style, body_style, styles)
        story.extend(elements)

        # Build PDF
        doc.build(
            story,
            onFirstPage=self._header_footer,
            onLaterPages=self._header_footer,
        )

        buffer.seek(0)
        return buffer.read()

    def _parse_markdown(
        self,
        content: str,
        heading_style,
        body_style,
        styles,
    ) -> list[Any]:
        """Parse markdown into ReportLab elements."""
        from reportlab.platypus import Paragraph, Spacer

        elements = []
        lines = content.split("\n")
        current_list = []
        in_list = False

        for line in lines:
            line = line.strip()

            if not line:
                if in_list and current_list:
                    # End list
                    for item in current_list:
                        elements.append(Paragraph(f"• {item}", body_style))
                    current_list = []
                    in_list = False
                elements.append(Spacer(1, 10))
                continue

            # Headers
            if line.startswith("### "):
                elements.append(Paragraph(line[4:], styles["Heading3"]))
            elif line.startswith("## "):
                elements.append(Paragraph(line[3:], heading_style))
            elif line.startswith("# "):
                elements.append(Paragraph(line[2:], heading_style))
            # List items
            elif line.startswith("- ") or line.startswith("* "):
                in_list = True
                current_list.append(self._format_text(line[2:]))
            # Regular text
            else:
                elements.append(Paragraph(self._format_text(line), body_style))

        return elements

    def _format_text(self, text: str) -> str:
        """Convert markdown formatting to ReportLab XML."""
        import re

        # Bold
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

        # Italic
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
        text = re.sub(r"_(.+?)_", r"<i>\1</i>", text)

        # Code
        text = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', text)

        return text

    def _header_footer(self, canvas, doc):
        """Draw header and footer on page."""

        canvas.saveState()

        if self.theme.show_header:
            # Header line
            canvas.setStrokeColor(
                [c / 255 for c in self.theme.primary_color.to_tuple()]
            )
            canvas.setLineWidth(1)
            canvas.line(
                doc.leftMargin,
                doc.height + doc.topMargin - 20,
                doc.width + doc.leftMargin,
                doc.height + doc.topMargin - 20,
            )

        if self.theme.show_footer:
            # Footer
            canvas.setFont(self.theme.font_family, self.theme.font_size_small)
            canvas.setFillColor(
                [c / 255 for c in self.theme.secondary_color.to_tuple()]
            )

            footer_y = doc.bottomMargin - 30

            # Date
            if self.author:
                canvas.drawString(
                    doc.leftMargin, footer_y, f"Generated by {self.author}"
                )

            # Page number
            if self.theme.show_page_numbers:
                page_num = canvas.getPageNumber()
                canvas.drawRightString(
                    doc.width + doc.leftMargin, footer_y, f"Page {page_num}"
                )

        canvas.restoreState()

    def generate_simple(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> bytes:
        """
        Generate simple text PDF.

        Args:
            content: Plain text content
            metadata: Document metadata

        Returns:
            PDF bytes
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas as pdf_canvas
        except ImportError as err:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install it with: pip install reportlab"
            ) from err

        buffer = io.BytesIO()
        c = pdf_canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Set font
        c.setFont(self.theme.font_family, self.theme.font_size_body)

        # Title
        c.setFont(self.theme.font_family, self.theme.font_size_title)
        c.drawCentredString(width / 2, height - self.theme.margin_top, self.title)

        # Content
        c.setFont(self.theme.font_family, self.theme.font_size_body)
        y = height - self.theme.margin_top - 50

        for line in content.split("\n"):
            if y < self.theme.margin_bottom:
                c.showPage()
                c.setFont(self.theme.font_family, self.theme.font_size_body)
                y = height - self.theme.margin_top

            c.drawString(self.theme.margin_left, y, line)
            y -= self.theme.font_size_body * self.theme.line_spacing

        c.save()
        buffer.seek(0)
        return buffer.read()


async def generate_pdf(
    title: str,
    content: str,
    metadata: dict[str, Any] | None = None,
    style: PDFStyle = PDFStyle.REPORT,
    author: str | None = None,
) -> bytes:
    """
    Generate PDF from markdown content.

    Convenience function for quick PDF generation.

    Args:
        title: Document title
        content: Markdown content
        metadata: Document metadata
        style: PDF style
        author: Document author

    Returns:
        PDF bytes
    """
    generator = PDFGenerator(
        title=title,
        author=author,
        style=style,
    )
    return generator.generate_from_markdown(content, metadata)

"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for PDF export module
Version: 1.0.0
"""

from unittest.mock import MagicMock, patch

import pytest

from ntlabs.export.pdf import PDFGenerator, generate_pdf
from ntlabs.export.styles import PDFStyle


class TestPDFGeneratorInit:
    """Test PDFGenerator initialization."""

    def test_default_init(self):
        """Test initialization with default values."""
        generator = PDFGenerator()
        assert generator.title == "Document"
        assert generator.author is None
        assert generator.theme is not None

    def test_custom_init(self):
        """Test initialization with custom values."""
        generator = PDFGenerator(
            title="Test Report",
            author="Test Author",
            style=PDFStyle.INVESTIGATION,
        )
        assert generator.title == "Test Report"
        assert generator.author == "Test Author"


class TestPDFGeneratorMarkdown:
    """Test PDF generation from markdown."""

    @pytest.fixture
    def generator(self):
        """Create a PDF generator."""
        return PDFGenerator(
            title="Test Document",
            author="Test Author",
        )

    def test_generate_from_markdown_basic(self, generator):
        """Test basic markdown to PDF generation."""
        with patch("reportlab.platypus.SimpleDocTemplate") as mock_doc:
            mock_instance = MagicMock()
            mock_doc.return_value = mock_instance

            pdf_bytes = generator.generate_from_markdown("# Hello World")

            assert isinstance(pdf_bytes, bytes)
            mock_instance.build.assert_called_once()

    def test_generate_from_markdown_with_metadata(self, generator):
        """Test PDF generation with metadata."""
        with patch("reportlab.platypus.SimpleDocTemplate") as mock_doc:
            mock_instance = MagicMock()
            mock_doc.return_value = mock_instance

            pdf_bytes = generator.generate_from_markdown(
                "# Content",
                metadata={"date": "2026-01-28", "author": "Test"},
            )

            assert isinstance(pdf_bytes, bytes)

    def test_generate_from_markdown_with_headers(self, generator):
        """Test PDF generation with markdown headers."""
        content = """
# Title
## Subtitle
### Section
"""
        with patch("reportlab.platypus.SimpleDocTemplate") as mock_doc:
            mock_instance = MagicMock()
            mock_doc.return_value = mock_instance

            pdf_bytes = generator.generate_from_markdown(content)
            assert isinstance(pdf_bytes, bytes)

    def test_generate_from_markdown_with_list(self, generator):
        """Test PDF generation with markdown lists."""
        content = """
# Items
- Item 1
- Item 2
- Item 3
"""
        with patch("reportlab.platypus.SimpleDocTemplate") as mock_doc:
            mock_instance = MagicMock()
            mock_doc.return_value = mock_instance

            pdf_bytes = generator.generate_from_markdown(content)
            assert isinstance(pdf_bytes, bytes)

    def test_generate_from_markdown_with_bold_text(self, generator):
        """Test PDF generation with bold text."""
        content = "This is **bold** text"

        with patch("reportlab.platypus.SimpleDocTemplate") as mock_doc:
            mock_instance = MagicMock()
            mock_doc.return_value = mock_instance

            pdf_bytes = generator.generate_from_markdown(content)
            assert isinstance(pdf_bytes, bytes)

    def test_generate_from_markdown_with_italic_text(self, generator):
        """Test PDF generation with italic text."""
        content = "This is *italic* text"

        with patch("reportlab.platypus.SimpleDocTemplate") as mock_doc:
            mock_instance = MagicMock()
            mock_doc.return_value = mock_instance

            pdf_bytes = generator.generate_from_markdown(content)
            assert isinstance(pdf_bytes, bytes)

    def test_generate_from_markdown_with_code(self, generator):
        """Test PDF generation with inline code."""
        content = "Use `print()` function"

        with patch("reportlab.platypus.SimpleDocTemplate") as mock_doc:
            mock_instance = MagicMock()
            mock_doc.return_value = mock_instance

            pdf_bytes = generator.generate_from_markdown(content)
            assert isinstance(pdf_bytes, bytes)

    def test_import_error(self, generator):
        """Test handling of missing reportlab."""
        with patch.dict("sys.modules", {"reportlib": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'reportlab'")):
                with pytest.raises(ImportError):
                    generator.generate_from_markdown("# Test")


class TestPDFGeneratorFormatText:
    """Test text formatting."""

    @pytest.fixture
    def generator(self):
        """Create a PDF generator."""
        return PDFGenerator()

    def test_format_bold(self, generator):
        """Test bold text formatting."""
        result = generator._format_text("**bold text**")
        assert "<b>bold text</b>" in result

    def test_format_bold_underscore(self, generator):
        """Test bold text with underscores."""
        result = generator._format_text("__bold text__")
        assert "<b>bold text</b>" in result

    def test_format_italic(self, generator):
        """Test italic text formatting."""
        result = generator._format_text("*italic text*")
        assert "<i>italic text</i>" in result

    def test_format_italic_underscore(self, generator):
        """Test italic text with underscores."""
        result = generator._format_text("_italic text_")
        assert "<i>italic text</i>" in result

    def test_format_code(self, generator):
        """Test inline code formatting."""
        result = generator._format_text("`code snippet`")
        assert "<font name=\"Courier\">code snippet</font>" in result

    def test_format_combined(self, generator):
        """Test combined formatting."""
        result = generator._format_text("**bold** and *italic* and `code`")
        assert "<b>bold</b>" in result
        assert "<i>italic</i>" in result
        assert "<font name=\"Courier\">code</font>" in result


class TestPDFGeneratorHeaderFooter:
    """Test header and footer drawing."""

    @pytest.fixture
    def generator(self):
        """Create a PDF generator."""
        return PDFGenerator(
            title="Test",
            author="Test Author",
        )

    def test_header_footer_with_header_enabled(self, generator):
        """Test header/footer with show_header enabled."""
        mock_canvas = MagicMock()
        mock_doc = MagicMock()
        mock_doc.leftMargin = 72
        mock_doc.width = 468
        mock_doc.height = 648
        mock_doc.topMargin = 72
        mock_doc.bottomMargin = 72

        generator.theme.show_header = True
        generator.theme.show_footer = True
        generator.theme.show_page_numbers = True

        generator._header_footer(mock_canvas, mock_doc)

        mock_canvas.saveState.assert_called_once()
        mock_canvas.restoreState.assert_called_once()

    def test_header_footer_without_author(self, generator):
        """Test footer without author."""
        generator.author = None

        mock_canvas = MagicMock()
        mock_doc = MagicMock()
        mock_doc.leftMargin = 72
        mock_doc.width = 468
        mock_doc.height = 648
        mock_doc.topMargin = 72
        mock_doc.bottomMargin = 72

        generator.theme.show_footer = True
        generator.theme.show_page_numbers = False

        generator._header_footer(mock_canvas, mock_doc)

        # drawString should not be called for author
        mock_canvas.drawString.assert_not_called()

    def test_header_footer_disabled(self, generator):
        """Test when header and footer are disabled."""
        mock_canvas = MagicMock()
        mock_doc = MagicMock()

        generator.theme.show_header = False
        generator.theme.show_footer = False

        generator._header_footer(mock_canvas, mock_doc)

        mock_canvas.saveState.assert_called_once()
        mock_canvas.restoreState.assert_called_once()


class TestPDFGeneratorSimple:
    """Test simple PDF generation."""

    @pytest.fixture
    def generator(self):
        """Create a PDF generator."""
        return PDFGenerator(
            title="Test Document",
            author="Test Author",
        )

    def test_generate_simple(self, generator):
        """Test simple PDF generation."""
        with patch("reportlab.pdfgen.canvas.Canvas") as mock_canvas:
            mock_instance = MagicMock()
            mock_canvas.return_value = mock_instance

            pdf_bytes = generator.generate_simple("Line 1\nLine 2\nLine 3")

            assert isinstance(pdf_bytes, bytes)
            mock_instance.save.assert_called_once()

    def test_generate_simple_with_page_break(self, generator):
        """Test simple PDF with page break."""
        # Create enough content to trigger page break
        content = "\n".join([f"Line {i}" for i in range(100)])

        with patch("reportlab.pdfgen.canvas.Canvas") as mock_canvas:
            mock_instance = MagicMock()
            mock_canvas.return_value = mock_instance

            pdf_bytes = generator.generate_simple(content)

            assert isinstance(pdf_bytes, bytes)
            mock_instance.save.assert_called_once()

    def test_generate_simple_import_error(self, generator):
        """Test handling missing reportlab in simple generation."""
        with patch.dict("sys.modules", {"reportlib": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'reportlab'")):
                with pytest.raises(ImportError):
                    generator.generate_simple("Test")


class TestGeneratePDFFunction:
    """Test the generate_pdf convenience function."""

    @pytest.mark.asyncio
    async def test_generate_pdf_function(self):
        """Test the async generate_pdf function."""
        with patch("ntlabs.export.pdf.PDFGenerator") as mock_gen:
            mock_instance = MagicMock()
            mock_instance.generate_from_markdown.return_value = b"PDF bytes"
            mock_gen.return_value = mock_instance

            result = await generate_pdf(
                title="Test",
                content="# Hello",
                metadata={"date": "2026-01-28"},
                style=PDFStyle.REPORT,
                author="Test Author",
            )

            assert result == b"PDF bytes"
            mock_gen.assert_called_once_with(
                title="Test",
                author="Test Author",
                style=PDFStyle.REPORT,
            )
            mock_instance.generate_from_markdown.assert_called_once_with(
                "# Hello",
                {"date": "2026-01-28"},
            )


class TestPDFGeneratorParseMarkdown:
    """Test markdown parsing."""

    @pytest.fixture
    def generator(self):
        """Create a PDF generator."""
        return PDFGenerator()

    @pytest.fixture
    def mock_styles(self):
        """Create properly configured mock styles."""
        from reportlab.lib.styles import ParagraphStyle
        return {
            "Heading1": ParagraphStyle("Heading1"),
            "Heading2": ParagraphStyle("Heading2"),
            "Heading3": ParagraphStyle("Heading3"),
            "Normal": ParagraphStyle("Normal"),
        }

    @pytest.fixture
    def mock_heading_style(self):
        """Create properly configured heading style."""
        from reportlab.lib.styles import ParagraphStyle
        return ParagraphStyle("CustomHeading")

    @pytest.fixture
    def mock_body_style(self):
        """Create properly configured body style."""
        from reportlab.lib.styles import ParagraphStyle
        return ParagraphStyle("CustomBody")

    def test_parse_empty_lines(self, generator, mock_styles, mock_heading_style, mock_body_style):
        """Test parsing content with empty lines."""
        content = "Line 1\n\nLine 2"

        elements = generator._parse_markdown(
            content,
            mock_heading_style,
            mock_body_style,
            mock_styles,
        )

        # Should have Spacer elements for empty lines
        assert len(elements) > 0

    def test_parse_headers(self, generator, mock_styles, mock_heading_style, mock_body_style):
        """Test parsing markdown headers."""
        content = """
# Header 1
## Header 2
### Header 3
"""
        elements = generator._parse_markdown(
            content,
            mock_heading_style,
            mock_body_style,
            mock_styles,
        )

        assert len(elements) > 0

    def test_parse_list_items(self, generator, mock_styles, mock_heading_style, mock_body_style):
        """Test parsing list items."""
        content = """
- Item 1
- Item 2
* Item 3
"""
        elements = generator._parse_markdown(
            content,
            mock_heading_style,
            mock_body_style,
            mock_styles,
        )

        assert len(elements) > 0

    def test_end_list_on_empty_line(self, generator, mock_styles, mock_heading_style, mock_body_style):
        """Test that list ends on empty line."""
        content = """
- Item 1
- Item 2

Regular text
"""
        elements = generator._parse_markdown(
            content,
            mock_heading_style,
            mock_body_style,
            mock_styles,
        )

        assert len(elements) > 0

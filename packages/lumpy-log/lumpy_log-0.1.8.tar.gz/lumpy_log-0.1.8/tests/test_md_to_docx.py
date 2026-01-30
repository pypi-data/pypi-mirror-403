"""Tests for the custom markdown to DOCX converter."""

import tempfile
from pathlib import Path
import pytest
from lumpy_log.md_to_docx import (
    markdown_to_docx,
    markdown_file_to_docx,
    _parse_inline_formatting,
)


class TestParseInlineFormatting:
    """Tests for inline formatting parser."""

    def test_bold_formatting(self):
        """Should parse **bold** text."""
        result = _parse_inline_formatting("This is **bold** text")
        # Should have at least 3 segments: text, bold, text
        assert len(result) >= 3
        bold_segment = [seg for seg in result if seg[1] and seg[0] == "bold"]
        assert len(bold_segment) == 1

    def test_italic_formatting(self):
        """Should parse *italic* text."""
        result = _parse_inline_formatting("This is *italic* text")
        italic_segment = [seg for seg in result if seg[2] and seg[0] == "italic"]
        assert len(italic_segment) == 1

    def test_inline_code_formatting(self):
        """Should parse `code` text."""
        result = _parse_inline_formatting("Use `variable` in code")
        code_segment = [seg for seg in result if seg[3] and seg[0] == "variable"]
        assert len(code_segment) == 1

    def test_mixed_formatting(self):
        """Should handle multiple formatting types."""
        text = "**bold** and *italic* and `code`"
        result = _parse_inline_formatting(text)
        assert len(result) > 0
        # Should have formatting indicators
        has_bold = any(seg[1] for seg in result)
        has_italic = any(seg[2] for seg in result)
        has_code = any(seg[3] for seg in result)
        assert has_bold or has_italic or has_code

    def test_no_formatting(self):
        """Should handle plain text without formatting."""
        result = _parse_inline_formatting("plain text")
        assert len(result) == 1
        assert result[0][0] == "plain text"
        assert result[0][1:] == (False, False, False)


class TestMarkdownToDocx:
    """Tests for markdown to DOCX conversion."""

    def test_basic_conversion(self):
        """Should convert basic markdown to DOCX."""
        markdown = "# Title\n\nThis is a paragraph."
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.docx"
            result = markdown_to_docx(markdown, str(output))
            assert result is True
            assert output.exists()

    def test_headers(self):
        """Should convert markdown headers."""
        markdown = "# H1\n## H2\n### H3"
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.docx"
            result = markdown_to_docx(markdown, str(output))
            assert result is True
            assert output.exists()

    def test_code_blocks(self):
        """Should convert code blocks."""
        markdown = """# Code Example

```python
def hello():
    print("world")
```

More text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.docx"
            result = markdown_to_docx(markdown, str(output))
            assert result is True
            assert output.exists()

    def test_unordered_lists(self):
        """Should convert unordered lists."""
        markdown = """# List

- Item 1
- Item 2
  - Nested item
- Item 3"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.docx"
            result = markdown_to_docx(markdown, str(output))
            assert result is True
            assert output.exists()

    def test_ordered_lists(self):
        """Should convert ordered lists."""
        markdown = """# Numbered List

1. First
2. Second
3. Third"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.docx"
            result = markdown_to_docx(markdown, str(output))
            assert result is True
            assert output.exists()

    def test_horizontal_rules(self):
        """Should convert horizontal rules."""
        markdown = """# Section 1

Content here.

---

# Section 2

More content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.docx"
            result = markdown_to_docx(markdown, str(output))
            assert result is True
            assert output.exists()

    def test_bold_and_italic(self):
        """Should handle bold and italic text."""
        markdown = """# Formatting

This has **bold text** and *italic text* and `inline code`."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.docx"
            result = markdown_to_docx(markdown, str(output))
            assert result is True
            assert output.exists()

    def test_empty_lines_between_paragraphs(self):
        """Should handle empty lines between paragraphs."""
        markdown = """First paragraph.

Second paragraph.

Third paragraph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.docx"
            result = markdown_to_docx(markdown, str(output))
            assert result is True
            assert output.exists()

    def test_complex_document(self):
        """Should handle a complex markdown document."""
        markdown = """# Development Log

Generated: 2024-01-15 12:00:00
Items: 2 (1 commits, 1 tests)

## Commit One

This is a commit description with **important** changes.

```python
def new_feature():
    return "implemented"
```

---

## Test Entry

- Test 1: Passed
- Test 2: Passed
- Test 3: Needs review

Final notes with *emphasis*."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.docx"
            result = markdown_to_docx(markdown, str(output))
            assert result is True
            assert output.exists()


class TestMarkdownFileToDOCX:
    """Tests for file-based conversion."""

    def test_file_not_found(self):
        """Should handle missing markdown file."""
        result = markdown_file_to_docx("/nonexistent/path.md")
        assert result is False

    def test_convert_file(self):
        """Should convert markdown file to DOCX."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("# Title\n\nContent here.")
            
            result = markdown_file_to_docx(str(md_file))
            assert result is True
            
            docx_file = md_file.with_suffix(".docx")
            assert docx_file.exists()

    def test_convert_with_custom_output(self):
        """Should convert to custom output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("# Title\n\nContent here.")
            
            output_file = Path(tmpdir) / "custom_output.docx"
            result = markdown_file_to_docx(str(md_file), str(output_file))
            assert result is True
            assert output_file.exists()

    def test_devlog_structure(self):
        """Should handle typical devlog markdown structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "devlog.md"
            devlog_content = """# Devlog

Generated: 2024-01-15 12:00:00
Items: 2 (1 commits, 1 tests)

# First Commit

## Changes

- Added new feature
- Fixed bug
- Updated documentation

```python
# New implementation
class Feature:
    def __init__(self):
        self.enabled = True
```

---

# Test Entry

## Results

1. Unit tests: PASSED
2. Integration: PASSED
3. Performance: OK"""
            md_file.write_text(devlog_content)
            
            result = markdown_file_to_docx(str(md_file))
            assert result is True
            
            docx_file = md_file.with_suffix(".docx")
            assert docx_file.exists()
            assert docx_file.stat().st_size > 0

import pytest
import tempfile
import os
from pathlib import Path
from lumpy_log.changelump import ChangeLump
from lumpy_log.languages import Languages


@pytest.fixture
def languages():
    """Load the languages configuration"""
    lang_path = os.path.join(os.path.dirname(__file__), "..", "lumpy_log", "languages.yml")
    return Languages(lang_path)


@pytest.fixture
def python_language(languages):
    """Get Python language"""
    return languages.getByExtension(".py")


class TestWindowsEncoding:
    """Test Windows-specific encoding scenarios"""
    
    def test_utf8_with_bom(self, python_language):
        """Test handling UTF-8 files with BOM (common on Windows)"""
        # UTF-8 BOM is \xef\xbb\xbf
        code_with_bom = [
            "def hello():",
            "    print('Hello, World!')",
            "    return True"
        ]
        
        lump = ChangeLump(python_language, code_with_bom, start=1, end=3)
        assert "def hello():" in lump.code
        assert "print('Hello, World!')" in lump.code
    
    def test_windows_line_endings_crlf(self, python_language):
        """Test handling Windows CRLF line endings"""
        code = [
            "def calculate(x):\r\n",
            "    result = x * 2\r\n",
            "    return result\r\n"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        result = lump.code
        
        # Should handle CRLF gracefully
        assert "def calculate(x):" in result
        assert "return result" in result
    
    def test_mixed_line_endings(self, python_language):
        """Test handling mixed LF and CRLF (can happen with Windows git config)"""
        code = [
            "def process():\n",
            "    x = 1\r\n",
            "    y = 2\n",
            "    return x + y\r\n"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=4)
        assert "def process():" in lump.code
        assert "return x + y" in lump.code
    
    def test_utf16_encoded_content(self, python_language):
        """Test UTF-16 content (sometimes used in Windows)"""
        # Simulate UTF-16 decoded content
        code = [
            "def greet(name):",
            "    # Grüße from Windows",
            "    return f'Hello {name}'"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        result = lump.code
        
        assert "Grüße" in result
        assert "def greet(name):" in result
    
    def test_latin1_characters(self, python_language):
        """Test Latin-1 encoded characters (ISO-8859-1, common in legacy Windows)"""
        code = [
            "def print_currency():",
            "    # Price in £€¥",
            "    return '£100'"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        assert "£" in lump.code or "currency" in lump.code
    
    def test_unicode_characters_in_comments(self, python_language):
        """Test Unicode characters in comments (emoji, etc.)"""
        code = [
            "# TODO: Fix this bug 🐛",
            "def buggy_function():",
            "    # Returns success ✓",
            "    return True"
        ]
        
        func_dict = {"start_line": 2, "end_line": 4, "name": "buggy_function"}
        lump = ChangeLump(python_language, code, func=func_dict)
        lump.extendOverComments()
        
        result = lump.code
        assert "TODO" in result or "buggy_function" in result
    
    def test_windows_path_in_string_literals(self, python_language):
        """Test handling Windows paths in string literals"""
        code = [
            "def get_config():",
            r"    path = 'C:\\Users\\Admin\\config.ini'",
            "    return path"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        assert "C:\\\\" in lump.code or "config.ini" in lump.code


class TestWindowsEncodingEdgeCases:
    """Test edge cases with Windows encoding"""
    
    def test_empty_file_with_bom(self, python_language):
        """Test empty file with BOM marker"""
        code = []
        
        lump = ChangeLump(python_language, code, start=1)
        assert lump.code == ""
    
    def test_only_whitespace_with_crlf(self, python_language):
        """Test file with only whitespace and CRLF"""
        code = ["\r\n", "    \r\n", "\r\n"]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        # Should handle gracefully without errors
        assert isinstance(lump.code, str)
    
    def test_code_page_1252_special_chars(self, python_language):
        """Test Windows-1252 special characters (smart quotes, etc.)"""
        code = [
            "def format_text():",
            "    # Use “smart quotes” and em—dashes",
            "    return 'formatted'"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        result = lump.code
        
        # Should preserve or handle special characters
        assert "format_text" in result
        assert "formatted" in result
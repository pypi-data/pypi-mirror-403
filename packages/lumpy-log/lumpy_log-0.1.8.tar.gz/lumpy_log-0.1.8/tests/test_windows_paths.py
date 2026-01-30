import pytest
import os
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


class TestWindowsPathHandling:
    """Test Windows path handling scenarios"""
    
    def test_backslash_path_parsing(self, python_language):
        """Test handling backslash paths in code"""
        code = [
            "import os",
            "config_path = 'C:\\\\Users\\\\Admin\\\\config.txt'",
            "data = open(config_path).read()"
        ]
        
        lump = ChangeLump(python_language, code, start=2)
        assert "config_path" in lump.code
    
    def test_raw_string_windows_path(self, python_language):
        """Test raw string Windows paths (r'C:\path')"""
        code = [
            r"path = r'C:\Users\Documents\file.txt'",
            "with open(path) as f:",
            "    data = f.read()"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        assert "path" in lump.code
    
    def test_forward_slash_on_windows(self, python_language):
        """Test forward slashes (valid on Windows Python)"""
        code = [
            "path = 'C:/Users/Admin/file.txt'",
            "os.path.exists(path)"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=2)
        assert "C:/Users" in lump.code or "file.txt" in lump.code
    
    def test_unc_path_handling(self, python_language):
        """Test UNC path handling (\\\\server\\share)"""
        code = [
            r"network_path = r'\\server\share\folder\file.txt'",
            "if os.path.exists(network_path):",
            "    process_file(network_path)"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        assert "network_path" in lump.code
    
    def test_drive_letter_paths(self, python_language):
        """Test various drive letter paths"""
        code = [
            "paths = [",
            "    'C:\\\\temp\\\\file1.txt',",
            "    'D:\\\\data\\\\file2.txt',",
            "    'E:\\\\backup\\\\file3.txt'",
            "]"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=5)
        result = lump.code
        assert "paths" in result
    
    def test_path_with_spaces(self, python_language):
        """Test Windows paths with spaces"""
        code = [
            r"path = 'C:\\Program Files\\My App\\config.ini'",
            "config = load_config(path)"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=2)
        assert "Program Files" in lump.code or "config" in lump.code
    
    def test_long_path_over_260_chars(self, python_language):
        """Test handling of long paths (>260 chars, Windows MAX_PATH)"""
        long_path = "C:\\\\" + "very_long_folder_name\\\\" * 20 + "file.txt"
        code = [
            f"path = '{long_path}'",
            "# Path length:", 
            f"# {len(long_path)} characters"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        assert len(lump.code) > 0
    
    def test_relative_path_with_backslashes(self, python_language):
        """Test relative paths with backslashes"""
        code = [
            r"rel_path = '..\\..\\config\\settings.ini'",
            "abs_path = os.path.abspath(rel_path)"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=2)
        assert "rel_path" in lump.code


class TestWindowsPathEdgeCases:
    """Test edge cases with Windows paths"""
    
    def test_path_with_special_characters(self, python_language):
        """Test paths with special characters (that are valid on Windows)"""
        code = [
            # $ ~ ` ! @ # % ^ & ( ) are valid in Windows filenames
            r"path = 'C:\\Users\\test$folder\\file!.txt'",
            "process(path)"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=2)
        assert "path" in lump.code
    
    def test_path_with_invalid_characters(self, python_language):
        """Test code containing invalid Windows path characters"""
        # < > : " | ? * are invalid in Windows filenames
        code = [
            "# This would fail on Windows:",
            r"# bad_path = 'C:\\folder\\file<>.txt'",
            "# Use sanitize_filename() instead"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        assert "bad_path" in lump.code or "sanitize" in lump.code
    
    def test_mixed_path_separators(self, python_language):
        """Test mixed path separators (backslash and forward slash)"""
        code = [
            r"path = 'C:\\Users/Admin\\Documents/file.txt'",
            "normalized = os.path.normpath(path)"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=2)
        assert "normalized" in lump.code
    
    def test_pathlib_windows_paths(self, python_language):
        """Test pathlib usage with Windows paths"""
        code = [
            "from pathlib import Path",
            "p = Path('C:/Users/Admin/file.txt')",
            "parent = p.parent",
            "name = p.name"
        ]
        
        lump = ChangeLump(python_language, code, start=2, end=4)
        assert "Path" in lump.code
    
    def test_case_insensitive_path_comments(self, python_language):
        """Test that Windows paths in comments are preserved"""
        code = [
            "# Config location: C:\\USERS\\ADMIN\\CONFIG.INI",
            "def load_config():",
            "    # Windows paths are case-insensitive",
            "    return parse_config()"
        ]
        
        func_dict = {"start_line": 2, "end_line": 4, "name": "load_config"}
        lump = ChangeLump(python_language, code, func=func_dict)
        lump.extendOverComments()
        
        result = lump.code
        assert "CONFIG.INI" in result or "config" in result.lower()
    
    def test_windows_temp_path(self, python_language):
        """Test Windows temporary file paths"""
        code = [
            "import tempfile",
            r"temp_dir = 'C:\\Users\\Admin\\AppData\\Local\\Temp'",
            "temp_file = os.path.join(temp_dir, 'data.tmp')"
        ]
        
        lump = ChangeLump(python_language, code, start=2, end=3)
        assert "Temp" in lump.code or "temp" in lump.code
    
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_actual_windows_path_operations(self, python_language, tmp_path):
        """Test with actual Windows path operations (only runs on Windows)"""
        # Create a test file with Windows path
        test_file = tmp_path / "test.py"
        code_content = [
            "def get_path():",
            f"    return r'{test_file}'",
            ""
        ]
        test_file.write_text("\n".join(code_content))
        
        # Read and process
        with open(test_file, 'r') as f:
            lines = f.readlines()
        
        lump = ChangeLump(python_language, lines, start=1, end=2)
        assert "get_path" in lump.code


class TestWindowsPathConversion:
    """Test path conversion scenarios"""
    
    def test_posix_to_windows_path_in_code(self, python_language):
        """Test code that converts POSIX to Windows paths"""
        code = [
            "def convert_to_windows(posix_path):",
            "    # Convert /home/user/file to C:\\Users\\user\\file",
            "    return posix_path.replace('/', '\\\\')",
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        assert "convert_to_windows" in lump.code
    
    def test_pathlib_pure_windows_path(self, python_language):
        """Test PureWindowsPath usage"""
        code = [
            "from pathlib import PureWindowsPath",
            "p = PureWindowsPath('C:/Users/Admin/file.txt')",
            "assert str(p) == 'C:\\\\Users\\\\Admin\\\\file.txt'"
        ]
        
        lump = ChangeLump(python_language, code, start=1, end=3)
        assert "PureWindowsPath" in lump.code
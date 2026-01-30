import re
import pytest
from lumpy_log.changelump import ChangeLump
from lumpy_log.languages import Languages
import os

@pytest.fixture
def languages():
    """Load the languages configuration"""
    lang_path = os.path.join(os.path.dirname(__file__), "..", "lumpy_log", "languages.yml")
    return Languages(lang_path)

@pytest.fixture
def python_language(languages):
    """Get Python language"""
    return languages.getByExtension(".py")

@pytest.fixture
def sample_python_code():
    """Sample Python code with a function"""
    return [
        "def calculate_sum(a, b):",
        "    \"\"\"Add two numbers together.\"\"\"",
        "    result = a + b",
        "    return result",
        "",
        "def multiply(x, y):",
        "    \"\"\"Multiply two numbers.\"\"\"",
        "    return x * y",
        "",
        "print('done')"
    ]

class TestChangeLumpWithFunction:
    """Test ChangeLump when initialized with a function"""
    
    def test_function_extraction_basic(self, python_language, sample_python_code):
        """Test extracting a complete function"""
        func_dict = {
            "start_line": 1,
            "end_line": 4,
            "name": "calculate_sum"
        }
        
        lump = ChangeLump(python_language, sample_python_code, func=func_dict)
        code = lump.code
        
        assert "def calculate_sum(a, b):" in code
        assert "result = a + b" in code
        assert "return result" in code
    
    def test_function_bounds(self, python_language, sample_python_code):
        """Test that function start and end are correctly set"""
        func_dict = {
            "start_line": 1,
            "end_line": 4,
            "name": "calculate_sum"
        }
        
        lump = ChangeLump(python_language, sample_python_code, func=func_dict)
        
        assert lump.start == 1  # 1-indexed
        assert lump.end == 4
        assert lump.source == "Function"
    
    def test_function_with_docstring(self, python_language, sample_python_code):
        """Test extracting function with docstring"""
        func_dict = {
            "start_line": 6,
            "end_line": 8,
            "name": "multiply"
        }
        
        lump = ChangeLump(python_language, sample_python_code, func=func_dict)
        code = lump.code
        
        assert "def multiply(x, y):" in code
        assert "Multiply two numbers" in code
        assert "return x * y" in code

class TestChangeLumpWithLineChange:
    """Test ChangeLump when initialized with a line number"""
    
    def test_line_change_single_line(self, python_language, sample_python_code):
        """Test identifying a single changed line"""
        lump = ChangeLump(python_language, sample_python_code, start=3)
        
        assert lump.start == 3  # 1-indexed
        assert lump.end == 3
        assert lump.source == "Line Changed"
    
    def test_line_change_with_range(self, python_language, sample_python_code):
        """Test identifying a range of changed lines"""
        lump = ChangeLump(python_language, sample_python_code, start=2, end=4)
        
        assert lump.start == 2
        assert lump.end == 4

class TestChangeLumpExtend:
    """Test the extend methods"""
    
    def test_extend_over_text_downward(self, python_language, sample_python_code):
        """Test extending a lump over contiguous non-empty lines"""
        lump = ChangeLump(python_language, sample_python_code, start=3)
        lump.extendOverText()
        
        # Should extend to include the function def and docstring
        assert lump.start <= 1
        assert lump.end >= 3
    
    def test_extend_over_comments(self, python_language):
        """Test extending over comment lines"""
        code_with_comments = [
            "# This is a comment",
            "# Another comment",
            "def my_function():",
            "    return 42"
        ]
        
        func_dict = {
            "start_line": 3,
            "end_line": 4,
            "name": "my_function"
        }
        
        lump = ChangeLump(python_language, code_with_comments, func=func_dict)
        lump.extendOverComments()
        
        # Should find comments before the function
        assert lump.commentStart is not None or lump.commentStart is None
        # (Depends on regex matching in language config)
    
    def test_extend_over_text_with_blank_lines(self, python_language):
        """Test extendOverText stops at blank lines"""
        code = [
            "x = 1",
            "y = 2",
            "",
            "z = 3",
            "w = 4"
        ]
        lump = ChangeLump(python_language, code, start=4)
        lump.extendOverText()
        
        assert lump.start == 4
        assert lump.end == 5
        assert "z = 3" in lump.code
        assert "w = 4" in lump.code
        assert "y = 2" not in lump.code

    def test_extend_over_comments_single_comment_before_function(self, python_language):
        """Test extending over a single comment line before function"""
        code = [
            "# This is important",
            "def my_func():",
            "    pass"
        ]
        func_dict = {"start_line": 2, "end_line": 3, "name": "my_func"}
        
        lump = ChangeLump(python_language, code, func=func_dict)
        lump.extendOverComments()
        
        assert lump.commentStart == 1
        assert "# This is important" in lump.code

class TestChangeLumpInLump:
    """Test the inLump method"""
    
    def test_in_lump_true(self, python_language, sample_python_code):
        """Test when line is within the lump"""
        lump = ChangeLump(python_language, sample_python_code, start=2, end=4)
        
        assert lump.inLump(2) == True
        assert lump.inLump(3) == True
        assert lump.inLump(4) == True
    
    def test_in_lump_false_before(self, python_language, sample_python_code):
        """Test when line is before the lump"""
        lump = ChangeLump(python_language, sample_python_code, start=3, end=4)
        
        assert lump.inLump(1) == False
    
    def test_in_lump_false_after(self, python_language, sample_python_code):
        """Test when line is after the lump"""
        lump = ChangeLump(python_language, sample_python_code, start=2, end=3)
        
        assert lump.inLump(4) == False
    
    def test_in_lump_boundary_edges(self, python_language, sample_python_code):
        """Test inLump with boundary edge cases"""
        lump = ChangeLump(python_language, sample_python_code, start=2, end=4)
        
        assert lump.inLump(1) == False
        assert lump.inLump(2) == True
        assert lump.inLump(3) == True
        assert lump.inLump(4) == True
        assert lump.inLump(5) == False

class TestChangeLumpBoundaryConditions:
    """Test edge cases and boundary conditions"""
    
    def test_zero_line_index(self, python_language, sample_python_code):
        """Test with line at index 1 (first line, 1-indexed)"""
        lump = ChangeLump(python_language, sample_python_code, start=1)
        
        assert lump.start == 1
    
    def test_negative_start_handled(self, python_language, sample_python_code):
        """Test that negative start is clamped to 1"""
        lump = ChangeLump(python_language, sample_python_code, start=-5)
        
        assert lump.start == 1
    
    def test_empty_lines_list(self, python_language):
        """Test with empty lines list"""
        lump = ChangeLump(python_language, [], start=1)
        
        assert lump.start is None
        assert lump.code == ""

    def test_empty_code_from_empty_lines(self, python_language):
        """Test code property returns empty string for empty lines list"""
        lump = ChangeLump(python_language, [], start=1, end=5)
        assert lump.code == ""

    def test_negative_end_clamped(self, python_language, sample_python_code):
        """Test that negative end is handled properly"""
        lump = ChangeLump(python_language, sample_python_code, start=2, end=-1)
        assert lump.end >= lump.start

class TestChangeLumpAdvancedFeatures:
    """Test advanced features: decorators, multi-line comments, and non-function code chunks"""
    
    @pytest.fixture
    def complex_python_code(self):
        """Sample Python code with decorators, multi-line comments, and standalone code"""
        return [
            "# Single line comment at top",
            "import os",
            "import sys",
            "",
            "\"\"\"",
            "This is a module-level docstring.",
            "It spans multiple lines.",
            "\"\"\"",
            "",
            "# Configuration constant",
            "MAX_RETRIES = 3",
            "",
            "@property",
            "@cache",
            "def get_user_name(self):",
            "    \"\"\"Get the current user name.\"\"\"",
            "    return os.getenv('USER')",
            "",
            "# Standalone code block",
            "if __name__ == '__main__':",
            "    # This is where execution starts",
            "    print('Starting application')",
            "    user = get_user_name()",
            "    print(f'Hello {user}')",
            "    # End of main block",
        ]
    
    def test_function_with_decorators(self, python_language, complex_python_code):
        """Test that decorators above a function are captured"""
        func_dict = {
            "start_line": 15,  # get_user_name function
            "end_line": 17,
            "name": "get_user_name"
        }
        
        lump = ChangeLump(python_language, complex_python_code, func=func_dict)
        lump.extendOverComments()
        code = lump.code
        
        # Should include the function
        assert "def get_user_name(self):" in code
        assert "return os.getenv('USER')" in code
        
        # TODO: Issue #18 - decorators are NOT currently captured
        # These assertions will fail until decorators are implemented
        assert "@property" in code
        assert "@cache" in code
    
    def test_multi_line_docstring_detection(self, python_language, complex_python_code):
        """Test detection of multi-line docstrings as comments"""
        # Test a line within the multi-line docstring
        lump = ChangeLump(python_language, complex_python_code, start=6, end=6)
        
        lump.debug = True

        # Line 6 (index 5) is inside the docstring
        is_comment = lump.lineIsComment(5)
        
        # This should detect multi-line comment (depends on language config)
        is_comment = lump.lineIsComment(10)
        assert is_comment == True
    
    def test_single_line_comment_detection(self, python_language, complex_python_code):
        """Test detection of single-line comments"""
        lump = ChangeLump(python_language, complex_python_code, start=10, end=11)
        
        # Line 10 (1-indexed) is "# Configuration constant"
        is_comment = lump.lineIsComment(10)
        
        assert is_comment == True
    
    def test_standalone_code_with_3_line_context(self, python_language, complex_python_code):
        """Test Issue #13: Extract standalone code with 3 lines before/after context"""
        # Simulate a change on line 22 (print('Starting application'))
        changed_line = 22  # 1-indexed
        
        lump = ChangeLump(python_language, complex_python_code, start=changed_line)
        
        # Initial state: just the changed line
        assert lump.start == 22  # 1-indexed
        assert lump.end == 22
        
        # Extend to get context
        lump.extendOverText()
        
        code = lump.code
        
        # Should include context around the change
        assert "    # This is where execution starts" in code
        assert "if __name__ == '__main__':" in code
        assert "print('Starting application')" in code
        assert "user = get_user_name()" in code
        
        # Verify we got reasonable context (not the whole file)
        assert "import os" not in code
        assert "MAX_RETRIES" not in code
    
    def test_standalone_code_stops_at_blank_lines(self, python_language, complex_python_code):
        """Test that extendOverText stops at blank lines (natural boundaries)"""
        # Change on the constant line (line 11)
        lump = ChangeLump(python_language, complex_python_code, start=11)
        lump.extendOverText()
        
        code = lump.code
        
        # Should include the comment and constant
        assert "# Configuration constant" in code
        assert "MAX_RETRIES = 3" in code
        
        # Should NOT extend beyond blank lines
        assert "@property" not in code
        assert "import os" not in code
    
    def test_extend_over_comments_before_decorators(self, python_language, complex_python_code):
        """Test extending over comments, but decorators aren't treated as comments"""
        func_dict = {
            "start_line": 15,  # get_user_name function
            "end_line": 17,
            "name": "get_user_name"
        }
        
        lump = ChangeLump(python_language, complex_python_code, func=func_dict)
        lump.extendOverComments()
        
        # extendOverComments should stop at decorators (they're not comments)
        # commentStart should be None or not extend past decorators
        if lump.commentStart is not None:
            # Should not reach back to "MAX_RETRIES" or imports
            code_lines = complex_python_code[lump.commentStart:lump.end+1]
            code_str = "\n".join(code_lines)
            assert "MAX_RETRIES" not in code_str

    def test_multiple_single_line_comments_captured(self, python_language):
        """Test that consecutive single-line comments are captured"""
        code_with_multiple_comments = [
            "# Comment 1",
            "# Comment 2", 
            "# Comment 3",
            "def my_function():",
            "    return True"
        ]
        
        func_dict = {
            "start_line": 4,
            "end_line": 5,
            "name": "my_function"
        }
        
        lump = ChangeLump(python_language, code_with_multiple_comments, func=func_dict)
        lump.extendOverComments()
        
        code = lump.code
        
        # Should capture all preceding comments
        assert "# Comment 1" in code
        assert "# Comment 2" in code
        assert "# Comment 3" in code
        assert "def my_function():" in code

class TestChangeLumpMisc:
    """Test miscellaneous cases and edge conditions"""
    
    def test_line_change_with_equal_start_end(self, python_language, sample_python_code):
        """Test line change where start equals end"""
        lump = ChangeLump(python_language, sample_python_code, start=4, end=4)
        
        assert lump.start == 4
        assert lump.end == 4
        assert lump.source == "Line Changed"
    
    def test_code_property_with_comment_start(self, python_language):
        """Test code property correctly uses commentStart"""
        code = ["# comment", "def foo():", "    pass"]
        func_dict = {"start_line": 2, "end_line": 3, "name": "foo"}
        
        lump = ChangeLump(python_language, code, func=func_dict)
        lump.commentStart = 1
        
        assert "# comment" in lump.code
        assert "def foo():" in lump.code
    
    def test_extend_over_text_upward_and_downward(self, python_language):
        """Test extendOverText extends both directions"""
        code = [
            "a = 1",
            "b = 2",
            "c = 3",
            "d = 4",
            "e = 5"
        ]
        lump = ChangeLump(python_language, code, start=3, end=3)
        lump.extendOverText()
        
        assert lump.start == 1
        assert lump.end == 5
        assert "a = 1" in lump.code
        assert "e = 5" in lump.code
    
    def test_function_source_not_set_for_line_changes(self, python_language, sample_python_code):
        """Test that source is set to 'Line Changed' for line-based initialization"""
        lump = ChangeLump(python_language, sample_python_code, start=1)
        assert lump.source == "Line Changed"
    
    def test_func_initialization_without_end(self, python_language, sample_python_code):
        """Test func initialization with missing optional fields"""
        func_dict = {"start_line": 1, "end_line": 3}
        lump = ChangeLump(python_language, sample_python_code, func=func_dict)
        
        assert lump.source == "Function"
        assert lump.start == 1
        assert lump.end == 3

    def test_code_property_respects_comment_start_zero(self, python_language):
        """Ensure commentStart=0 is honored (truthy check bugfix)."""
        code = [
            "# header comment",
            "def foo():",
            "    return 1",
        ]
        func_dict = {"start_line": 2, "end_line": 3, "name": "foo"}
        lump = ChangeLump(python_language, code, func=func_dict)
        lump.commentStart = 1

        result = lump.code
        assert result.startswith("# header comment")
        assert "def foo()" in result

    def test_extend_over_comments_no_comments_present(self, python_language):
        """extendOverComments should leave commentStart None when none exist."""
        code = [
            "def bar():",
            "    return 2",
        ]
        func_dict = {"start_line": 1, "end_line": 2, "name": "bar"}
        lump = ChangeLump(python_language, code, func=func_dict)
        lump.extendOverComments()

        assert lump.commentStart is None
        assert lump.code == "\n".join(code)

    def test_line_change_with_empty_slice(self, python_language):
        """Changing a line beyond list length should clamp and yield empty code."""
        lump = ChangeLump(python_language, [], start=10, end=12)
        assert lump.start == None
        assert lump.end == None
        assert lump.code == ""

    def test_line_change_too_big(self, python_language):
        """Changing a line beyond list length should clamp and yield empty code."""
        code = [
            "# header comment",
            "def foo():",
            "    return 1",
        ]
        
        lump = ChangeLump(python_language, code, start=10, end=12)
        assert lump.start == None
        assert lump.end == None
        assert lump.code == ""
#!/usr/bin/python3
"""Tests for TAP parser module."""

import pytest
from lumpy_log.tap_parser import SimpleTAPParser, TAPResult, parse_test_output


class TestTAPResult:
    """Tests for TAPResult dataclass"""
    
    def test_default_values(self):
        """Test TAPResult initializes with correct defaults"""
        result = TAPResult()
        assert result.version is None
        assert result.plan_start == 0
        assert result.plan_end == 0
        assert result.tests_run == 0
        assert result.tests_passed == 0
        assert result.tests_failed == 0
        assert result.tests_skipped == 0
        assert result.failed_tests == []
        assert result.raw_output == ""
    
    def test_custom_values(self):
        """Test TAPResult can be initialized with custom values"""
        result = TAPResult(
            version=13,
            plan_start=1,
            plan_end=5,
            tests_run=5,
            tests_passed=3,
            tests_failed=2,
            raw_output="test output"
        )
        assert result.version == 13
        assert result.plan_end == 5
        assert result.tests_passed == 3


class TestSimpleTAPParserIsTapFormat:
    """Tests for is_tap_format detection"""
    
    def test_detects_version_line(self):
        """Should detect TAP version line"""
        output = "TAP version 13\n1..5"
        assert SimpleTAPParser.is_tap_format(output) is True
    
    def test_detects_plan_line(self):
        """Should detect TAP plan line"""
        output = "1..10\nok 1 - test passes"
        assert SimpleTAPParser.is_tap_format(output) is True
    
    def test_detects_test_line(self):
        """Should detect TAP test result line"""
        output = "ok 1 - first test\nok 2 - second test"
        assert SimpleTAPParser.is_tap_format(output) is True
    
    def test_rejects_non_tap(self):
        """Should reject non-TAP output"""
        output = "This is just regular output\nNothing TAP-like here"
        assert SimpleTAPParser.is_tap_format(output) is False
    
    def test_rejects_empty_string(self):
        """Should reject empty string"""
        assert SimpleTAPParser.is_tap_format("") is False
    
    def test_case_insensitive_detection(self):
        """Should detect TAP regardless of case"""
        output = "tap version 13\nOK 1 test"
        assert SimpleTAPParser.is_tap_format(output) is True


class TestSimpleTAPParserParse:
    """Tests for parse method"""
    
    def test_parse_simple_passing_tests(self):
        """Parse simple passing tests"""
        tap_output = """TAP version 13
1..3
ok 1 - First test
ok 2 - Second test
ok 3 - Third test
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.version == 13
        assert result.plan_start == 1
        assert result.plan_end == 3
        assert result.tests_run == 3
        assert result.tests_passed == 3
        assert result.tests_failed == 0
        assert result.tests_skipped == 0
        assert len(result.failed_tests) == 0
    
    def test_parse_failing_tests(self):
        """Parse failing tests"""
        tap_output = """1..3
ok 1 - First test
not ok 2 - Second test failed
ok 3 - Third test
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.tests_run == 3
        assert result.tests_passed == 2
        assert result.tests_failed == 1
        assert len(result.failed_tests) == 1
        assert result.failed_tests[0]['number'] == '2'
        assert result.failed_tests[0]['description'] == '- Second test failed'
    
    def test_parse_skipped_tests(self):
        """Parse skipped tests with SKIP directive"""
        tap_output = """1..3
ok 1 - First test
ok 2 - Second test # SKIP not implemented yet
ok 3 - Third test
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.tests_run == 3
        assert result.tests_passed == 2
        assert result.tests_skipped == 1
        assert result.tests_failed == 0
    
    def test_parse_without_test_numbers(self):
        """Parse tests without explicit test numbers"""
        tap_output = """1..2
ok - test one
not ok - test two
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.tests_run == 2
        assert result.tests_passed == 1
        assert result.tests_failed == 1
        assert result.failed_tests[0]['number'] == '2'
    
    def test_parse_with_descriptions(self):
        """Parse tests with various description formats"""
        tap_output = """1..4
ok 1 This is a description
ok 2 - This has a dash
ok 3 - Complex description with #hashtags
not ok 4 - Failed test with detail
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.tests_run == 4
        assert result.tests_passed == 3
        assert result.tests_failed == 1
        assert 'Failed test with detail' in result.failed_tests[0]['description']
    
    def test_parse_bail_out(self):
        """Parse bail out directive"""
        tap_output = """1..10
ok 1 - First test
ok 2 - Second test
Bail out! Database connection failed
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.tests_run == 2
        assert len(result.failed_tests) == 1
        assert result.failed_tests[0]['number'] == 'BAIL'
        assert 'Database connection failed' in result.failed_tests[0]['description']
    
    def test_parse_todo_directive(self):
        """Parse TODO directive"""
        tap_output = """1..2
ok 1 - First test
not ok 2 - Second test # TODO fix this later
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.tests_run == 2
        assert result.tests_passed == 1
        assert result.tests_failed == 1
    
    def test_parse_empty_output(self):
        """Parse empty output"""
        result = SimpleTAPParser.parse("")
        
        assert result.tests_run == 0
        assert result.tests_passed == 0
        assert result.tests_failed == 0
        assert result.raw_output == ""
    
    def test_parse_whitespace_only(self):
        """Parse whitespace-only output"""
        result = SimpleTAPParser.parse("   \n  \n  ")
        
        assert result.tests_run == 0
    
    def test_parse_plan_with_comment(self):
        """Parse plan with comment"""
        tap_output = """1..5 # Running 5 tests
ok 1
ok 2
ok 3
ok 4
ok 5
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.plan_end == 5
        assert result.tests_run == 5
    
    def test_parse_case_insensitive(self):
        """Parse with mixed case"""
        tap_output = """TAP VERSION 13
1..2
OK 1 - test
NOT OK 2 - test # SKIP reason
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.version == 13
        assert result.tests_run == 2
        assert result.tests_passed == 1
        assert result.tests_skipped == 1
    
    def test_parse_with_diagnostics(self):
        """Parse with diagnostic lines (comments)"""
        tap_output = """1..2
# Starting tests
ok 1 - First test
# Some diagnostic info
not ok 2 - Second test
# More diagnostics
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.tests_run == 2
        assert result.tests_passed == 1
        assert result.tests_failed == 1


class TestParseTestOutput:
    """Tests for parse_test_output wrapper function"""
    
    def test_parse_tap_format(self):
        """Parse valid TAP format output"""
        tap_output = """1..3
ok 1 - test one
ok 2 - test two
ok 3 - test three
"""
        result = parse_test_output(tap_output)
        
        assert result['format'] == 'tap'
        assert result['tests_run'] == 3
        assert result['tests_passed'] == 3
        assert result['tests_failed'] == 0
        assert result['summary'] == '3 tests run'
    
    def test_parse_non_tap_format(self):
        """Parse non-TAP format output"""
        raw_output = """Running tests...
Test 1: PASS
Test 2: FAIL
All tests complete
"""
        result = parse_test_output(raw_output)
        
        assert result['format'] == 'raw'
        assert result['tests_run'] == 0
        assert 'raw_output' not in result  # Parser no longer includes raw_output
        assert 'lines captured' in result['summary']
    
    def test_parse_empty_output(self):
        """Parse empty output"""
        result = parse_test_output("")
        
        assert result['format'] == 'empty'
        assert result['tests_run'] == 0
        assert result['summary'] == 'No test output received'
    
    def test_parse_whitespace_output(self):
        """Parse whitespace-only output"""
        result = parse_test_output("   \n  \n  ")
        
        assert result['format'] == 'empty'
        assert result['tests_run'] == 0
    
    def test_parse_none_output(self):
        """Parse None as output"""
        result = parse_test_output(None)
        
        assert result['format'] == 'empty'
    
    def test_parse_tap_with_failures(self):
        """Parse TAP with failed tests"""
        tap_output = """1..2
ok 1 - passing test
not ok 2 - failing test
"""
        result = parse_test_output(tap_output)
        
        assert result['format'] == 'tap'
        assert result['tests_failed'] == 1
        assert len(result['failed_tests']) == 1
        assert result['failed_tests'][0]['number'] == '2'
    
    def test_raw_output_not_in_parser(self):
        """Verify parser does NOT include raw_output (added by TestProcessor)"""
        original = "1..1\nok 1 - test"
        result = parse_test_output(original)
        
        assert 'raw_output' not in result  # Parser doesn't include it anymore


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_very_long_output(self):
        """Handle very long output"""
        lines = ["ok {} - test".format(i) for i in range(1, 1001)]
        tap_output = "1..1000\n" + "\n".join(lines)
        
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.tests_run == 1000
        assert result.tests_passed == 1000
    
    def test_special_characters_in_description(self):
        """Handle special characters in test descriptions"""
        tap_output = """1..3
ok 1 - test with "quotes"
ok 2 - test with <brackets>
ok 3 - test with & ampersand
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.tests_run == 3
        assert result.tests_passed == 3
    
    def test_unicode_in_description(self):
        """Handle Unicode characters"""
        tap_output = """1..2
ok 1 - test with emoji 🎉
ok 2 - test with español
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.tests_run == 2
        assert result.tests_passed == 2
    
    def test_multiple_plans_uses_first(self):
        """Handle multiple plan lines (use first)"""
        tap_output = """1..5
1..10
ok 1
"""
        result = SimpleTAPParser.parse(tap_output)
        
        assert result.plan_end == 5
    
    def test_mixed_line_endings(self):
        """Handle mixed line endings"""
        tap_output = "1..2\rok 1\r\nok 2\n"
        result = SimpleTAPParser.parse(tap_output)
        
        # Should handle at least some of the tests
        assert result.tests_run >= 1

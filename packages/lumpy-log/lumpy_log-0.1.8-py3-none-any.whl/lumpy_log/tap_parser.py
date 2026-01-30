#!/usr/bin/python3
"""TAP (Test Anything Protocol) parser for test output processing."""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TAPResult:
    """Represents parsed TAP output"""
    version: Optional[int] = None
    plan_start: int = 0
    plan_end: int = 0
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    failed_tests: List[Dict[str, str]] = field(default_factory=list)
    raw_output: str = ""


class SimpleTAPParser:
    """Minimal TAP parser - extracts ok/not ok lines and counts"""
    
    # TAP regex patterns
    VERSION_RE = re.compile(r'^TAP version (\d+)\s*$', re.IGNORECASE)
    PLAN_RE = re.compile(r'^1\.\.(\d+)\s*(?:#\s*(.*))?$')
    TEST_LINE_RE = re.compile(
        r'^(ok|not ok)\s+(\d+)?\s*([^#]*?)?\s*(?:#\s*(TODO|SKIP|todo|skip)?\s*(.*))?$',
        re.IGNORECASE
    )
    DIAGNOSTIC_RE = re.compile(r'^#\s*(.*)$')
    BAIL_OUT_RE = re.compile(r'^Bail out!\s*(.*)$', re.IGNORECASE)
    
    @staticmethod
    def parse(tap_output: str) -> TAPResult:
        """Parse TAP format output"""
        result = TAPResult(raw_output=tap_output)
        lines = tap_output.split('\n')
        
        test_number = 0
        plan_seen = False
        
        for line in lines:
            line = line.rstrip()
            
            # Check version
            version_match = SimpleTAPParser.VERSION_RE.match(line)
            if version_match:
                result.version = int(version_match.group(1))
                continue
            
            # Check plan (only accept first plan line)
            plan_match = SimpleTAPParser.PLAN_RE.match(line)
            if plan_match and not plan_seen:
                result.plan_start = 1
                result.plan_end = int(plan_match.group(1))
                plan_seen = True
                continue
            
            # Check test line
            test_match = SimpleTAPParser.TEST_LINE_RE.match(line)
            if test_match:
                status = test_match.group(1).lower()
                number = test_match.group(2)
                description = test_match.group(3).strip() if test_match.group(3) else ""
                directive = test_match.group(4)
                directive_reason = test_match.group(5)
                
                test_number += 1
                result.tests_run = test_number
                
                if directive and directive.upper() == 'SKIP':
                    result.tests_skipped += 1
                elif status == 'ok':
                    result.tests_passed += 1
                else:  # not ok
                    result.tests_failed += 1
                    result.failed_tests.append({
                        'number': number or str(test_number),
                        'description': description,
                        'line': line
                    })
                
                continue
            
            # Check bail out
            bail_match = SimpleTAPParser.BAIL_OUT_RE.match(line)
            if bail_match:
                result.failed_tests.append({
                    'number': 'BAIL',
                    'description': bail_match.group(1),
                    'line': line
                })
                break
        
        return result

    @staticmethod
    def is_tap_format(output: str) -> bool:
        """Quick check if output appears to be TAP format"""
        lines = output.split('\n')[:20]  # Check first 20 lines
        
        for line in lines:
            if SimpleTAPParser.VERSION_RE.match(line):
                return True
            if SimpleTAPParser.PLAN_RE.match(line):
                return True
            if SimpleTAPParser.TEST_LINE_RE.match(line):
                return True
        
        return False


def parse_test_output(output: str) -> Dict:
    """
    Parse test output - TAP if available, raw otherwise
    
    Returns dictionary with test results data
    """
    if not output or not output.strip():
        return {
            'format': 'empty',
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'failed_tests': [],
            'summary': 'No test output received'
        }
    
    if SimpleTAPParser.is_tap_format(output):
        tap_result = SimpleTAPParser.parse(output)
        return {
            'format': 'tap',
            'tests_run': tap_result.tests_run,
            'tests_passed': tap_result.tests_passed,
            'tests_failed': tap_result.tests_failed,
            'tests_skipped': tap_result.tests_skipped,
            'failed_tests': tap_result.failed_tests,
            'summary': f'{tap_result.tests_run} tests run'
        }
    else:
        # Fallback: just capture raw output
        line_count = len(output.split('\n'))
        return {
            'format': 'raw',
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'failed_tests': [],
            'summary': f'{line_count} lines captured'
        }

#!/usr/bin/python3
"""Process test output and generate markdown documentation."""

import sys
import os
from datetime import datetime
from pathlib import Path
from . import OUTPUT_TESTRESULTS_DIR
from jinja2 import Environment, FileSystemLoader
from .tap_parser import parse_test_output
from .utils import _clean_markdown, _get_templates_dir, _format_markdown, _rebuild_index
from .config import print_active_config, get_output_format, get_config_value, get_raw_output

class TestProcessor:
    """Process test output and generate markdown files"""
    
    def __init__(self, output_folder: str = "devlog"):
        self.output_folder = Path(output_folder or "devlog")
        self.tests_dir = self.output_folder / OUTPUT_TESTRESULTS_DIR
        
        # Set up Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader(_get_templates_dir()))
    
    def setup_directories(self):
        """Create necessary directory structure"""
        self.tests_dir.mkdir(parents=True, exist_ok=True)
    
    def read_input(self, input_file: str = None) -> str:
        """
        Read test output from file or stdin
        
        Args:
            input_file: Path to file, or None to read from stdin
            
        Returns:
            Test output as string
            
        Raises:
            ValueError: If stdin is empty and no file provided
        """
        if input_file:
            with open(input_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Read from stdin
            if sys.stdin.isatty():
                raise ValueError(
                    "No input provided. Either pipe test output or use --input <file>.\n"
                    "Example: pytest --tap | lumpy-log test"
                )
            
            content = sys.stdin.read()
            if not content or not content.strip():
                raise ValueError(
                    "Empty input received. Please provide test output via pipe or file."
                )
            
            return content
    
    def generate_filename(self) -> str:
        """Generate timestamped filename for test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"{timestamp}.md"
    
    def process_test_output(
        self,
        output: str,
        verbose: bool = False,
        raw_output: bool = False,
        build_devlog: bool = False,
        limit: int = None,
        output_formats: list = None,
    ) -> Path:
        """
        Process test output and generate markdown file
        
        Args:
            output: Test output string
            verbose: Print progress messages
            raw_output: Include raw output in the markdown report
            output_formats: List of output formats (e.g., ['obsidian', 'docx'])
            
        Returns:
            Path to generated markdown file
        """
        # Use provided formats or default to obsidian
        if output_formats is None:
            output_formats = ["obsidian"]
        
        # Parse test output
        test_data = parse_test_output(output)
        
        # Add metadata
        test_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_data['generation_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Only include raw output if explicitly requested
        if raw_output:
            test_data['raw_output'] = output
        
        # Load template and render
        template = self.jinja_env.get_template("test_results.md")
        markdown_content = template.render(test_data)
        
        # Generate filename and save
        filename = self.generate_filename()
        filepath = self.tests_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(_format_markdown(markdown_content))
        
        if verbose:
            print(f"Test results saved to: {filepath}")
            if test_data['format'] == 'tap':
                print(f"  Tests run: {test_data['tests_run']}")
                print(f"  Passed: {test_data['tests_passed']}")
                print(f"  Failed: {test_data['tests_failed']}")
                print(f"  Skipped: {test_data['tests_skipped']}")
        
        # Rebuild index to include new test results
        _rebuild_index(
            str(self.output_folder),
            verbose=verbose,
            output_formats=output_formats,
            limit=limit,
            repo_path=".",
        )
        
        return filepath
    
def main(args: dict) -> int:
    """
    Main entry point for test processing
    
    Args:
        args: Dictionary of CLI arguments
    """
    repo_path = '.'

    # Resolve verbosity from CLI/config/defaults
    verbose = get_config_value('verbose', args, repo_path, False)

    if verbose:
        print_active_config(args, repo_path)
    
    output_folder = get_config_value('outputfolder', args, repo_path, 'devlog')
    
    # Determine output formats from config and CLI
    output_formats = get_output_format(args, repo_path)
    
    processor = TestProcessor(output_folder)
    processor.setup_directories()
    
    try:
        # Read input
        output = processor.read_input(args.get('input'))
        
        # Process and generate markdown
        raw_output = bool(get_raw_output(args, repo_path, False))
        filepath = processor.process_test_output(
            output, 
            verbose=verbose,
            raw_output=raw_output,
            build_devlog=args.get("devlog", False),
            limit=args.get('limit'),
            output_formats=output_formats,
        )
        
        if not verbose:
            print(f"Test results saved to: {filepath}")
        
        return 0
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error processing test output: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1

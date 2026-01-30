"""Command-line interface for Lumpy Log"""
import argparse
import sys
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from .core import main as core_main
from .test_processor import main as test_main
from .config import get_output_format, print_active_config, get_config_value
from .utils import _rebuild_index, _get_templates_dir, _format_markdown
from . import OUTPUT_JOURNAL_DIR, OUTPUT_CHANGELOGS_DIR, OUTPUT_TESTRESULTS_DIR


def rebuild_main(args):
    """Rebuild index from existing commits and test results"""
    try:
        # Use config system for defaults
        from .config import get_config_value
        
        output_folder = get_config_value('outputfolder', args, '.', 'devlog')
        repo_path = '.'
        
        # Show active configuration if verbose
        verbose = get_config_value('verbose', args, '.', False)
        if verbose:
            print_active_config(args, repo_path)
        
        # Check if CLI switch was provided
        if args.get('output_format'):
            output_formats = args['output_format']
            if isinstance(output_formats, str):
                output_formats = [output_formats]
        else:
            output_formats = get_output_format(args, repo_path)
        
        # Detect current branch
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            current_branch = result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            current_branch = "unknown"
        
        results = _rebuild_index(
            output_folder,
            verbose=verbose,
            changelog_order=get_config_value('changelog', args, '.', False),
            output_formats=output_formats,
            current_branch=current_branch,
            limit=get_config_value('limit', args, '.', None),
            repo_path=repo_path
        )
        
        if not verbose:
            parts = ["Index rebuilt:"]
            if "obsidian" in results:
                parts.append(f"{results['obsidian']}")
            if "devlog" in results:
                parts.append(f"{results['devlog']}")
            if "docx" in results:
                parts.append(f"{results['docx']}")
            print(" ".join(parts))
        else:
            # If docx was requested but not produced, emit an explicit note
            if "docx" in output_formats and "docx" not in results:
                print("Note: docx requested but not produced (md2docx not installed or failed)")
        return 0
    except Exception as e:
        print(f"Error rebuilding index: {e}", file=sys.stderr)
        verbose = args.get('verbose', False)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def entry_main(args):
    """Create a new dated entry from the entry template and rebuild index"""
    repo_path = '.'
    verbose = get_config_value('verbose', args, repo_path, False)
    if verbose:
        print_active_config(args, repo_path)

    output_folder = get_config_value('outputfolder', args, repo_path, 'devlog')
    entries_dir = Path(output_folder) / OUTPUT_JOURNAL_DIR
    entries_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    title = args.get('title') or now.strftime("%Y-%m-%d")
    filename = args.get('filename') or f"{now.strftime('%Y%m%d')}.md"
    filepath = entries_dir / filename

    if filepath.exists() and not args.get('force'):
        print(f"Entry already exists: {filepath}", file=sys.stderr)
        return 1

    env = Environment(loader=FileSystemLoader(_get_templates_dir()))
    template = env.get_template('journal-entry.md')
    rendered = template.render({
        'title': title,
        'generation_date': now.strftime('%Y-%m-%d %H:%M:%S'),
    })
    content = _format_markdown(rendered)
    filepath.write_text(content, encoding='utf-8')

    if verbose:
        print(f"Entry created: {filepath}")

    output_formats = get_output_format(args, repo_path)
    _rebuild_index(
        output_folder,
        verbose=verbose,
        changelog_order=get_config_value('changelog', args, repo_path, False),
        output_formats=output_formats,
        current_branch=None,
        limit=get_config_value('limit', args, repo_path, None),
        repo_path=repo_path,
    )

    if not verbose:
        print(f"Entry created: {filepath}")

    return 0


def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        prog='lumpy-log',
        description='Make git logs easier for use in scenarios when communicating the progress of a project to non-experts.',
        epilog='Use "lumpy-log <command> --help" for more information about a command.'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Changes command (processes git commits)
    changes_parser = subparsers.add_parser('changes', help='Generate change logs from git commits (default if no command specified)')
    changes_parser.add_argument(
        "-i", "--repo",
        default='.',
        help="Path to the local Git repository (default: current directory)"
    )
    changes_parser.add_argument(
        "-o", "--outputfolder",
        default=None,
        help="Output folder for generated files (default: devlog)"
    )
    changes_parser.add_argument(
        "-f", "--fromcommit",
        dest="from_commit",
        help="Start from this commit"
    )
    changes_parser.add_argument(
        "-t", "--tocommit",
        dest="to_commit",
        help="End at this commit"
    )
    changes_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=None,
        help="Verbose output"
    )
    changes_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing files"
    )
    changes_parser.add_argument(
        "-d", "--dryrun",
        action="store_true",
        help="Dry run - don't write files"
    )

    changes_parser.add_argument(
        "--devlog",
        action="store_true",
        default=None,
        help="Generate a combined devlog.md with all commit and test content",
    )
    changes_parser.add_argument(
        "--limit",
        type=int,
        help="Limit index/devlog to N most recent entries"
    )
    
    # Test command (processes test output)
    test_parser = subparsers.add_parser(
        'test', 
        help='Process unit test output and generate test_results entry',
        description='Process test output (TAP format or raw text) and generate markdown documentation.',
        epilog='''
Examples:
  Bash/Linux/macOS:
    pytest --tap | lumpy-log test
    pytest --tap > results.txt && lumpy-log test --input results.txt
  
  Windows (cmd/PowerShell):
    py -m pytest --tap | lumpy-log test
    py -m pytest --tap > results.txt
    lumpy-log test --input results.txt
  
Note: Requires pytest-tap plugin (pip install pytest-tap)
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    test_parser.add_argument(
        "-o", "--outputfolder",
        default=None,
        help="Output folder containing change_logs/, journal/ and tests/ (default: devlog)"

    )
    test_parser.add_argument(
        "--input",
        help="Input file with test output (if not specified, reads from stdin)"
    )
    test_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=None,
        help="Verbose output"
    )
    test_parser.add_argument(
        "--raw-test-output",
        dest="raw_test_output",
        action="store_true",
        default=None,
        help="Include raw test output in the report"
    )
    
    test_parser.add_argument(
        "--limit",
        type=int,
        help="Limit index/devlog to N most recent entries"
    )
    
    # Rebuild command (regenerates index from existing files)
    rebuild_parser = subparsers.add_parser(
        'rebuild',
        help='Rebuild the index.md from existing commits and test results',
        description='Scans both commits/ and tests/ folders and regenerates index.md with all items interleaved by time.'
    )
    rebuild_parser.add_argument(
        "-o", "--outputfolder",
        default=None,
        help="Output folder containing change_logs/, journal/ and tests/ (default: devlog)"
    )
    rebuild_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=None,
        help="Verbose output"
    )
    rebuild_parser.add_argument(
        "--changelog",
        action="store_true",
        default=None,
        help="Use changelog order (newest first) instead of default (oldest first)"
    )

    rebuild_parser.add_argument(
        "--output-format",
        dest="output_format",
        nargs='+',
        choices=['obsidian', 'devlog', 'docx'],
        help="Output format(s) (overrides .lumpyconfig.yml)"
    )
    rebuild_parser.add_argument(
        "--limit",
        type=int,
        help="Limit index/devlog to N most recent entries"
    )

    # Journal command (creates a dated journal entry from template)
    journal_entry_parser = subparsers.add_parser(
        'journal',
        help='Create a new dated journal entry from the dev_log_entry template and rebuild the index'
    )
    journal_entry_parser.add_argument(
        "-o", "--outputfolder",
        default=None,
        help="Parent output folder containing journal/, change_logs/, and tests/ (default: devlog)"
    )
    journal_entry_parser.add_argument(
        "-t", "--title",
        help="Title to place in the journal entry"
    )
    journal_entry_parser.add_argument(
        "-f", "--filename",
        help="Optional filename for the journal entry (default: YYYYMMDD.md)"
    )
    journal_entry_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing journal entry file if present"
    )
    journal_entry_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=None,
        help="Verbose output"
    )
    journal_entry_parser.add_argument(
        "--limit",
        type=int,
        help="Limit index/devlog to N most recent entries"
    )
    journal_entry_parser.add_argument(
        "--output-format",
        dest="output_format",
        nargs='+',
        choices=['obsidian', 'devlog', 'docx'],
        help="Output format(s) (overrides .lumpyconfig.yml)"
    )
    
    # Parse args, but handle backwards compatibility
    # If first arg looks like an option (starts with -) but is NOT --help/-h, assume 'changes' command
    if len(sys.argv) > 1 and sys.argv[1].startswith('-') and sys.argv[1] not in ['--help', '-h']:
        # Insert 'changes' as the command for backwards compatibility
        sys.argv.insert(1, 'changes')
    
    args = parser.parse_args()
    
    # Default to 'changes' if no command specified (backwards compatibility)
    if args.command is None:
        # Re-parse args as if 'changes' was provided as the command
        new_argv = sys.argv[:1] + ['changes'] + sys.argv[1:]
        args = parser.parse_args(new_argv[1:])
        args.command = 'changes'
        # Continue as if 'changes' was specified
        # (fall through to the handler below)
    
    # Route to appropriate handler
    if args.command == 'test':
        sys.exit(test_main(vars(args)))
    elif args.command == 'rebuild':
        sys.exit(rebuild_main(vars(args)))
    elif args.command == 'journal':
        sys.exit(entry_main(vars(args)))
    else:
        sys.exit(core_main(vars(args)))


if __name__ == "__main__":
    main()

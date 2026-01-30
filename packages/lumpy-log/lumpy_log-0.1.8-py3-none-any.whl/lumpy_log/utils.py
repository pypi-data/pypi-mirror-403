import os
import re
from pathlib import Path
from . import OUTPUT_JOURNAL_DIR, OUTPUT_CHANGELOGS_DIR, OUTPUT_TESTRESULTS_DIR
from . import ITEM_TYPE_CHANGELOG, ITEM_TYPE_TEST, ITEM_TYPE_ENTRY
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import mdformat
from lumpy_log.config import get_hcti_credentials

# Export for external use
__all__ = [
    "_get_templates_dir",
    "_clean_markdown",
    "_format_markdown",
    "_collect_items",
    "_generate_obsidian_index",
    "_generate_devlog",
    "_generate_docx",
    "_rebuild_index",
]


def _get_templates_dir():
    package_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(package_dir, "templates")

def _clean_markdown(md: str) -> str:
    cleaned_lines = [line.rstrip() for line in md.splitlines()]
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip() + "\n"

def _format_markdown(md: str) -> str:
    if mdformat:
        try:
            return mdformat.text(md).rstrip() + "\n"
        except Exception:
            pass
    return _clean_markdown(md)

def _collect_items(output_folder: str, changelog_order: bool = False, limit: int = None) -> tuple:
    """Collect and organize commit and test items from output folder.
    
    Args:
        output_folder: Base output folder containing change_logs/, test_results/, journal/
        changelog_order: If True, sort newest first. If False (default), oldest first
        limit: If specified, limit to N most recent entries
    
    Returns:
        Tuple of (items_list, commit_files, test_files, entry_files, total_before_limit)
    """
    output_path = Path(output_folder)
    commits_dir = output_path / OUTPUT_CHANGELOGS_DIR
    tests_dir = output_path / OUTPUT_TESTRESULTS_DIR
    entries_dir = output_path / OUTPUT_JOURNAL_DIR
    
    # Collect files
    change_log_files = sorted(commits_dir.glob("*.md")) if commits_dir.exists() else []
    test_result_files = sorted(tests_dir.glob("*.md")) if tests_dir.exists() else []
    journal_files = sorted(entries_dir.glob("*.md")) if entries_dir.exists() else []
    
    # Create combined list with type markers
    items = []
    for f in change_log_files:
        items.append({"path": f"{OUTPUT_CHANGELOGS_DIR}/{f.name}", "name": f.stem, "type": ITEM_TYPE_CHANGELOG, "filename": f.name})
    for f in test_result_files:
        items.append({"path": f"{OUTPUT_TESTRESULTS_DIR}/{f.name}", "name": f.stem, "type": ITEM_TYPE_TEST, "filename": f.name})
    for f in journal_files:
        items.append({"path": f"{OUTPUT_JOURNAL_DIR}/{f.name}", "name": f.stem, "type": ITEM_TYPE_ENTRY, "filename": f.name})
    
    items.sort(key=lambda x: x['filename'], reverse=changelog_order)
    
    total_before_limit = len(items)
    
    # Apply limit if specified (take most recent)
    if limit and limit > 0:
        # Most recent are at the end if not changelog_order, at start if changelog_order
        if changelog_order:
            items = items[:limit]
        else:
            items = items[-limit:]
    
    return items, change_log_files, test_result_files, journal_files, total_before_limit

def _generate_obsidian_index(output_folder: str, items: list, verbose: bool = False, current_branch: str = None) -> dict:
    """Generate Obsidian index from items.
    
    Args:
        output_folder: Base output folder
        items: List of items with path, name, type, and filename
        verbose: Print progress messages
        current_branch: Current git branch name
    
    Returns:
        Dict with "obsidian" key pointing to index path
    """
    output_path = Path(output_folder)
    commit_count = sum(1 for item in items if item["type"] == ITEM_TYPE_CHANGELOG)
    test_count = sum(1 for item in items if item["type"] == ITEM_TYPE_TEST)
    entry_count = sum(1 for item in items if item["type"] == ITEM_TYPE_ENTRY)
    
    # Set up Jinja2 for templates
    jinja_env = Environment(loader=FileSystemLoader(_get_templates_dir()))
    
    index_path = output_path / "index.md"
    template = jinja_env.get_template("obsidian_index.md")
    index_content = _clean_markdown(template.render({
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "repo_path": ".",
        "current_branch": current_branch or "unknown",
        "items": items,
        "total_items": len(items),
        "total_commits": commit_count,
        "total_tests": test_count,
        "total_entries": entry_count,
    }))
    
    index_path.write_text(index_content, encoding="utf-8")
    if True or verbose:
        print(f"Updated index: {index_path}")
    
    return {"obsidian": str(index_path)}

def _generate_devlog(output_folder: str, items: list, verbose: bool = False, current_branch: str = None) -> dict:
    """Generate devlog markdown from items.
    
    Args:
        output_folder: Base output folder
        items: List of items with path, name, type, and filename
        verbose: Print progress messages
        current_branch: Current git branch name
    
    Returns:
        Dict with "devlog" key pointing to devlog path
    """
    output_path = Path(output_folder)
    commit_count = sum(1 for item in items if item["type"] == ITEM_TYPE_CHANGELOG)
    test_count = sum(1 for item in items if item["type"] == ITEM_TYPE_TEST)
    entry_count = sum(1 for item in items if item["type"] == ITEM_TYPE_ENTRY)
    
    header_lines = [
        "# Devlog",
        "",
        datetime.now().strftime("Generated: %Y-%m-%d %H:%M:%S"),
        f"Branch: {current_branch or 'unknown'}",
        f"Items: {len(items)} ({commit_count} commits, {test_count} tests, {entry_count} entries)",
        "",
    ]
    
    segments = []
    for item in items:
        entry_path = output_path / item["path"]
        try:
            entry_text = entry_path.read_text(encoding="utf-8").strip()
            segments.append(entry_text)
        except FileNotFoundError:
            if verbose:
                print(f"Missing item skipped: {entry_path}")
    
    devlog_body = "\n\n---\n\n".join(segments)
    full_devlog = _clean_markdown("\n".join(header_lines + ([devlog_body] if devlog_body else [])))
    
    devlog_path = output_path / "devlog.md"
    devlog_path.write_text(full_devlog, encoding="utf-8")
    if verbose:
        print(f"Built devlog: {devlog_path}")
    
    return {"devlog": str(devlog_path)}

def _generate_docx(devlog_md_path: str, output_path: str = None, verbose: bool = False, render_code_as_images: bool = False, repo_path: str = ".") -> dict:
    """Convert devlog markdown to docx using our custom converter.
    
    Args:
        devlog_md_path: Path to devlog.md file
        output_path: Output path for docx file (defaults to devlog.docx in same dir as md)
        verbose: Print progress messages
        render_code_as_images: If True, render code blocks as images using HCTI API or local Playwright
        repo_path: Repository path for loading HCTI credentials from config
    
    Returns:
        Dict with "docx" key pointing to docx path, or empty dict if conversion failed
    """
    if output_path is None:
        md_path = Path(devlog_md_path)
        output_path = str(md_path.parent / "devlog.docx")
    
    try:
        try:
            from lumpy_log.md_to_docx import markdown_file_to_docx
        except ImportError as ie:
            msg = (
                "Optional dependencies for docx playwright offline image generation are not installed.\n"
                "  pip install lumpy-log[docx-playwright] # docx export with code-as-image\n"
                "See README.md or pyproject.toml for details.\n"
            )
            if verbose:
                print(msg)
            else:
                print("Docx playwright offline image generation requires optional dependencies. Run with --verbose for details.")
            return {}

        # Get HCTI credentials from config or environment
        hcti_creds = get_hcti_credentials(repo_path)
        hcti_user_id = hcti_creds.get('user_id')
        hcti_api_key = hcti_creds.get('api_key')

        if verbose and hcti_creds:
            print(f"Using HCTI credentials from {hcti_creds.get('source', 'unknown')}")

        success = markdown_file_to_docx(
            str(devlog_md_path), 
            str(output_path), 
            render_code_as_images,
            hcti_user_id=hcti_user_id,
            hcti_api_key=hcti_api_key
        )
        if success:
            if verbose:
                print(f"Built docx: {output_path}")
            return {"docx": str(output_path)}
        else:
            if verbose:
                print(f"Warning: docx conversion failed")
            return {}
    except Exception as e:
        if verbose:
            error_type = type(e).__name__
            print(f"Warning: docx conversion failed ({error_type}): {e}")
        return {}

def _rebuild_index(
    output_folder: str,
    verbose: bool = False,
    changelog_order: bool = False,
    output_formats: list = None,
    current_branch: str = None,
    limit: int = None,
    repo_path: str = ".",
):
    """Rebuild the unified index with commits and tests interleaved by time.

    Args:
        output_folder: Base output folder containing commits/ and tests/
        verbose: Print progress messages
        changelog_order: If True, sort newest first. If False (default), oldest first
        output_formats: List of output formats (e.g., ["obsidian", "devlog", "docx"])
        current_branch: Current git branch name
        limit: If specified, limit to N most recent entries
        repo_path: Repository path for loading HCTI credentials from config
    """
    if output_formats is None:
        output_formats = ["obsidian"]
    
    results = {}
    
    if True or verbose:
        print(f"Rebuilding index with formats: {output_formats}")
    
    # Collect items
    items, commit_files, test_files, entry_files, total_before_limit = _collect_items(output_folder, changelog_order, limit)
    
    if verbose and limit and total_before_limit > len(items):
        print(f"Limited to {len(items)} most recent entries (out of {total_before_limit} total)")
    
    # Generate obsidian index
    if "obsidian" in output_formats:
        results.update(_generate_obsidian_index(output_folder, items, verbose, current_branch))
    
    # Generate devlog and/or docx
    if "devlog" in output_formats or "docx" in output_formats:
        devlog_result = _generate_devlog(output_folder, items, verbose, current_branch)
        results.update(devlog_result)
        devlog_path = devlog_result.get("devlog")
        
        if "docx" in output_formats and devlog_path:
            # Check if code-as-images rendering should be enabled
            from .config import get_config_value
            render_code_as_images = get_config_value('render_code_as_images', {}, repo_path, False)
            if verbose and render_code_as_images:
                hcti_creds = get_hcti_credentials(repo_path)
                if hcti_creds:
                    print(f"Code-as-images: HCTI API (from {hcti_creds.get('source')})")
                else:
                    print("Code-as-images: Playwright (local rendering)")
            docx_result = _generate_docx(devlog_path, verbose=verbose, render_code_as_images=render_code_as_images, repo_path=repo_path)
            results.update(docx_result)
            
            # Clean up devlog.md if only docx was requested
            if "devlog" not in output_formats and docx_result:
                Path(devlog_path).unlink(missing_ok=True)
    
    return results

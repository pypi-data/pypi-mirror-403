#!/usr/bin/python3

import yaml
from jinja2 import Environment, FileSystemLoader
from genericpath import exists
from re import split, sub
import sys, os
import pathspec
from pydriller import Repository
from .changelump import ChangeLump
from .languages import Languages
from .test_processor import TestProcessor
from .utils import _get_templates_dir, _format_markdown, _rebuild_index
from .config import get_output_format, get_config_value, print_active_config
from . import OUTPUT_CHANGELOGS_DIR

languages = Languages(os.path.join(os.path.dirname(os.path.abspath(__file__)), "languages.yml"))

jinja_env = Environment(loader=FileSystemLoader(_get_templates_dir()))
tCommit = jinja_env.get_template("commit_entry.md")
tModifiedFiles = jinja_env.get_template("modified_files.md")
tObsidianIndex = jinja_env.get_template("obsidian_index.md")


change_verbs_past = {
    "ADD" : "Added",
    "COPY" : "Copied",
    "RENAME" : "Renamed",
    "DELETE" : "Removed",
    "MODIFY" : "Modified",
    "UNKNOWN" : "Unknown"
}

def _load_lumpy_ignore(repo_path: str):
    """Load .lumpyignore patterns (gitignore-style), with built-in defaults.

    Built-in defaults: ignore Markdown files ("*.md").
    """
    default_patterns = ["*.md"]
    ignore_file = os.path.join(repo_path, ".lumpyignore")

    patterns = list(default_patterns)
    if os.path.isfile(ignore_file):
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                # PathSpec.from_lines handles comments; keep non-empty lines
                file_lines = [line.rstrip("\n") for line in f.readlines()]
                patterns.extend([l for l in file_lines if l.strip() != ""])
        except Exception as e:
            # Fail soft: proceed with defaults if file can't be read
            if __name__ == "__main__" or os.environ.get("LUMPY_LOG_VERBOSE_ERRORS"):
                print(f"Warning: could not read .lumpyignore: {e}")

    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def main(args):
    # Show active configuration if verbose
    repo_path = args.get('repo', '.')
    verbose = get_config_value('verbose', args, repo_path, False)
    outputfolder = get_config_value('outputfolder', args, repo_path, 'devlog')

    # Show active configuration if verbose
    if verbose:
        print_active_config(args, repo_path)

    kwargs = {}
    for param in args.keys():
        if not param in [
            "dryrun",
            "outputfolder",
            "force",
            "verbose",
            "repo",
            "single_file",
            "devlog",
            "command",
            "input",
            "HCTI_API_USER_ID",
            "HCTI_API_KEY",
            "limit",  # limit is for index generation, not pydriller
        ]:
            if args[param]:
                kwargs[param] = args[param]

    # Only create the output directory when not a dry run
    if not args.get('dryrun'):
        if not exists(outputfolder):
            os.makedirs(outputfolder)
        # Create change_logs subdirectory
        change_logs_dir = os.path.join(outputfolder, OUTPUT_CHANGELOGS_DIR)
        if not exists(change_logs_dir):
            os.makedirs(change_logs_dir)

    commits = []

    #print("args", args)
    #return

    # Build ignore spec once per run
    ignore_spec = _load_lumpy_ignore(repo_path)
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
    
    # Report branch processing info if verbose
    if True or verbose:
        print(f"Processing current branch: {current_branch}")
    
    for commit in Repository(repo_path, **kwargs).traverse_commits():
        if commit.in_main_branch:
            genfilename = commit.author_date.strftime("%Y%m%d_%H%M")+"_"+commit.hash[:7]
            change_logs_dir = os.path.join(outputfolder, OUTPUT_CHANGELOGS_DIR)
            genfilepath = os.path.join(change_logs_dir, genfilename+".md")
            
            if(args["force"] or not os.path.exists(genfilepath)):
                if verbose:
                    print("Making", genfilepath)
                newcommit = {
                    "hash":commit.hash,
                    "msg":commit.msg,
                    "author":commit.author.name,
                    "date":commit.author_date.strftime("%Y-%m-%d"),
                    "name": genfilename,
                    "author_date":commit.author_date,
                    "modifications":[],
                }
                newcommit["markdown"] = tCommit.render(newcommit)
                        
                if hasattr(commit, "modified_files"):
                    for m in commit.modified_files:
                        # Skip files that match .lumpyignore patterns
                        try:
                            if ignore_spec and ignore_spec.match_file(m.filename):
                                if verbose:
                                    print(f"Ignoring per .lumpyignore: {m.filename}")
                                continue
                        except Exception:
                            # If matching fails for any reason, do not block processing
                            pass
                        filename, file_extension = os.path.splitext(m.filename)
                        language = languages.getByExtension(file_extension)
                        change_verb = m.change_type.name[0]+m.change_type.name[1:].lower()
                        
                        newmod = {
                            "filename":m.filename,
                            "change_type":m.change_type.name,
                            "change_verb": change_verb,
                            "change_verb_past": change_verbs_past[m.change_type.name],
                            "code" : [],
                            "lumps": [],
                            "language": language.mdname,
                            "source":""
                        }
                                            
                        if m.filename.lower().endswith(('.png', '.jpg', '.jpeg', 'gif')) == False:                    
                            if m.change_type.name == "ADD":
                                newmod["code"].append(m.source_code)
                                
                            if m.change_type.name == "MODIFY":
                                lines = str.splitlines(m.source_code)
                                    
                                if False and verbose:
                                    print ("m.changed_methods", m.changed_methods)
                                if (len(m.changed_methods)):
                                    for c in m.changed_methods:
                                        newfunc = c.__dict__
                                        lump = ChangeLump(language, lines, func=c.__dict__, verbose=verbose)
                                        lump.extendOverComments()
                                        newfunccode = lump.code
                                        newmod["source"] = "changed_methods"
                                        newmod["code"].append(newfunccode)
                                        newmod["lumps"].append(lump)
                                else:
                                    if False and verbose:
                                        print ("Change m", m.diff_parsed)
                                    
                                    newmod["source"] = "line change"
                                    
                                    lump = None
                                    lumps = []
                                    for (linenum, linetext) in m.diff_parsed["added"]:
                                        if lump is None:
                                            lump = ChangeLump(language, lines, start=linenum, verbose=verbose)
                                            lump.extendOverText()
                                            lumps.append(lump)    
                                        if(not lump.inLump(linenum-1)):
                                            lump = ChangeLump(language, lines, start=linenum, verbose=verbose)
                                            lump.extendOverText()
                                            lumps.append(lump)
                                    
                                    for lump in lumps:
                                        if False and verbose:
                                            print("lump.code", lump.code)
                                        newmod["code"].append(lump.code)
                                        newmod["lumps"].append(lump)
                                    
                                    #newmod["code"].append(m.source_code)

                            newcommit["markdown"] += "\n\n" + tModifiedFiles.render(newmod)
                            
                        newcommit["modifications"].append(newmod)
                
                # Normalize whitespace before saving
                newcommit["markdown"] = _format_markdown(newcommit["markdown"])
                
                # Write the commit file to disk (unless dry run)
                if not args.get("dryrun"):
                    with open(genfilepath, "w", encoding="utf-8") as f:
                        f.write(newcommit["markdown"])
                    if verbose:
                        print(f"Wrote {genfilepath}")
                
                commits.append(newcommit)
    
    # Rebuild index after processing commits

    if not args["dryrun"]:
        _rebuild_index(
                        outputfolder,
                        verbose=verbose,
                        output_formats=output_formats,
                        current_branch=current_branch,
                        limit=get_config_value("limit", args, repo_path, None),
                        repo_path=repo_path,
        )



# Lumpy Log - Prettified Git Logs

Make git change logs super readable and combine then with test results and journal entries for the ultimate devlog. Great for use in scenarios when communicating the progress of a project to non-experts.

## Features

- Generates readable markdown reports from Git commit history
- Processes test output (TAP format) and creates test documentation
- Generates blank journal entries or joins up with Obsidian Daily Notes, so you write about the progress & document the dev process
- Multi-folder organization with unified index
- Allows you to edit the files and regenerate the output (as an Obsidian index page, complete devlog.md, or a .docx file)

📚 **See Also:**

- [Obsidian Integration Guide](OBSIDIAN.md) - Detailed guide for using with Obsidian

## Installation

### From PyPI

```bash
pip install lumpy-log
```

For code-as-image rendering in DOCX output, install the optional Playwright dependency:

```bash
pip install lumpy-log[docx-playwright]
playwright install chromium
```

See [CODE_AS_IMAGE.md](CODE_AS_IMAGE.md) for full setup and usage instructions.

## Usage

### Create / Update Your Development Log
#### Typical usage : documenting a python project on linux

```bash
# Process the git commits in this branch
lumpy-log

# run pytest on your code and it to the devlog
pytest --tap | lumpy-log test 

# Add a new dev journal entry
lumpy-log journal
```

### As a Python Module

You can also run it as a module if you can't install it in the PATH:

```bash
python -m lumpy_log
```

### Configuration File

Lumpy Log supports configuration via a `.lumpyconfig.yml` file in your repository root.

#### Quick Start

Create a `.lumpyconfig.yml` file:

```yaml
# Output format(s)
output_format:
  - obsidian # a single index.md that includes the file for each entry by filename
  # - devlog # a single devlog.md that include the content of all the entries
  # - docx # a devlog.docx file that includes all the content of all the entries (require optional install)

# Enable verbose output
verbose: true

# Limit to recent entries (optional)
# limit: 10
```

All the details are documented in [CONFIG](CONFIG.md)

### Command-line Options

#### Common Options

- `-o, --outputfolder`: Output folder for all dev log entries (default: devlog/)
- `-v, --verbose`: Verbose output
- `--limit`: Limit index/devlog to N most recent entries
- `--output-format`: Output format(s) (overrides .lumpyconfig.yml)
- `--changelog`: Use changelog order (newest first) instead of default (oldest first)

#### Changes Command (Commit Logs)

```bash
lumpy-log
lumpy-log changes
```

- `-i, --repo`: Path to the local Git repository (default: current directory)
- `-f, --fromcommit`: Start from this commit

```bash
pytest --tap | lumpy-log test 
```

Detailed instruction for many languages are found in [TESTING_COMMANDS](TESTING_COMMANDS.md)

- `--input`: Input file with test output (if not specified, reads from stdin)
lumpy-log journal
```

- `-t, --title`: Title to place in the log entry
- `-f, --filename`: Optional filename for the log entry (default: YYYYMMDD.md)

#### Rebuild Command (Regenerate Index)

Rebuilds the unified `index.md` from existing logs, change logs, and test results without re-processing git history or re-running tests. Only has the common options.

```bash

# Process the change logs for the current directory repository
lumpy-log

# Process the change logs for the current directory repository
# Process a specific repository
lumpy-log changes -i /path/to/repo

# Process with options
lumpy-log changes -i /path/to/repo -o devlog --verbose --force
```

### Process Test Results

Lumpy Log can process test output in TAP (Test Anything Protocol) format and create markdown documentation alongside your commit logs.

Detailed instruction for many languages are found in [TESTING_COMMANDS](TESTING_COMMANDS.md)

**Install pytest-tap plugin:**

```bash
pip install pytest-tap
```

**Bash/Linux/macOS:**

```bash
# Pipe test output directly
pytest --tap | lumpy-log test

# Or save to file first
pytest --tap > test_output.txt
lumpy-log test --input test_output.txt
```

**Windows cmd.exe or PowerShell:**

```cmd
REM Pipe test output directly
py -m pytest --tap | lumpy-log test

REM Or save to file first
py -m pytest --tap > test_output.txt
lumpy-log test --input test_output.txt

REM Include raw output for debugging
py -m pytest --tap | lumpy-log test --raw-output
```

Test results are saved to `output/tests/` with timestamp filenames (e.g., `20260118_1430.md`), and the index is automatically updated to include both commits and test results.

## Output Structure

Lumpy Log organizes output into subdirectories:

devlog/
├── journal/         # Journal entries (from `lumpy-log journal`)
├── change_logs/     # Commit logs (from `lumpy-log changes`)
├── test_results/    # Test result markdown files (from `lumpy-log test`)
├── index.md         # Unified index in Obsidian format (optional / default)
├── devlog.md        # All the entries rendered fully into .md (optional)
└── devlog.docx      # All the entries rendered fully into .docx (optional)

### Ignoring Files (.lumpyignore)

Lumpy Log respects a repository-level `.lumpyignore` file using the same syntax as `.gitignore` (git wildmatch patterns). By default, it ignores Markdown files (`*.md`) so documentation changes don't flood the logs. Add additional patterns to `.lumpyignore` at your repo root to skip files or folders.

Example `.lumpyignore`:

```gitignore
# Ignore Markdown (default)
*.md

# Ignore generated docs and build artifacts
docs/
dist/
*.tmp
```

## Developing Lumpy Log

- [Development Guide](DEVELOPMENT.md) - For contributors and developers
- [Publishing Guide](PUBLISHING.md) - How to publish to PyPI


# Example Output

## Commit : Refactor verbose logging conditions in ChangeLump methods for clarity

By "Mr Eggleton" on 2026-01-18

### "changelump.py" was Modified

```python
    # Abstracts out lineIsComment so we can  print the results
    def _lineIsComment(self, i):
            print(self.lang.name, "self.lang.comment_structure",self.lang.comment_structure)
        comment_structure = self.lang.comment_structure

        begin = comment_structure.get("begin")
        end = comment_structure.get("end")
        single = comment_structure.get("single")

        # Multiline comments: treat lines with both begin and end as comment,
        # and any line inside unmatched begin/end pairs as comment.
        if begin:
            try:
                beginmatches = re.findall(begin, line)
                endmatches = re.findall(end, line)

                # If both markers appear on the same line, it's a comment line.
                if len(beginmatches) and len(endmatches):
                    return True
                
                # If this line is inside an open multiline comment, it's a comment.
                if self._in_multiline_comment(i, begin, end):
                    return True
            except Exception as Err:
                print(type(Err), Err)
                print(self.lang.comment_family, comment_structure)

        # Single-line comments
        if single:
            try:
                if re.search(single, line.strip()):
                    return True
            except Exception as Err:
                print("Single", type(Err), Err)
                print(self.lang.comment_family, comment_structure["single"])

        return False

```

```python
    @property
    def code(self):    
        start = self.start 
        if(self.commentStart is not None):
            start = self.commentStart     

        #code = ""self.source+"\n"+
        code = ("\n".join(self.lines[start: self.end+1]))
        if self.verbose:
            print("code", code)
        return code
```

```python
    def extendOverComments(self):
        if self.verbose:
            print("extendOverComments", "self.start", self.start)
        j = self.start
        while(j > 0 and self.lineIsComment(j-1)):
            j -= 1
            self.commentStart = j
```

```python
    def lineIsComment(self, i):
        blineIsComment = self._lineIsComment(i)
        if self.verbose:
            print("lineIsComment", blineIsComment, self.lines[i])
        return blineIsComment
```

```python
    def inLump(self,i):
        inLump = (self.start <= i and i <= self.end)
    
        if self.verbose:
            print("inLump", "self.start", self.start,"i", i, "inLump",inLump)
        return inLump
```

```python
        """Return True if line i is inside an unmatched multiline comment block."""
        try:
            # Check if begin and end delimiters are the same (symmetric like """)
            # Strip common regex anchors to compare the actual delimiter strings
            begin_stripped = begin_re.strip('^$\\s')
            end_stripped = end_re.strip('^$\\s')
            symmetric = (begin_stripped == end_stripped)
            
            in_comment = False
            for idx in range(0, i + 1):
                s = self.lines[idx]
                
                if symmetric:
                    # For symmetric delimiters (like """ in Python), each occurrence
                    # toggles the comment state: first one opens, second one closes, etc.
                    # Example: """comment""" means we enter on first """, exit on second
                    matches = re.findall(begin_re, s)
                    for _ in matches:
                        in_comment = not in_comment  # Flip True->False or False->True
                else:
                    # For asymmetric delimiters, track depth
                    begins = len(re.findall(begin_re, s))
                    ends = len(re.findall(end_re, s))
                    
                    # Process begins first, then ends
                    if not in_comment and begins > 0:
                        in_comment = True
                    if in_comment and ends > 0:
                        in_comment = False
                    
            
            return in_comment
        except Exception as Err:
            if self.verbose:
                print("_in_multiline_comment error", type(Err), Err)
            return False

```

## Test Results : 2026-01-20 13:30:12

- **Tests Run:** 113
- **Passed:** 113 ✅
- **Failed:** 0 
- **Skipped:** 0

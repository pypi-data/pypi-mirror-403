"""
Insert abstract role - ensures AsciiDoc files have [role="_abstract"] above the first paragraph.

Core logic for adding the [role="_abstract"] attribute required for DITA short description conversion.
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional


def find_first_paragraph_after_title(lines: List[str]) -> Optional[int]:
    """
    Find the line index of the first paragraph after the document title.

    The first paragraph is the first non-empty line that:
    - Comes after a level 1 heading (= Title)
    - Is not an attribute definition (starts with :)
    - Is not a comment (starts with //)
    - Is not a block attribute (starts with [)
    - Is not another heading

    Args:
        lines: List of lines from the file (without trailing newlines)

    Returns:
        Line index of the first paragraph, or None if not found
    """
    title_found = False
    title_index = -1

    for i, line in enumerate(lines):
        # Check for level 1 heading (document title)
        if re.match(r'^=\s+[^=]', line):
            title_found = True
            title_index = i
            continue

        # Only look for first paragraph after we've found the title
        if not title_found:
            continue

        # Skip empty lines
        if re.match(r'^\s*$', line):
            continue

        # Skip attribute definitions
        if re.match(r'^:', line):
            continue

        # Skip comments (single line)
        if re.match(r'^//', line):
            continue

        # Skip block attributes like [role=...], [id=...], etc.
        if re.match(r'^\[', line):
            continue

        # Skip other headings
        if re.match(r'^=+\s+', line):
            continue

        # Skip include directives
        if re.match(r'^include::', line):
            continue

        # This is the first paragraph
        return i

    return None


def has_abstract_role(lines: List[str], paragraph_index: int) -> bool:
    """
    Check if there's already a [role="_abstract"] before the paragraph.

    Args:
        lines: List of lines from the file
        paragraph_index: Index of the first paragraph

    Returns:
        True if [role="_abstract"] already exists before the paragraph
    """
    # Look at the lines immediately before the paragraph
    for i in range(paragraph_index - 1, -1, -1):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            continue

        # Found abstract role
        if re.match(r'^\[role=["\']_abstract["\']\]$', line):
            return True

        # If we hit any other non-empty content, stop looking
        # (could be attribute, heading, etc.)
        break

    return False


def process_file(file_path: Path, dry_run: bool = False, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Process a single AsciiDoc file to add [role="_abstract"] if needed.

    Args:
        file_path: Path to the file to process
        dry_run: If True, show what would be changed without modifying
        verbose: If True, show detailed output

    Returns:
        Tuple of (changes_made, messages) where messages is a list of verbose output
    """
    messages = []

    if verbose:
        messages.append(f"Processing: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (IOError, UnicodeDecodeError) as e:
        raise IOError(f"Error reading {file_path}: {e}")

    # Remove trailing newlines from lines for processing
    lines = [line.rstrip('\n\r') for line in lines]

    # Find the first paragraph after the title
    paragraph_index = find_first_paragraph_after_title(lines)

    if paragraph_index is None:
        if verbose:
            messages.append("  No paragraph found after title")
        return False, messages

    # Check if abstract role already exists
    if has_abstract_role(lines, paragraph_index):
        if verbose:
            messages.append("  [role=\"_abstract\"] already present")
        return False, messages

    # Insert [role="_abstract"] before the first paragraph
    # We need to add it with a blank line before it if there isn't one
    new_lines = lines[:paragraph_index]

    # Check if we need to add a blank line before the role
    if paragraph_index > 0 and lines[paragraph_index - 1].strip():
        new_lines.append('')

    new_lines.append('[role="_abstract"]')
    new_lines.extend(lines[paragraph_index:])

    if verbose:
        preview = lines[paragraph_index][:60] + "..." if len(lines[paragraph_index]) > 60 else lines[paragraph_index]
        messages.append(f"  Adding [role=\"_abstract\"] before line {paragraph_index + 1}: {preview}")

    if not dry_run:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for line in new_lines:
                    f.write(line + '\n')
        except IOError as e:
            raise IOError(f"Error writing {file_path}: {e}")

    return True, messages


def find_adoc_files(path: Path, exclude_dirs: List[str] = None, exclude_files: List[str] = None) -> List[Path]:
    """
    Find all .adoc files in the given path.

    Args:
        path: File or directory path to search
        exclude_dirs: List of directory paths to exclude
        exclude_files: List of file paths to exclude

    Returns:
        List of Path objects for .adoc files
    """
    exclude_dirs = exclude_dirs or []
    exclude_files = exclude_files or []

    # Normalize exclusion paths to absolute
    exclude_dirs_abs = [Path(d).resolve() for d in exclude_dirs]
    exclude_files_abs = [Path(f).resolve() for f in exclude_files]

    adoc_files = []

    if path.is_file():
        if path.suffix == '.adoc':
            path_abs = path.resolve()
            if path_abs not in exclude_files_abs:
                adoc_files.append(path)
    elif path.is_dir():
        for adoc_path in path.rglob('*.adoc'):
            # Skip symlinks
            if adoc_path.is_symlink():
                continue

            path_abs = adoc_path.resolve()

            # Check if file is excluded
            if path_abs in exclude_files_abs:
                continue

            # Check if any parent directory is excluded
            skip = False
            for exclude_dir in exclude_dirs_abs:
                try:
                    path_abs.relative_to(exclude_dir)
                    skip = True
                    break
                except ValueError:
                    pass

            if not skip:
                adoc_files.append(adoc_path)

    return sorted(adoc_files)

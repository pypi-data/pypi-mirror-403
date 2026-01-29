"""
Core logic for finding AsciiDoc files that are included more than once.

Scans AsciiDoc files for include:: macros and identifies files that are
included from multiple locations, which may indicate opportunities for
content reuse or potential maintenance issues.
"""

import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


INCLUDE_PATTERN = re.compile(r'^include::([^\[]+)\[', re.MULTILINE)

# Files commonly expected to be included in multiple places
DEFAULT_COMMON_INCLUDES = {
    'attributes.adoc',
    'common/attributes.adoc',
    'common/revision-info.adoc',
    '_attributes.adoc',
}

# Default directories to exclude
DEFAULT_EXCLUDE_DIRS = {'.git', '.archive', 'target', 'build', 'node_modules'}


@dataclass
class IncludeLocation:
    """Represents where an include was found."""
    source_file: str
    line_number: int
    raw_include_path: str


@dataclass
class DuplicateInclude:
    """Represents a file that is included multiple times."""
    resolved_path: str
    locations: list[IncludeLocation] = field(default_factory=list)
    is_common: bool = False

    @property
    def count(self) -> int:
        return len(self.locations)


def find_includes_in_file(file_path: str) -> list[tuple[str, int]]:
    """
    Extract all include:: targets from an AsciiDoc file.

    Returns list of (include_target, line_number) tuples.
    """
    includes = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                match = re.match(r'^include::([^\[]+)\[', line)
                if match:
                    includes.append((match.group(1), line_num))
    except (IOError, UnicodeDecodeError) as e:
        print(f"Warning: Could not read {file_path}: {e}")
    return includes


def resolve_include_path(include_target: str, source_file: str, base_dir: str) -> str:
    """
    Resolve an include target to a normalized path relative to base directory.
    """
    source_dir = os.path.dirname(source_file)

    # Resolve the path relative to source file's directory
    if include_target.startswith('../') or include_target.startswith('./'):
        resolved = os.path.normpath(os.path.join(source_dir, include_target))
    else:
        resolved = os.path.normpath(os.path.join(source_dir, include_target))

    # Make relative to base directory if possible
    try:
        resolved = os.path.relpath(resolved, base_dir)
    except ValueError:
        pass  # Keep absolute path if on different drive (Windows)

    return resolved


def is_common_include(path: str, common_includes: set[str]) -> bool:
    """Check if a path matches a common include pattern."""
    basename = os.path.basename(path)
    return path in common_includes or basename in common_includes


def collect_adoc_files(
    directory: str,
    exclude_dirs: set[str] | None = None,
    exclude_files: set[str] | None = None
) -> list[str]:
    """
    Collect all .adoc files in a directory recursively.

    Args:
        directory: Base directory to scan
        exclude_dirs: Directory names to exclude
        exclude_files: File names or paths to exclude

    Returns:
        List of absolute paths to .adoc files
    """
    exclude_dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS
    exclude_files = exclude_files or set()

    adoc_files = []
    base_path = os.path.abspath(directory)

    for root, dirs, files in os.walk(base_path, followlinks=False):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for filename in files:
            if not filename.endswith('.adoc'):
                continue

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, base_path)

            # Check exclusions
            if filename in exclude_files or rel_path in exclude_files:
                continue

            adoc_files.append(filepath)

    return sorted(adoc_files)


def find_duplicate_includes(
    directory: str,
    exclude_dirs: set[str] | None = None,
    exclude_files: set[str] | None = None,
    include_common: bool = False,
    common_includes: set[str] | None = None
) -> tuple[list[DuplicateInclude], int, int]:
    """
    Find all files that are included more than once.

    Args:
        directory: Base directory to scan
        exclude_dirs: Directory names to exclude
        exclude_files: File names or paths to exclude
        include_common: If True, include common files in results
        common_includes: Set of paths considered "common" (expected duplicates)

    Returns:
        Tuple of (duplicates, total_files_scanned, excluded_common_count)
    """
    if common_includes is None:
        common_includes = DEFAULT_COMMON_INCLUDES

    # Collect all .adoc files
    adoc_files = collect_adoc_files(directory, exclude_dirs, exclude_files)
    base_dir = os.path.abspath(directory)

    # Track includes: {resolved_path: [IncludeLocation, ...]}
    include_map: dict[str, list[IncludeLocation]] = defaultdict(list)

    for source_file in adoc_files:
        includes = find_includes_in_file(source_file)
        for include_target, line_num in includes:
            resolved = resolve_include_path(include_target, source_file, base_dir)
            rel_source = os.path.relpath(source_file, base_dir)

            include_map[resolved].append(IncludeLocation(
                source_file=rel_source,
                line_number=line_num,
                raw_include_path=include_target
            ))

    # Find duplicates
    duplicates = []
    excluded_common_count = 0

    for path, locations in include_map.items():
        if len(locations) <= 1:
            continue

        is_common = is_common_include(path, common_includes)

        if is_common and not include_common:
            excluded_common_count += 1
            continue

        duplicates.append(DuplicateInclude(
            resolved_path=path,
            locations=locations,
            is_common=is_common
        ))

    # Sort by count descending
    duplicates.sort(key=lambda d: d.count, reverse=True)

    return duplicates, len(adoc_files), excluded_common_count


def format_txt_report(
    duplicates: list[DuplicateInclude],
    total_files: int,
    excluded_common: int,
    directory: str,
    cmd_line: str
) -> str:
    """Format results as plain text."""
    lines = []

    lines.append(f"Command: {cmd_line}")
    lines.append(f"Directory: {os.path.abspath(directory)}")
    lines.append(f"Files scanned: {total_files}")
    lines.append("")

    if not duplicates:
        if excluded_common:
            lines.append(f"No unexpected duplicates found ({excluded_common} common files excluded).")
            lines.append("Use --include-common to see all duplicates.")
        else:
            lines.append("No files are included more than once.")
        return '\n'.join(lines)

    lines.append(f"Found {len(duplicates)} files included more than once:")
    if excluded_common:
        lines.append(f"  ({excluded_common} common files excluded; use --include-common to see all)")
    lines.append("")
    lines.append("=" * 70)

    for i, dup in enumerate(duplicates, 1):
        common_marker = " [COMMON]" if dup.is_common else ""
        lines.append(f"\n[{i}] {dup.resolved_path}{common_marker}")
        lines.append(f"    Included {dup.count} times:")
        lines.append("-" * 50)

        for loc in dup.locations:
            lines.append(f"    - {loc.source_file}:{loc.line_number}")

    return '\n'.join(lines)


def format_csv_report(
    duplicates: list[DuplicateInclude],
    total_files: int,
    excluded_common: int,
    directory: str,
    cmd_line: str
) -> str:
    """Format results as CSV."""
    lines = []
    lines.append("Included File,Inclusion Count,Is Common,Source File,Line Number,Raw Include Path")

    for dup in duplicates:
        for loc in dup.locations:
            lines.append(
                f'"{dup.resolved_path}",{dup.count},{dup.is_common},'
                f'"{loc.source_file}",{loc.line_number},"{loc.raw_include_path}"'
            )

    return '\n'.join(lines)


def format_json_report(
    duplicates: list[DuplicateInclude],
    total_files: int,
    excluded_common: int,
    directory: str,
    cmd_line: str
) -> str:
    """Format results as JSON."""
    import json

    data = {
        "command": cmd_line,
        "directory": os.path.abspath(directory),
        "files_scanned": total_files,
        "excluded_common_count": excluded_common,
        "duplicate_count": len(duplicates),
        "duplicates": [
            {
                "path": dup.resolved_path,
                "count": dup.count,
                "is_common": dup.is_common,
                "locations": [
                    {
                        "source_file": loc.source_file,
                        "line_number": loc.line_number,
                        "raw_include_path": loc.raw_include_path
                    }
                    for loc in dup.locations
                ]
            }
            for dup in duplicates
        ]
    }

    return json.dumps(data, indent=2)


def format_md_report(
    duplicates: list[DuplicateInclude],
    total_files: int,
    excluded_common: int,
    directory: str,
    cmd_line: str
) -> str:
    """Format results as Markdown."""
    lines = []

    lines.append("# Duplicate Includes Report")
    lines.append("")
    lines.append(f"**Command:** `{cmd_line}`")
    lines.append(f"**Directory:** `{os.path.abspath(directory)}`")
    lines.append(f"**Files scanned:** {total_files}")
    lines.append("")

    if not duplicates:
        if excluded_common:
            lines.append(f"No unexpected duplicates found ({excluded_common} common files excluded).")
        else:
            lines.append("No files are included more than once.")
        return '\n'.join(lines)

    lines.append(f"## Summary")
    lines.append("")
    lines.append(f"Found **{len(duplicates)}** files included more than once.")
    if excluded_common:
        lines.append(f"({excluded_common} common files excluded)")
    lines.append("")

    for i, dup in enumerate(duplicates, 1):
        common_marker = " *(common)*" if dup.is_common else ""
        lines.append(f"### {i}. `{dup.resolved_path}`{common_marker}")
        lines.append("")
        lines.append(f"Included **{dup.count}** times:")
        lines.append("")

        for loc in dup.locations:
            lines.append(f"- `{loc.source_file}:{loc.line_number}`")

        lines.append("")

    return '\n'.join(lines)

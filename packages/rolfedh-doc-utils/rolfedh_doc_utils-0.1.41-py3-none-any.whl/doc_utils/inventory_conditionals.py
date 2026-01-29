"""
Module for inventorying AsciiDoc conditional directives.

Functions:
- find_adoc_files: Recursively find all .adoc files in a directory.
- scan_file_for_conditionals: Scan a file for conditional directives.
- create_inventory: Create an inventory of all conditionals found in .adoc files.
"""

import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, Dict, Set


# Pattern to match AsciiDoc conditionals
CONDITIONAL_PATTERN = re.compile(
    r'^(ifdef|ifndef|endif|ifeval)::(.*)$',
    re.MULTILINE
)


def find_adoc_files(directory: Path) -> List[Path]:
    """Find all .adoc files in the given directory recursively."""
    return sorted(directory.rglob('*.adoc'))


def scan_file_for_conditionals(filepath: Path) -> List[Tuple[int, str, str]]:
    """
    Scan a file for conditional directives.

    Args:
        filepath: Path to the .adoc file to scan.

    Returns:
        A list of tuples: (line_number, directive_type, condition)
    """
    results = []
    try:
        content = filepath.read_text(encoding='utf-8')
        for i, line in enumerate(content.splitlines(), start=1):
            match = CONDITIONAL_PATTERN.match(line.strip())
            if match:
                directive_type = match.group(1)
                condition = match.group(2)
                results.append((i, directive_type, condition))
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
    return results


def create_inventory(directory: Path, output_dir: Path = None) -> Path:
    """
    Create an inventory of all conditionals found in .adoc files.

    Args:
        directory: Directory to scan for .adoc files.
        output_dir: Directory to write the inventory file. Defaults to current directory.

    Returns:
        The path to the created inventory file.
    """
    if output_dir is None:
        output_dir = Path.cwd()

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_file = output_dir / f'inventory-{timestamp}.txt'

    adoc_files = find_adoc_files(directory)

    # Track statistics
    stats: Dict[str, int] = defaultdict(int)
    conditions_used: Dict[str, List[Tuple[Path, int]]] = defaultdict(list)
    total_files_with_conditionals = 0

    lines = []
    lines.append("AsciiDoc Conditionals Inventory")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Directory: {directory.resolve()}")
    lines.append("=" * 80)
    lines.append("")

    for filepath in adoc_files:
        conditionals = scan_file_for_conditionals(filepath)
        if conditionals:
            total_files_with_conditionals += 1
            relative_path = filepath.relative_to(directory)
            lines.append(f"File: {relative_path}")
            lines.append("-" * 60)

            for line_num, directive, condition in conditionals:
                stats[directive] += 1
                # Extract the condition name (before any brackets)
                cond_name = condition.split('[')[0] if condition else '(empty)'
                if directive in ('ifdef', 'ifndef', 'ifeval'):
                    conditions_used[cond_name].append((relative_path, line_num))

                lines.append(f"  Line {line_num:5d}: {directive}::{condition}")

            lines.append("")

    # Add summary section
    lines.append("=" * 80)
    lines.append("SUMMARY")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total .adoc files scanned: {len(adoc_files)}")
    lines.append(f"Files with conditionals: {total_files_with_conditionals}")
    lines.append("")
    lines.append("Directive counts:")
    for directive in sorted(stats.keys()):
        lines.append(f"  {directive}: {stats[directive]}")
    lines.append(f"  Total: {sum(stats.values())}")
    lines.append("")

    # List unique conditions
    lines.append("=" * 80)
    lines.append("UNIQUE CONDITIONS USED")
    lines.append("=" * 80)
    lines.append("")
    for cond in sorted(conditions_used.keys()):
        occurrences = conditions_used[cond]
        lines.append(f"  {cond}: {len(occurrences)} occurrences")

    # Write the inventory file
    output_file.write_text('\n'.join(lines), encoding='utf-8')

    return output_file


def get_inventory_stats(directory: Path) -> Dict:
    """
    Get statistics about conditionals without writing a file.

    Args:
        directory: Directory to scan for .adoc files.

    Returns:
        Dictionary with statistics about conditionals found.
    """
    adoc_files = find_adoc_files(directory)

    stats: Dict[str, int] = defaultdict(int)
    conditions_used: Dict[str, int] = defaultdict(int)
    files_with_conditionals: Set[Path] = set()

    for filepath in adoc_files:
        conditionals = scan_file_for_conditionals(filepath)
        if conditionals:
            files_with_conditionals.add(filepath)
            for line_num, directive, condition in conditionals:
                stats[directive] += 1
                cond_name = condition.split('[')[0] if condition else '(empty)'
                if directive in ('ifdef', 'ifndef', 'ifeval'):
                    conditions_used[cond_name] += 1

    return {
        'total_files': len(adoc_files),
        'files_with_conditionals': len(files_with_conditionals),
        'directive_counts': dict(stats),
        'total_conditionals': sum(stats.values()),
        'unique_conditions': dict(conditions_used),
    }

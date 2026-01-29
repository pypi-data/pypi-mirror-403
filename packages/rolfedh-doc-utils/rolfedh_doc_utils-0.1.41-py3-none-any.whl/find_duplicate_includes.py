#!/usr/bin/env python3
"""
Find AsciiDoc files that are included more than once.

Scans AsciiDoc files for include:: macros and identifies files that are
included from multiple locations, helping identify opportunities for
content reuse or potential maintenance issues.

Usage:
    find-duplicate-includes [directory] [options]
"""

import argparse
import os
import sys
from datetime import datetime

from doc_utils.duplicate_includes import (
    DEFAULT_COMMON_INCLUDES,
    DEFAULT_EXCLUDE_DIRS,
    find_duplicate_includes,
    format_txt_report,
    format_csv_report,
    format_json_report,
    format_md_report,
)


def build_cmd_line(args: argparse.Namespace) -> str:
    """Reconstruct the command line for display."""
    parts = ['find-duplicate-includes']

    if args.directory != '.':
        parts.append(args.directory)

    if args.include_common:
        parts.append('--include-common')

    for d in (args.exclude_dir or []):
        parts.append(f'-e {d}')

    for f in (args.exclude_file or []):
        parts.append(f'--exclude-file {f}')

    if args.format != 'txt':
        parts.append(f'--format {args.format}')

    if args.no_output:
        parts.append('--no-output')

    return ' '.join(parts)


def main():
    parser = argparse.ArgumentParser(
        description='Find AsciiDoc files that are included more than once.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan current directory
  find-duplicate-includes

  # Scan a specific directory
  find-duplicate-includes ./docs

  # Include common files (attributes.adoc, etc.) in results
  find-duplicate-includes --include-common

  # Exclude specific directories
  find-duplicate-includes -e archive -e drafts

  # Generate CSV report
  find-duplicate-includes --format csv

  # Display only, no report file
  find-duplicate-includes --no-output
"""
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--include-common',
        action='store_true',
        help='Include common files (attributes.adoc, etc.) in results'
    )
    parser.add_argument(
        '-e', '--exclude-dir',
        action='append',
        metavar='DIR',
        help='Directory to exclude (can be repeated)'
    )
    parser.add_argument(
        '--exclude-file',
        action='append',
        metavar='FILE',
        help='File to exclude (can be repeated)'
    )
    parser.add_argument(
        '--no-output',
        action='store_true',
        help='Do not write report file (stdout only)'
    )
    parser.add_argument(
        '--format',
        choices=['txt', 'csv', 'json', 'md'],
        default='txt',
        help='Output format (default: txt)'
    )

    args = parser.parse_args()

    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)

    # Build exclusion sets
    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    if args.exclude_dir:
        exclude_dirs.update(args.exclude_dir)

    exclude_files = set()
    if args.exclude_file:
        exclude_files.update(args.exclude_file)

    # Build command line for display
    cmd_line = build_cmd_line(args)

    # Find duplicates
    duplicates, total_files, excluded_common = find_duplicate_includes(
        directory=args.directory,
        exclude_dirs=exclude_dirs,
        exclude_files=exclude_files,
        include_common=args.include_common,
        common_includes=DEFAULT_COMMON_INCLUDES
    )

    # Format report
    formatters = {
        'txt': format_txt_report,
        'csv': format_csv_report,
        'json': format_json_report,
        'md': format_md_report,
    }

    formatter = formatters[args.format]
    report = formatter(duplicates, total_files, excluded_common, args.directory, cmd_line)

    # Output summary to stdout
    if duplicates:
        print(f"\n\u2713 Found {len(duplicates)} files included more than once")
    else:
        if excluded_common:
            print(f"\n\u2713 No unexpected duplicates found ({excluded_common} common files excluded)")
        else:
            print("\n\u2713 No files are included more than once")

    print(f"\nCommand: {cmd_line}")
    print(f"Directory: {os.path.abspath(args.directory)}")
    print(f"Files scanned: {total_files}\n")

    # Print report content
    if args.format == 'txt':
        # Skip header lines already printed
        lines = report.split('\n')
        # Find where the actual results start (after the header)
        start = 0
        for i, line in enumerate(lines):
            if line.startswith('=') or line.startswith('No ') or line.startswith('Found '):
                start = i
                break
        print('\n'.join(lines[start:]))
    else:
        print(report)

    # Write report file
    if not args.no_output and duplicates:
        reports_dir = './reports'
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'{reports_dir}/duplicate-includes_{timestamp}.{args.format}'

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\nReport written to: {filename}")

    return 1 if duplicates else 0


if __name__ == '__main__':
    sys.exit(main())

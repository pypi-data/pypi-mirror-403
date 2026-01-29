"""
Find Duplicate Content in AsciiDoc Files

Scans AsciiDoc files for duplicate and similar content blocks including:
- Recurring notes (NOTE, TIP, WARNING, IMPORTANT, CAUTION)
- Tables
- Step sequences (ordered lists)
- Code blocks

This tool helps identify content that could be refactored into reusable components.
"""

import argparse
import os
import sys
from datetime import datetime
from doc_utils.duplicate_content import (
    find_duplicates,
    format_report,
    generate_csv_report
)
from doc_utils.spinner import Spinner
from doc_utils.version_check import check_version_on_startup
from doc_utils.version import __version__


def main():
    # Check for updates (non-blocking, won't interfere with tool operation)
    check_version_on_startup()

    parser = argparse.ArgumentParser(
        description='Find duplicate and similar content in AsciiDoc files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  find-duplicate-content                     # Scan current directory, write txt report
  find-duplicate-content ./docs              # Scan specific directory
  find-duplicate-content -t note -t table    # Find only notes and tables
  find-duplicate-content -s 0.7              # Include 70%+ similar content
  find-duplicate-content --format csv        # Write CSV report to ./reports/
  find-duplicate-content --no-output         # Display results without saving report
        """
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to scan (default: current directory)'
    )

    parser.add_argument(
        '-t', '--type',
        dest='block_types',
        action='append',
        choices=['note', 'tip', 'warning', 'important', 'caution', 'table', 'steps', 'code'],
        help='Block types to search for (can be specified multiple times). Default: all types'
    )

    parser.add_argument(
        '-s', '--similarity',
        type=float,
        default=0.8,
        metavar='THRESHOLD',
        help='Minimum similarity threshold (0.0-1.0). Default: 0.8'
    )

    parser.add_argument(
        '-m', '--min-length',
        type=int,
        default=50,
        metavar='CHARS',
        help='Minimum content length to consider. Default: 50 characters'
    )

    parser.add_argument(
        '--exact-only',
        action='store_true',
        help='Only find exact duplicates (sets similarity to 1.0)'
    )

    parser.add_argument(
        '-e', '--exclude-dir',
        dest='exclude_dirs',
        action='append',
        default=[],
        metavar='DIR',
        help='Directory to exclude (can be specified multiple times)'
    )

    parser.add_argument(
        '--no-content',
        action='store_true',
        help='Hide content preview in output'
    )

    parser.add_argument(
        '--no-output',
        action='store_true',
        help='Do not write report to ./reports/ directory (report is written by default)'
    )

    parser.add_argument(
        '--format',
        choices=['txt', 'csv', 'json', 'md'],
        default='txt',
        help='Output format (default: txt)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    args = parser.parse_args()

    # Validate arguments
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory")
        return 1

    if args.similarity < 0 or args.similarity > 1:
        print("Error: Similarity threshold must be between 0.0 and 1.0")
        return 1

    # Set up parameters
    similarity = 1.0 if args.exact_only else args.similarity
    exclude_dirs = ['.git', '.archive', 'target', 'build', 'node_modules'] + args.exclude_dirs

    # Build command line options summary
    cmd_options = ['find-duplicate-content']
    if args.directory != '.':
        cmd_options.append(args.directory)
    if args.block_types:
        for bt in args.block_types:
            cmd_options.append(f'-t {bt}')
    if args.exact_only:
        cmd_options.append('--exact-only')
    elif args.similarity != 0.8:
        cmd_options.append(f'-s {args.similarity}')
    if args.min_length != 50:
        cmd_options.append(f'-m {args.min_length}')
    for ed in args.exclude_dirs:
        cmd_options.append(f'-e {ed}')
    if args.no_content:
        cmd_options.append('--no-content')
    if args.no_output:
        cmd_options.append('--no-output')
    if args.format != 'txt':
        cmd_options.append(f'--format {args.format}')
    cmd_line = ' '.join(cmd_options)

    # Run analysis
    spinner = Spinner(f"Scanning AsciiDoc files in {args.directory}")
    spinner.start()

    try:
        duplicate_groups = find_duplicates(
            root_dir=args.directory,
            min_similarity=similarity,
            min_content_length=args.min_length,
            exclude_dirs=exclude_dirs,
            block_types=args.block_types
        )
    except Exception as e:
        spinner.stop()
        print(f"Error: {e}")
        return 1

    spinner.stop(f"Found {len(duplicate_groups)} groups of duplicate content")

    # Print command line options used
    print(f"\nCommand: {cmd_line}")
    print(f"Directory: {os.path.abspath(args.directory)}\n")

    # Generate report based on format
    if args.format == 'csv':
        report = generate_csv_report(duplicate_groups)
    else:
        report = format_report(
            duplicate_groups,
            show_content=not args.no_content
        )

    print(report)

    # Write report file by default (unless --no-output)
    if not args.no_output and duplicate_groups:
        reports_dir = './reports'
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'{reports_dir}/duplicate-content_{timestamp}.{args.format}'

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Duplicate content report\n")
            f.write(f"Command: {cmd_line}\n")
            f.write(f"Directory: {os.path.abspath(args.directory)}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(report)

        print(f"\nReport written to: {filename}")

    return 0


if __name__ == '__main__':
    sys.exit(main())

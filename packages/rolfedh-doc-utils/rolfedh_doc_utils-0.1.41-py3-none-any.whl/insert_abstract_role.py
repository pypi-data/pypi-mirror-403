#!/usr/bin/env python3
"""
insert-abstract-role - Insert [role="_abstract"] above the first paragraph after the title.

Ensures AsciiDoc files have the [role="_abstract"] attribute required for DITA short description
conversion, as enforced by the AsciiDocDITA.ShortDescription vale rule.
"""

import argparse
import sys
from pathlib import Path

from doc_utils.insert_abstract_role import process_file, find_adoc_files
from doc_utils.version_check import check_version_on_startup
from doc_utils.version import __version__
from doc_utils.file_utils import parse_exclude_list_file


# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_colored(message: str, color: str = Colors.NC) -> None:
    """Print message with color"""
    print(f"{color}{message}{Colors.NC}")


def main():
    # Check for updates (non-blocking, won't interfere with tool operation)
    check_version_on_startup()

    parser = argparse.ArgumentParser(
        description="Insert [role=\"_abstract\"] above the first paragraph after the document title",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Insert [role="_abstract"] above the first paragraph after the document title in AsciiDoc files.
This attribute is required for DITA short description conversion.

The tool identifies the first paragraph after a level 1 heading (= Title) and inserts
the [role="_abstract"] attribute on the line immediately before it.

Examples:
  %(prog)s                                    # Process all .adoc files in current directory
  %(prog)s modules/                           # Process all .adoc files in modules/
  %(prog)s modules/rn/my-release-note.adoc    # Process single file
  %(prog)s --dry-run modules/                 # Preview changes without modifying
  %(prog)s --exclude-dir .archive modules/    # Exclude .archive directories
        """
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='File or directory to process (default: current directory)'
    )
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--exclude-dir',
        action='append',
        default=[],
        help='Directory to exclude (can be specified multiple times)'
    )
    parser.add_argument(
        '--exclude-file',
        action='append',
        default=[],
        help='File to exclude (can be specified multiple times)'
    )
    parser.add_argument(
        '--exclude-list',
        help='Path to file containing list of files/directories to exclude (one per line)'
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    args = parser.parse_args()

    # Convert path to Path object
    target_path = Path(args.path)

    # Check if path exists
    if not target_path.exists():
        print_colored(f"Error: Path does not exist: {target_path}", Colors.RED)
        sys.exit(1)

    # Parse exclusion list file if provided
    exclude_dirs = list(args.exclude_dir)
    exclude_files = list(args.exclude_file)

    if args.exclude_list:
        list_dirs, list_files = parse_exclude_list_file(args.exclude_list)
        exclude_dirs.extend(list_dirs)
        exclude_files.extend(list_files)

    # Display dry-run mode message
    if args.dry_run:
        print_colored("DRY RUN MODE - No files will be modified", Colors.YELLOW)

    # Find all AsciiDoc files
    adoc_files = find_adoc_files(target_path, exclude_dirs, exclude_files)

    if not adoc_files:
        if target_path.is_file():
            print_colored(f"Warning: {target_path} is not an AsciiDoc file (.adoc)", Colors.YELLOW)
        print(f"Processed 0 AsciiDoc file(s)")
        print("Insert abstract role complete!")
        return

    # Process each file
    files_processed = 0
    files_modified = 0

    for file_path in adoc_files:
        try:
            changes_made, messages = process_file(file_path, args.dry_run, args.verbose)

            # Print verbose messages
            if args.verbose:
                for msg in messages:
                    print(msg)

            if changes_made:
                files_modified += 1
                if args.dry_run:
                    print_colored(f"Would modify: {file_path}", Colors.YELLOW)
                else:
                    print_colored(f"Modified: {file_path}", Colors.GREEN)
            elif args.verbose:
                print(f"  No changes needed for: {file_path}")

            files_processed += 1

        except KeyboardInterrupt:
            print_colored("\nOperation cancelled by user", Colors.YELLOW)
            sys.exit(1)
        except IOError as e:
            print_colored(f"{e}", Colors.RED)
        except Exception as e:
            print_colored(f"Unexpected error processing {file_path}: {e}", Colors.RED)

    print(f"Processed {files_processed} AsciiDoc file(s)")
    if args.dry_run and files_modified > 0:
        print(f"Would modify {files_modified} file(s)")
    elif files_modified > 0:
        print(f"Modified {files_modified} file(s)")
    print("Insert abstract role complete!")


if __name__ == "__main__":
    main()

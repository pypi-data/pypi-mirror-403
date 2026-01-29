#!/usr/bin/env python3
"""
CLI tool to create an inventory of AsciiDoc conditional directives.

Scans .adoc files for ifdef, ifndef, endif, and ifeval directives
and creates a timestamped inventory file.

Usage:
    inventory-conditionals [directory] [-o OUTPUT_DIR]

If no directory is specified, the current working directory is used.
"""

import argparse
from pathlib import Path

from doc_utils.inventory_conditionals import create_inventory


def main():
    parser = argparse.ArgumentParser(
        description='Create an inventory of AsciiDoc conditional directives.'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to scan for .adoc files (default: current directory)'
    )
    parser.add_argument(
        '-o', '--output-dir',
        default=None,
        help='Directory to write the inventory file (default: current directory)'
    )

    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"Error: {directory} is not a valid directory")
        return 1

    output_dir = Path(args.output_dir).resolve() if args.output_dir else Path.cwd()

    print(f"Scanning for .adoc files in: {directory}")
    output_file = create_inventory(directory, output_dir)
    print(f"Inventory written to: {output_file}")

    return 0


if __name__ == '__main__':
    exit(main())

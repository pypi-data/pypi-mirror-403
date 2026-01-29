#!/usr/bin/env python3
"""
convert-freemarker-to-asciidoc - Convert FreeMarker-templated AsciiDoc to standard AsciiDoc.

Converts Keycloak-style FreeMarker template markup in AsciiDoc files to standard
AsciiDoc format. This tool:

- Removes FreeMarker import statements (<#import ...>)
- Converts <@tmpl.guide> blocks to AsciiDoc title and short description
- Removes closing </@tmpl.guide> tags
- Converts <@links.*> macros to AsciiDoc xref cross-references
- Converts <@kc.*> command macros to code blocks
- Handles <@profile.*> conditional blocks (community vs product)
- Removes <@opts.*> option macros

Usage:
    convert-freemarker-to-asciidoc                    # Process current directory
    convert-freemarker-to-asciidoc docs/guides/       # Process specific directory
    convert-freemarker-to-asciidoc --dry-run          # Preview changes
    convert-freemarker-to-asciidoc --structure-only   # Only convert imports and guide blocks

Examples:
    # Preview changes without modifying files
    convert-freemarker-to-asciidoc --dry-run docs/guides/

    # Convert all .adoc files in current directory
    convert-freemarker-to-asciidoc

    # Only convert structure (imports, guide blocks) - leave inline macros
    convert-freemarker-to-asciidoc --structure-only docs/guides/server/

    # Keep product content instead of community content
    convert-freemarker-to-asciidoc --product docs/guides/
"""

import argparse
import sys
from pathlib import Path

from doc_utils.convert_freemarker_to_asciidoc import (
    process_file,
    find_adoc_files,
    has_freemarker_content,
    ConversionStats
)
from doc_utils.version_check import check_version_on_startup
from doc_utils.version import __version__


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


def print_colored(message: str, color: str = Colors.NC) -> None:
    """Print message with color."""
    print(f"{color}{message}{Colors.NC}")


def aggregate_stats(stats_list: list) -> ConversionStats:
    """Aggregate statistics from multiple conversion results."""
    total = ConversionStats()
    for stats in stats_list:
        total.imports_removed += stats.imports_removed
        total.guide_blocks_converted += stats.guide_blocks_converted
        total.closing_tags_removed += stats.closing_tags_removed
        total.link_macros_converted += stats.link_macros_converted
        total.kc_macros_converted += stats.kc_macros_converted
        total.profile_blocks_handled += stats.profile_blocks_handled
        total.noparse_blocks_handled += stats.noparse_blocks_handled
        total.opts_macros_removed += stats.opts_macros_removed
        total.features_macros_removed += stats.features_macros_removed
        total.other_macros_removed += stats.other_macros_removed
        total.directives_marked += stats.directives_marked
    return total


def format_stats_summary(stats: ConversionStats) -> str:
    """Format statistics as a summary string."""
    parts = []
    if stats.imports_removed > 0:
        parts.append(f"{stats.imports_removed} import(s)")
    if stats.guide_blocks_converted > 0:
        parts.append(f"{stats.guide_blocks_converted} guide block(s)")
    if stats.link_macros_converted > 0:
        parts.append(f"{stats.link_macros_converted} link(s) -> xref")
    if stats.kc_macros_converted > 0:
        parts.append(f"{stats.kc_macros_converted} command(s) -> code")
    if stats.profile_blocks_handled > 0:
        parts.append(f"{stats.profile_blocks_handled} profile block(s)")
    if stats.noparse_blocks_handled > 0:
        parts.append(f"{stats.noparse_blocks_handled} noparse block(s)")
    if stats.opts_macros_removed > 0:
        parts.append(f"{stats.opts_macros_removed} opts macro(s)")
    if stats.features_macros_removed > 0:
        parts.append(f"{stats.features_macros_removed} features macro(s)")
    if stats.directives_marked > 0:
        parts.append(f"{stats.directives_marked} directive(s) marked")
    if stats.other_macros_removed > 0:
        parts.append(f"{stats.other_macros_removed} other macro(s)")
    return ', '.join(parts) if parts else 'no changes'


def main():
    """Main entry point."""
    # Check for updates (non-blocking)
    check_version_on_startup()

    parser = argparse.ArgumentParser(
        description="Convert FreeMarker-templated AsciiDoc to standard AsciiDoc",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Convert FreeMarker template markup to standard AsciiDoc:

  STRUCTURE (always converted):
  - Removes <#import ...> statements
  - Converts <@tmpl.guide title="..." summary="..."> to = Title and summary
  - Removes </@tmpl.guide> closing tags

  INLINE MACROS (converted by default, skip with --structure-only):
  - <@links.server id="hostname"/> -> xref:server/hostname.adoc[]
  - <@kc.start parameters="--hostname x"/> -> code block with bin/kc.sh command
  - <@profile.ifCommunity> blocks -> kept (or removed with --product)
  - <@opts.*> macros -> removed (build-time generated)

This tool is designed for converting Keycloak documentation from FreeMarker
template format to standard AsciiDoc that can be used with other toolchains.

Examples:
  %(prog)s                                    # Process all .adoc files
  %(prog)s docs/guides/                       # Process specific directory
  %(prog)s docs/guides/server/hostname.adoc   # Process single file
  %(prog)s --dry-run docs/guides/             # Preview changes
  %(prog)s --structure-only docs/guides/      # Only convert structure
  %(prog)s --product docs/guides/             # Keep product content
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
        help='Show detailed output for each file'
    )
    parser.add_argument(
        '--structure-only',
        action='store_true',
        help='Only convert structure (imports, guide blocks); leave inline macros'
    )
    parser.add_argument(
        '--product',
        action='store_true',
        help='Keep product content in profile blocks (default: keep community)'
    )
    parser.add_argument(
        '--base-path',
        default='',
        help='Base path prefix for xref links (e.g., "guides")'
    )
    parser.add_argument(
        '--only-freemarker',
        action='store_true',
        help='Only process files that contain FreeMarker markup (faster for mixed repos)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    args = parser.parse_args()

    # Convert path to Path object
    target_path = Path(args.path)

    # Check if path exists
    if not target_path.exists():
        print_colored(f"Error: Path does not exist: {target_path}", Colors.RED)
        sys.exit(1)

    # Display mode messages
    if args.dry_run:
        print_colored("DRY RUN MODE - No files will be modified", Colors.YELLOW)
        print()

    if args.structure_only:
        print("Converting structure only (imports, guide blocks)")
        print()

    # Find all AsciiDoc files
    adoc_files = find_adoc_files(target_path)

    if not adoc_files:
        if target_path.is_file():
            print_colored(
                f"Warning: {target_path} is not an AsciiDoc file (.adoc)",
                Colors.YELLOW
            )
        print("No AsciiDoc files found.")
        return

    # Filter to only files with FreeMarker content if requested
    if args.only_freemarker:
        adoc_files = [f for f in adoc_files if has_freemarker_content(f)]
        if not adoc_files:
            print("No files with FreeMarker markup found.")
            return
        if args.verbose:
            print(f"Found {len(adoc_files)} file(s) with FreeMarker markup")
            print()

    # Process each file
    files_processed = 0
    files_modified = 0
    all_stats = []

    for file_path in adoc_files:
        try:
            result = process_file(
                file_path,
                dry_run=args.dry_run,
                verbose=args.verbose,
                convert_all=not args.structure_only,
                keep_community=not args.product,
                base_path=args.base_path
            )

            # Print verbose messages
            if args.verbose:
                for msg in result.messages:
                    print(msg)

            if result.changes_made:
                files_modified += 1
                all_stats.append(result.stats)

                if args.dry_run:
                    print_colored(f"Would modify: {file_path}", Colors.YELLOW)
                else:
                    print_colored(f"Modified: {file_path}", Colors.GREEN)

            files_processed += 1

        except KeyboardInterrupt:
            print_colored("\nOperation cancelled by user", Colors.YELLOW)
            sys.exit(1)
        except IOError as e:
            print_colored(f"{e}", Colors.RED)
        except Exception as e:
            print_colored(f"Unexpected error processing {file_path}: {e}", Colors.RED)

    # Print summary
    print()
    print(f"Processed {files_processed} AsciiDoc file(s)")

    if files_modified > 0:
        if args.dry_run:
            print(f"Would modify {files_modified} file(s)")
        else:
            print(f"Modified {files_modified} file(s)")

        # Detailed stats
        total_stats = aggregate_stats(all_stats)
        summary = format_stats_summary(total_stats)
        print(f"  ({summary})")
    else:
        print("No files needed conversion.")

    print()
    print_colored("FreeMarker to AsciiDoc conversion complete!", Colors.CYAN)


if __name__ == "__main__":
    main()

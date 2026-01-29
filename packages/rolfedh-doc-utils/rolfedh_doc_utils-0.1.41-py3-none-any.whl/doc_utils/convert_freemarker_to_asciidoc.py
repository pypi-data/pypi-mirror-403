"""
Convert FreeMarker-templated AsciiDoc to standard AsciiDoc.

Core logic for converting Keycloak-style FreeMarker template markup in AsciiDoc
files to standard AsciiDoc format. This module handles:

- Removing FreeMarker import statements (<#import ...>)
- Converting <@tmpl.guide> and <@template.guide> blocks to AsciiDoc title/summary
- Removing closing </@tmpl.guide> and </@template.guide> tags
- Converting <@links.*> macros to AsciiDoc xref cross-references
- Converting <@kc.*> command macros to code blocks
- Removing or preserving <@profile.*> conditional blocks
- Removing <@opts.*> option macros (build-time generated content)
- Removing <@features.table> macros (build-time generated content)
- Handling <#noparse> blocks (preserving content, removing tags)

PATTERNS THAT CANNOT BE RELIABLY CONVERTED (require manual review):
- <#list> loops: Dynamic content generation, no static equivalent
- <#if>/<#else> conditionals: Logic-based content, context-dependent
- <#assign> variables: Build-time variable assignment
- <@features.table ctx.*/>: Dynamic feature tables generated at build time
- Index files with <#list ctx.guides>: Auto-generated navigation
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field


# Mapping of link types to their base paths
# These are the guide categories used in Keycloak docs
LINK_TYPE_PATHS: Dict[str, str] = {
    'server': 'server',
    'ha': 'high-availability',
    'gettingstarted': 'getting-started',
    'operator': 'operator',
    'migration': 'migration',
    'securing': 'securing-apps',
    'securingapps': 'securing-apps',  # Alternative spelling used in some files
    'observability': 'observability',
}

# Mapping of kc command types to their shell commands
KC_COMMAND_MAP: Dict[str, str] = {
    'start': 'bin/kc.sh start',
    'startdev': 'bin/kc.sh start-dev',
    'build': 'bin/kc.sh build',
    'export': 'bin/kc.sh export',
    'import': 'bin/kc.sh import',
    'admin': 'bin/kcadm.sh',
    'bootstrapadmin': 'bin/kc.sh bootstrap-admin',
    'updatecompatibility': 'bin/kc.sh update-compatibility',
}


@dataclass
class ConversionStats:
    """Statistics for a conversion operation."""
    imports_removed: int = 0
    guide_blocks_converted: int = 0
    closing_tags_removed: int = 0
    link_macros_converted: int = 0
    kc_macros_converted: int = 0
    profile_blocks_handled: int = 0
    noparse_blocks_handled: int = 0
    opts_macros_removed: int = 0
    features_macros_removed: int = 0
    other_macros_removed: int = 0
    directives_marked: int = 0


@dataclass
class ConversionResult:
    """Result of converting a single file."""
    file_path: Path
    changes_made: bool
    stats: ConversionStats = field(default_factory=ConversionStats)
    messages: List[str] = field(default_factory=list)


def extract_guide_attributes(content: str) -> Optional[Tuple[str, str, int, int]]:
    """
    Extract title and summary from a <@tmpl.guide> or <@template.guide> block.

    Args:
        content: The file content to parse

    Returns:
        Tuple of (title, summary, start_index, end_index) or None if not found
    """
    # Match both <@tmpl.guide> and <@template.guide> variants
    pattern = r'<@(?:tmpl|template)\.guide\s*\n?((?:[^>]|\n)*?)>'

    match = re.search(pattern, content)
    if not match:
        return None

    block_content = match.group(1)
    start_idx = match.start()
    end_idx = match.end()

    # Extract title attribute
    title_match = re.search(r'title\s*=\s*"([^"]*)"', block_content)
    title = title_match.group(1) if title_match else ""

    # Extract summary attribute
    summary_match = re.search(r'summary\s*=\s*"([^"]*)"', block_content)
    summary = summary_match.group(1) if summary_match else ""

    return (title, summary, start_idx, end_idx)


def remove_freemarker_imports(content: str) -> Tuple[str, int]:
    """
    Remove FreeMarker import statements from content.

    Args:
        content: The file content

    Returns:
        Tuple of (modified content, count of imports removed)
    """
    # Match lines that are FreeMarker imports: <#import "..." as ...>
    import_pattern = r'^<#import\s+"[^"]+"\s+as\s+\w+>\s*\n?'

    count = len(re.findall(import_pattern, content, re.MULTILINE))
    new_content = re.sub(import_pattern, '', content, flags=re.MULTILINE)

    return (new_content, count)


def convert_guide_block(content: str) -> Tuple[str, bool]:
    """
    Convert <@tmpl.guide> or <@template.guide> block to standard AsciiDoc title and summary.

    Args:
        content: The file content

    Returns:
        Tuple of (modified content, whether conversion was made)
    """
    result = extract_guide_attributes(content)
    if not result:
        return (content, False)

    title, summary, start_idx, end_idx = result

    # Build the AsciiDoc replacement
    replacement_parts = []

    if title:
        replacement_parts.append(f"= {title}")
        replacement_parts.append("")  # Blank line after title

    if summary:
        replacement_parts.append(summary)
        replacement_parts.append("")  # Blank line after summary

    replacement = "\n".join(replacement_parts)

    # Replace the guide block with the AsciiDoc equivalent
    new_content = content[:start_idx] + replacement + content[end_idx:]

    # Clean up any excessive blank lines at the start
    new_content = re.sub(r'^\n+', '', new_content)

    return (new_content, True)


def remove_closing_guide_tag(content: str) -> Tuple[str, bool]:
    """
    Remove the closing </@tmpl.guide> or </@template.guide> tag.

    Args:
        content: The file content

    Returns:
        Tuple of (modified content, whether tag was removed)
    """
    # Match both variants
    pattern = r'\n*</@(?:tmpl|template)\.guide>\s*\n*'
    if re.search(pattern, content):
        new_content = re.sub(pattern, '\n', content)
        return (new_content, True)
    return (content, False)


def convert_link_macros(content: str, base_path: str = '') -> Tuple[str, int]:
    """
    Convert <@links.*> macros to AsciiDoc xref cross-references.

    Converts patterns like:
    - <@links.server id="hostname"/> -> xref:server/hostname.adoc[]
    - <@links.ha id="intro" anchor="section"/> -> xref:high-availability/intro.adoc#section[]
    - <@links.securingapps id="client-registration"/> -> xref:securing-apps/client-registration.adoc[]

    Args:
        content: The file content
        base_path: Optional base path prefix for xref links

    Returns:
        Tuple of (modified content, count of macros converted)
    """
    count = 0

    def replace_link(match):
        nonlocal count
        count += 1

        link_type = match.group(1)  # e.g., 'server', 'ha', 'gettingstarted', 'securingapps'
        link_id = match.group(2)    # e.g., 'hostname', 'introduction'
        anchor = match.group(4) if match.group(4) else ''  # Optional anchor

        # Map link type to directory path
        dir_path = LINK_TYPE_PATHS.get(link_type, link_type)

        # Build the file path
        file_path = f"{link_id}.adoc"

        # Build the xref
        if base_path:
            xref_path = f"{base_path}/{dir_path}/{file_path}"
        else:
            xref_path = f"{dir_path}/{file_path}"

        if anchor:
            xref_path += f"#{anchor}"

        # Return xref with empty link text (will use document title)
        return f"xref:{xref_path}[]"

    # Pattern to match link macros:
    # <@links.TYPE id="ID"/> or <@links.TYPE id="ID" anchor="ANCHOR"/>
    # Also handles extra whitespace variations
    link_pattern = r'<@links\.(\w+)\s+id="([^"]+)"(\s+anchor="([^"]+)")?\s*/>'

    new_content = re.sub(link_pattern, replace_link, content)

    return (new_content, count)


def convert_kc_macros(content: str) -> Tuple[str, int]:
    """
    Convert <@kc.*> command macros to AsciiDoc code blocks.

    Converts patterns like:
    - <@kc.start parameters="--hostname x"/> -> [source,bash]\n----\nbin/kc.sh start --hostname x\n----
    - <@kc.build parameters="--db postgres"/> -> [source,bash]\n----\nbin/kc.sh build --db postgres\n----
    - <@kc.export parameters="--dir <dir>"/> -> [source,bash]\n----\nbin/kc.sh export --dir <dir>\n----
    - <@kc.import parameters="--file <file>"/> -> [source,bash]\n----\nbin/kc.sh import --file <file>\n----

    Args:
        content: The file content

    Returns:
        Tuple of (modified content, count of macros converted)
    """
    count = 0

    def replace_kc_macro(match):
        nonlocal count
        count += 1

        command = match.group(1)      # e.g., 'start', 'build', 'admin', 'export', 'import'
        parameters = match.group(2)   # e.g., '--hostname my.keycloak.org'

        # Get the base command from the map, or use generic kc.sh
        if command in KC_COMMAND_MAP:
            base_cmd = KC_COMMAND_MAP[command]
        else:
            # Generic kc command
            base_cmd = f"bin/kc.sh {command}"

        # Build the full command line
        if parameters:
            cmd_line = f"{base_cmd} {parameters}".strip()
        else:
            cmd_line = base_cmd

        # Return as a code block
        return f"[source,bash]\n----\n{cmd_line}\n----"

    # Pattern to match kc macros: <@kc.COMMAND parameters="PARAMS"/>
    kc_pattern = r'<@kc\.(\w+)\s+parameters="([^"]*)"\s*/>'

    new_content = re.sub(kc_pattern, replace_kc_macro, content)

    return (new_content, count)


def handle_profile_blocks(content: str, keep_community: bool = True) -> Tuple[str, int]:
    """
    Handle <@profile.*> conditional blocks.

    These blocks wrap content that should only appear in specific editions
    (community vs product). By default, we keep community content and remove
    product-specific content.

    Args:
        content: The file content
        keep_community: If True, keep community content; if False, keep product content

    Returns:
        Tuple of (modified content, count of blocks handled)
    """
    count = 0

    # First, handle ifCommunity blocks
    community_pattern = r'<@profile\.ifCommunity>\s*\n?(.*?)</@profile\.ifCommunity>\s*\n?'

    def handle_community(match):
        nonlocal count
        count += 1
        if keep_community:
            # Keep the content, remove the tags
            return match.group(1)
        else:
            # Remove the entire block
            return ''

    content = re.sub(community_pattern, handle_community, content, flags=re.DOTALL)

    # Handle ifProduct blocks
    product_pattern = r'<@profile\.ifProduct>\s*\n?(.*?)</@profile\.ifProduct>\s*\n?'

    def handle_product(match):
        nonlocal count
        count += 1
        if not keep_community:
            # Keep the content, remove the tags
            return match.group(1)
        else:
            # Remove the entire block
            return ''

    content = re.sub(product_pattern, handle_product, content, flags=re.DOTALL)

    return (content, count)


def handle_noparse_blocks(content: str) -> Tuple[str, int]:
    """
    Handle <#noparse> blocks by removing the tags but keeping the content.

    These blocks are used to escape FreeMarker syntax in code examples.
    The content inside should be preserved as-is.

    Args:
        content: The file content

    Returns:
        Tuple of (modified content, count of blocks handled)
    """
    count = 0

    # Pattern for noparse blocks: <#noparse>...</#noparse>
    noparse_pattern = r'<#noparse>\s*\n?(.*?)</#noparse>\s*\n?'

    def handle_noparse(match):
        nonlocal count
        count += 1
        # Keep the content, remove the tags
        return match.group(1)

    content = re.sub(noparse_pattern, handle_noparse, content, flags=re.DOTALL)

    return (content, count)


def remove_opts_macros(content: str) -> Tuple[str, int]:
    """
    Remove <@opts.*> option macros.

    These macros generate option documentation at build time and have no
    meaningful conversion to static AsciiDoc. They are replaced with a
    placeholder comment.

    Args:
        content: The file content

    Returns:
        Tuple of (modified content, count of macros removed)
    """
    count = 0

    # Pattern for self-closing opts macros: <@opts.expectedValues option="..."/>
    self_closing_pattern = r'<@opts\.\w+[^/>]*\/>'

    def replace_self_closing(match):
        nonlocal count
        count += 1
        return '// Configuration options are documented in the all-config guide'

    content = re.sub(self_closing_pattern, replace_self_closing, content)

    # Pattern for block opts macros: <@opts.list ...>...</@opts.list>
    block_pattern = r'<@opts\.\w+[^>]*>.*?</@opts\.\w+>'

    def replace_block(match):
        nonlocal count
        count += 1
        return '// Configuration options are documented in the all-config guide'

    content = re.sub(block_pattern, replace_block, content, flags=re.DOTALL)

    return (content, count)


def remove_features_macros(content: str) -> Tuple[str, int]:
    """
    Remove <@features.table> macros.

    These macros generate feature tables at build time and cannot be
    converted to static content.

    Args:
        content: The file content

    Returns:
        Tuple of (modified content, count of macros removed)
    """
    count = 0

    # Pattern for features.table macros: <@features.table ctx.features.supported/>
    features_pattern = r'<@features\.table[^/>]*\/>'

    def replace_features(match):
        nonlocal count
        count += 1
        return '// Feature table is generated at build time - see the features guide'

    content = re.sub(features_pattern, replace_features, content)

    return (content, count)


def mark_unconvertible_directives(content: str) -> Tuple[str, int]:
    """
    Mark FreeMarker directives that cannot be reliably converted.

    These include:
    - <#list> loops
    - <#if>/<#else> conditionals
    - <#assign> variables

    Args:
        content: The file content

    Returns:
        Tuple of (modified content, count of directives marked)
    """
    count = 0

    # Pattern for list blocks: <#list ...>...</#list>
    list_pattern = r'(<#list\s+[^>]+>)(.*?)(</#list>)'

    def mark_list(match):
        nonlocal count
        count += 1
        opening = match.group(1)
        inner = match.group(2)
        closing = match.group(3)
        return f"// TODO: Manual conversion required - FreeMarker list loop\n// {opening}\n{inner}// {closing}"

    content = re.sub(list_pattern, mark_list, content, flags=re.DOTALL)

    # Pattern for if/else blocks: <#if ...>...</#if>
    if_pattern = r'(<#if\s+[^>]+>)(.*?)(</#if>)'

    def mark_if(match):
        nonlocal count
        count += 1
        opening = match.group(1)
        inner = match.group(2)
        closing = match.group(3)
        return f"// TODO: Manual conversion required - FreeMarker conditional\n// {opening}\n{inner}// {closing}"

    content = re.sub(if_pattern, mark_if, content, flags=re.DOTALL)

    # Pattern for standalone else: <#else>
    else_pattern = r'<#else>'

    def mark_else(match):
        nonlocal count
        count += 1
        return '// <#else>'

    content = re.sub(else_pattern, mark_else, content)

    # Pattern for assign: <#assign ...>
    assign_pattern = r'<#assign\s+[^>]+>'

    def mark_assign(match):
        nonlocal count
        count += 1
        return f"// TODO: Manual conversion required - {match.group(0)}"

    content = re.sub(assign_pattern, mark_assign, content)

    return (content, count)


def remove_remaining_macros(content: str) -> Tuple[str, int]:
    """
    Remove any remaining FreeMarker macros that weren't handled by specific converters.

    Args:
        content: The file content

    Returns:
        Tuple of (modified content, count of macros removed)
    """
    count = 0

    # Self-closing macros: <@something .../>
    self_closing = r'<@\w+\.[^/>]+/>'
    self_closing_count = len(re.findall(self_closing, content))
    if self_closing_count > 0:
        content = re.sub(self_closing, '// TODO: Unconverted FreeMarker macro', content)
        count += self_closing_count

    # Block macros: <@something>...</@something>
    block_pattern = r'<@\w+[^>]*>.*?</@\w+[^>]*>'
    block_count = len(re.findall(block_pattern, content, re.DOTALL))
    if block_count > 0:
        content = re.sub(block_pattern, '// TODO: Unconverted FreeMarker macro', content, flags=re.DOTALL)
        count += block_count

    return (content, count)


def process_file(
    file_path: Path,
    dry_run: bool = False,
    verbose: bool = False,
    convert_all: bool = True,
    keep_community: bool = True,
    base_path: str = ''
) -> ConversionResult:
    """
    Process a single AsciiDoc file to convert FreeMarker markup.

    Args:
        file_path: Path to the file to process
        dry_run: If True, show what would be changed without modifying
        verbose: If True, show detailed output
        convert_all: If True, convert all FreeMarker macros (not just structure)
        keep_community: If True, keep community content in profile blocks
        base_path: Optional base path prefix for xref links

    Returns:
        ConversionResult with details of changes made
    """
    messages = []
    stats = ConversionStats()

    if verbose:
        messages.append(f"Processing: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except (IOError, UnicodeDecodeError) as e:
        raise IOError(f"Error reading {file_path}: {e}")

    content = original_content

    # Step 1: Remove FreeMarker imports
    content, count = remove_freemarker_imports(content)
    stats.imports_removed = count
    if count > 0 and verbose:
        messages.append(f"  Removed {count} FreeMarker import(s)")

    # Step 2: Convert guide block (both tmpl.guide and template.guide)
    content, converted = convert_guide_block(content)
    if converted:
        stats.guide_blocks_converted = 1
        if verbose:
            messages.append("  Converted guide block to AsciiDoc title/summary")

    # Step 3: Remove closing tag
    content, removed = remove_closing_guide_tag(content)
    if removed:
        stats.closing_tags_removed = 1
        if verbose:
            messages.append("  Removed closing guide tag")

    # Step 4: Convert inline macros if requested
    if convert_all:
        # Handle noparse blocks first (preserve content)
        content, count = handle_noparse_blocks(content)
        stats.noparse_blocks_handled = count
        if count > 0 and verbose:
            messages.append(f"  Processed {count} <#noparse> block(s)")

        # Convert link macros to xrefs
        content, count = convert_link_macros(content, base_path)
        stats.link_macros_converted = count
        if count > 0 and verbose:
            messages.append(f"  Converted {count} <@links.*> macro(s) to xref")

        # Convert kc command macros to code blocks
        content, count = convert_kc_macros(content)
        stats.kc_macros_converted = count
        if count > 0 and verbose:
            messages.append(f"  Converted {count} <@kc.*> macro(s) to code blocks")

        # Handle profile conditional blocks
        content, count = handle_profile_blocks(content, keep_community)
        stats.profile_blocks_handled = count
        if count > 0 and verbose:
            messages.append(f"  Processed {count} <@profile.*> block(s)")

        # Remove opts macros
        content, count = remove_opts_macros(content)
        stats.opts_macros_removed = count
        if count > 0 and verbose:
            messages.append(f"  Removed {count} <@opts.*> macro(s)")

        # Remove features macros
        content, count = remove_features_macros(content)
        stats.features_macros_removed = count
        if count > 0 and verbose:
            messages.append(f"  Removed {count} <@features.*> macro(s)")

        # Mark unconvertible directives
        content, count = mark_unconvertible_directives(content)
        stats.directives_marked = count
        if count > 0 and verbose:
            messages.append(f"  Marked {count} FreeMarker directive(s) for manual review")

        # Remove any remaining macros
        content, count = remove_remaining_macros(content)
        stats.other_macros_removed = count
        if count > 0 and verbose:
            messages.append(f"  Marked {count} other macro(s) for review")

    # Determine if changes were made
    changes_made = content != original_content

    # Write changes if not dry run
    if changes_made and not dry_run:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except IOError as e:
            raise IOError(f"Error writing {file_path}: {e}")

    if not changes_made and verbose:
        messages.append("  No FreeMarker markup found")

    return ConversionResult(
        file_path=file_path,
        changes_made=changes_made,
        stats=stats,
        messages=messages
    )


def find_adoc_files(path: Path) -> List[Path]:
    """
    Find all .adoc files in the given path.

    Args:
        path: File or directory to search

    Returns:
        List of Path objects for .adoc files
    """
    adoc_files = []

    if path.is_file():
        if path.suffix == '.adoc':
            adoc_files.append(path)
    elif path.is_dir():
        # Use os.walk to avoid following symlinks
        import os
        for root, dirs, files in os.walk(path, followlinks=False):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.endswith('.adoc'):
                    adoc_files.append(Path(root) / file)

    return sorted(adoc_files)


def has_freemarker_content(file_path: Path) -> bool:
    """
    Check if a file contains FreeMarker markup.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file contains FreeMarker markup
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return bool(
                re.search(r'<#import', content) or
                re.search(r'<#\w+', content) or  # Any FreeMarker directive
                re.search(r'<@\w+\.', content)   # Any FreeMarker macro
            )
    except (IOError, UnicodeDecodeError):
        return False

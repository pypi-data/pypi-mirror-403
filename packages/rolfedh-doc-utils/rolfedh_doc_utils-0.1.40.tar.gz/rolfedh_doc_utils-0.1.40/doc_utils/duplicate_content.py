"""
Module for finding duplicate and similar content in AsciiDoc files.

This module detects:
- Recurring notes (NOTE, TIP, WARNING, IMPORTANT, CAUTION)
- Tables
- Step sequences (ordered lists)
- Code blocks
- Any other repeated content elements

Functions:
- extract_content_blocks: Extract content blocks from an AsciiDoc file
- find_duplicates: Find duplicate and similar content across files
- calculate_similarity: Calculate text similarity between two strings
"""

import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ContentBlock:
    """Represents a content block extracted from an AsciiDoc file."""
    block_type: str  # 'note', 'table', 'steps', 'code', 'paragraph'
    content: str
    file_path: str
    line_number: int
    content_hash: str = field(default="", init=False)

    def __post_init__(self):
        # Normalize content for comparison (strip whitespace, lowercase)
        normalized = ' '.join(self.content.split()).lower()
        self.content_hash = hashlib.md5(normalized.encode()).hexdigest()


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate or similar content blocks."""
    block_type: str
    blocks: List[ContentBlock]
    similarity: float  # 1.0 for exact, < 1.0 for similar
    canonical_content: str  # Representative content for this group


def find_adoc_files(root_dir: str, exclude_dirs: List[str] = None) -> List[str]:
    """Recursively find all .adoc files in a directory (ignoring symlinks)."""
    if exclude_dirs is None:
        exclude_dirs = ['.git', '.archive', 'target', 'build', 'node_modules']

    adoc_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=False):
        # Remove excluded directories from dirnames to prevent descending into them
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]

        for fname in filenames:
            if fname.endswith('.adoc'):
                full_path = os.path.join(dirpath, fname)
                if not os.path.islink(full_path):
                    adoc_files.append(full_path)
    return adoc_files


def extract_content_blocks(file_path: str) -> List[ContentBlock]:
    """
    Extract content blocks from an AsciiDoc file.

    Identifies:
    - Admonition blocks (NOTE, TIP, WARNING, IMPORTANT, CAUTION)
    - Tables (|=== blocks)
    - Ordered lists (step sequences)
    - Code blocks (---- or .... blocks)
    - Delimited blocks ([NOTE], [TIP], etc.)
    """
    blocks = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (UnicodeDecodeError, PermissionError):
        return blocks

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for inline admonitions (NOTE:, TIP:, etc.)
        admonition_match = re.match(r'^(NOTE|TIP|WARNING|IMPORTANT|CAUTION):\s*(.+)$', stripped)
        if admonition_match:
            block_type = admonition_match.group(1).lower()
            content = admonition_match.group(2)
            blocks.append(ContentBlock(
                block_type=block_type,
                content=content,
                file_path=file_path,
                line_number=i + 1
            ))
            i += 1
            continue

        # Check for delimited admonition blocks [NOTE], [TIP], etc.
        delimited_match = re.match(r'^\[(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]$', stripped)
        if delimited_match:
            block_type = delimited_match.group(1).lower()
            # Read until we hit a delimiter or empty line pattern
            content_lines = []
            i += 1
            # Check for delimiter on next line
            if i < len(lines) and lines[i].strip().startswith('===='):
                delimiter = lines[i].strip()
                i += 1
                while i < len(lines) and lines[i].strip() != delimiter:
                    content_lines.append(lines[i])
                    i += 1
                i += 1  # Skip closing delimiter
            else:
                # No delimiter, read paragraph
                while i < len(lines) and lines[i].strip():
                    content_lines.append(lines[i])
                    i += 1

            if content_lines:
                blocks.append(ContentBlock(
                    block_type=block_type,
                    content=''.join(content_lines).strip(),
                    file_path=file_path,
                    line_number=i - len(content_lines)
                ))
            continue

        # Check for tables (|===)
        if stripped.startswith('|==='):
            content_lines = [line]
            start_line = i + 1
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('|==='):
                content_lines.append(lines[i])
                i += 1
            if i < len(lines):
                content_lines.append(lines[i])
                i += 1

            blocks.append(ContentBlock(
                block_type='table',
                content=''.join(content_lines).strip(),
                file_path=file_path,
                line_number=start_line
            ))
            continue

        # Check for code blocks (---- or ....)
        if stripped.startswith('----') or stripped.startswith('....'):
            delimiter = stripped[:4]
            content_lines = [line]
            start_line = i + 1
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(delimiter):
                content_lines.append(lines[i])
                i += 1
            if i < len(lines):
                content_lines.append(lines[i])
                i += 1

            blocks.append(ContentBlock(
                block_type='code',
                content=''.join(content_lines).strip(),
                file_path=file_path,
                line_number=start_line
            ))
            continue

        # Check for ordered lists (step sequences) - consecutive numbered items
        if re.match(r'^\d+\.\s+', stripped) or stripped.startswith('. '):
            content_lines = [line]
            start_line = i + 1
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                # Continue if numbered item, continuation (+), or indented content
                if (re.match(r'^\d+\.\s+', next_line) or
                    next_line.startswith('. ') or
                    next_line == '+' or
                    (next_line and lines[i].startswith('  '))):
                    content_lines.append(lines[i])
                    i += 1
                elif not next_line:
                    # Empty line might be part of list if followed by more items
                    if i + 1 < len(lines) and (re.match(r'^\d+\.\s+', lines[i+1].strip()) or
                                                lines[i+1].strip().startswith('. ')):
                        content_lines.append(lines[i])
                        i += 1
                    else:
                        break
                else:
                    break

            # Only record if we have multiple steps
            if len([l for l in content_lines if re.match(r'^\d+\.\s+', l.strip()) or l.strip().startswith('. ')]) >= 2:
                blocks.append(ContentBlock(
                    block_type='steps',
                    content=''.join(content_lines).strip(),
                    file_path=file_path,
                    line_number=start_line
                ))
            continue

        i += 1

    return blocks


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings.

    Uses a simple word-based Jaccard similarity for efficiency.
    Returns a value between 0.0 (completely different) and 1.0 (identical).
    """
    # Normalize texts
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def find_duplicates(
    root_dir: str,
    min_similarity: float = 0.8,
    min_content_length: int = 50,
    exclude_dirs: List[str] = None,
    block_types: List[str] = None
) -> List[DuplicateGroup]:
    """
    Find duplicate and similar content blocks across AsciiDoc files.

    Args:
        root_dir: Directory to scan
        min_similarity: Minimum similarity threshold (0.0-1.0)
        min_content_length: Minimum content length to consider
        exclude_dirs: Directories to exclude from scanning
        block_types: Types of blocks to search for (None = all types)

    Returns:
        List of DuplicateGroup objects containing groups of similar content
    """
    adoc_files = find_adoc_files(root_dir, exclude_dirs)

    # Collect all content blocks
    all_blocks: List[ContentBlock] = []
    for file_path in adoc_files:
        blocks = extract_content_blocks(file_path)
        for block in blocks:
            if len(block.content) >= min_content_length:
                if block_types is None or block.block_type in block_types:
                    all_blocks.append(block)

    # Group by exact hash first (exact duplicates)
    hash_groups: Dict[str, List[ContentBlock]] = defaultdict(list)
    for block in all_blocks:
        hash_groups[block.content_hash].append(block)

    # Find exact duplicates
    duplicate_groups: List[DuplicateGroup] = []
    processed_hashes: Set[str] = set()

    for content_hash, blocks in hash_groups.items():
        if len(blocks) > 1:
            processed_hashes.add(content_hash)
            duplicate_groups.append(DuplicateGroup(
                block_type=blocks[0].block_type,
                blocks=blocks,
                similarity=1.0,
                canonical_content=blocks[0].content
            ))

    # Find similar (but not exact) duplicates
    if min_similarity < 1.0:
        # Get blocks that weren't exact duplicates
        remaining_blocks = [b for b in all_blocks if b.content_hash not in processed_hashes]

        # Compare remaining blocks for similarity
        used_indices: Set[int] = set()

        for i, block1 in enumerate(remaining_blocks):
            if i in used_indices:
                continue

            similar_blocks = [block1]
            used_indices.add(i)

            for j, block2 in enumerate(remaining_blocks[i+1:], start=i+1):
                if j in used_indices:
                    continue

                # Only compare blocks of the same type
                if block1.block_type != block2.block_type:
                    continue

                similarity = calculate_similarity(block1.content, block2.content)
                if similarity >= min_similarity:
                    similar_blocks.append(block2)
                    used_indices.add(j)

            if len(similar_blocks) > 1:
                # Calculate average similarity within the group
                total_sim = 0
                count = 0
                for k, b1 in enumerate(similar_blocks):
                    for b2 in similar_blocks[k+1:]:
                        total_sim += calculate_similarity(b1.content, b2.content)
                        count += 1
                avg_similarity = total_sim / count if count > 0 else 1.0

                duplicate_groups.append(DuplicateGroup(
                    block_type=similar_blocks[0].block_type,
                    blocks=similar_blocks,
                    similarity=avg_similarity,
                    canonical_content=similar_blocks[0].content
                ))

    # Sort by number of duplicates (most duplicates first)
    duplicate_groups.sort(key=lambda g: len(g.blocks), reverse=True)

    return duplicate_groups


def format_report(
    duplicate_groups: List[DuplicateGroup],
    show_content: bool = True,
    max_content_preview: int = 200
) -> str:
    """
    Format a report of duplicate content groups.

    Args:
        duplicate_groups: List of DuplicateGroup objects
        show_content: Whether to show content preview
        max_content_preview: Maximum characters for content preview

    Returns:
        Formatted report string
    """
    if not duplicate_groups:
        return "No duplicate content found."

    lines = []
    lines.append(f"Found {len(duplicate_groups)} groups of duplicate/similar content\n")
    lines.append("=" * 70)

    for i, group in enumerate(duplicate_groups, 1):
        similarity_label = "EXACT" if group.similarity == 1.0 else f"{group.similarity:.0%} similar"
        lines.append(f"\n[{i}] {group.block_type.upper()} ({similarity_label}) - {len(group.blocks)} occurrences")
        lines.append("-" * 50)

        if show_content:
            preview = group.canonical_content
            if len(preview) > max_content_preview:
                preview = preview[:max_content_preview] + "..."
            # Indent the preview
            preview_lines = preview.split('\n')
            lines.append("  Content preview:")
            for pl in preview_lines[:5]:  # Limit to 5 lines
                lines.append(f"    {pl}")
            if len(preview_lines) > 5:
                lines.append(f"    ... ({len(preview_lines) - 5} more lines)")
            lines.append("")

        lines.append("  Locations:")
        for block in group.blocks:
            rel_path = os.path.relpath(block.file_path)
            lines.append(f"    - {rel_path}:{block.line_number}")

        lines.append("")

    return '\n'.join(lines)


def generate_csv_report(duplicate_groups: List[DuplicateGroup]) -> str:
    """
    Generate a CSV report of duplicate content.

    Returns:
        CSV formatted string
    """
    lines = ["Block Type,Similarity,Occurrences,File Path,Line Number,Content Preview"]

    for group in duplicate_groups:
        similarity_str = "exact" if group.similarity == 1.0 else f"{group.similarity:.2f}"
        # Escape content for CSV
        preview = group.canonical_content[:100].replace('"', '""').replace('\n', ' ')

        for block in group.blocks:
            rel_path = os.path.relpath(block.file_path)
            lines.append(f'"{group.block_type}","{similarity_str}",{len(group.blocks)},"{rel_path}",{block.line_number},"{preview}"')

    return '\n'.join(lines)

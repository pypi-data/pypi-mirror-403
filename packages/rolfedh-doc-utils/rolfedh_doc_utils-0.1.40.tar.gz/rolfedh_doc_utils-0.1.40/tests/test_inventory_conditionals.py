"""Tests for the inventory_conditionals module."""

import os
import tempfile
from pathlib import Path
from doc_utils.inventory_conditionals import (
    find_adoc_files,
    scan_file_for_conditionals,
    create_inventory,
    get_inventory_stats,
)


def make_file(path, content):
    """Helper to create a file with given content."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def test_find_adoc_files():
    """Test finding .adoc files recursively."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create some .adoc files
        make_file(tmppath / 'root.adoc', 'content')
        (tmppath / 'subdir').mkdir()
        make_file(tmppath / 'subdir' / 'nested.adoc', 'content')
        make_file(tmppath / 'other.txt', 'not adoc')

        files = find_adoc_files(tmppath)

        assert len(files) == 2
        names = [f.name for f in files]
        assert 'root.adoc' in names
        assert 'nested.adoc' in names
        assert 'other.txt' not in names


def test_scan_file_for_conditionals_ifdef():
    """Test detecting ifdef directives."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        adoc_file = tmppath / 'test.adoc'
        make_file(adoc_file, """= Title

ifdef::rh-only[]
Red Hat only content
endif::rh-only[]
""")

        results = scan_file_for_conditionals(adoc_file)

        assert len(results) == 2
        assert results[0] == (3, 'ifdef', 'rh-only[]')
        assert results[1] == (5, 'endif', 'rh-only[]')


def test_scan_file_for_conditionals_ifndef():
    """Test detecting ifndef directives."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        adoc_file = tmppath / 'test.adoc'
        make_file(adoc_file, """= Title

ifndef::no-feature[]
Feature content
endif::[]
""")

        results = scan_file_for_conditionals(adoc_file)

        assert len(results) == 2
        assert results[0] == (3, 'ifndef', 'no-feature[]')
        assert results[1] == (5, 'endif', '[]')


def test_scan_file_for_conditionals_ifeval():
    """Test detecting ifeval directives."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        adoc_file = tmppath / 'test.adoc'
        make_file(adoc_file, """= Title

ifeval::[2 > 1]
Always shown
endif::[]
""")

        results = scan_file_for_conditionals(adoc_file)

        assert len(results) == 2
        assert results[0] == (3, 'ifeval', '[2 > 1]')
        assert results[1] == (5, 'endif', '[]')


def test_scan_file_for_conditionals_inline():
    """Test detecting inline conditionals."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        adoc_file = tmppath / 'test.adoc'
        make_file(adoc_file, """= Title

ifdef::ibm-only[*Important:*]
Some content
""")

        results = scan_file_for_conditionals(adoc_file)

        assert len(results) == 1
        assert results[0] == (3, 'ifdef', 'ibm-only[*Important:*]')


def test_scan_file_no_conditionals():
    """Test file with no conditionals."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        adoc_file = tmppath / 'test.adoc'
        make_file(adoc_file, """= Title

This is plain content.
No conditionals here.
""")

        results = scan_file_for_conditionals(adoc_file)

        assert len(results) == 0


def test_create_inventory():
    """Test creating an inventory file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create .adoc files with conditionals
        make_file(tmppath / 'test1.adoc', """= Title
ifdef::rh-only[]
content
endif::rh-only[]
""")
        make_file(tmppath / 'test2.adoc', """= Title
ifndef::no-feature[]
content
endif::[]
""")

        output_file = create_inventory(tmppath, tmppath)

        assert output_file.exists()
        assert output_file.name.startswith('inventory-')
        assert output_file.name.endswith('.txt')

        content = output_file.read_text()

        assert 'AsciiDoc Conditionals Inventory' in content
        assert 'test1.adoc' in content
        assert 'test2.adoc' in content
        assert 'ifdef::rh-only[]' in content
        assert 'ifndef::no-feature[]' in content
        assert 'SUMMARY' in content
        assert 'UNIQUE CONDITIONS USED' in content


def test_get_inventory_stats():
    """Test getting statistics without creating a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create .adoc files with conditionals
        make_file(tmppath / 'test1.adoc', """ifdef::rh-only[]
content
endif::rh-only[]
ifdef::ibm-only[]
more
endif::ibm-only[]
""")
        make_file(tmppath / 'test2.adoc', """ifndef::no-feature[]
content
endif::[]
""")
        make_file(tmppath / 'test3.adoc', 'No conditionals here.')

        stats = get_inventory_stats(tmppath)

        assert stats['total_files'] == 3
        assert stats['files_with_conditionals'] == 2
        assert stats['directive_counts']['ifdef'] == 2
        assert stats['directive_counts']['ifndef'] == 1
        assert stats['directive_counts']['endif'] == 3
        assert stats['total_conditionals'] == 6
        assert 'rh-only' in stats['unique_conditions']
        assert 'ibm-only' in stats['unique_conditions']
        assert 'no-feature' in stats['unique_conditions']


def test_create_inventory_empty_directory():
    """Test creating inventory in a directory with no .adoc files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        output_file = create_inventory(tmppath, tmppath)

        assert output_file.exists()
        content = output_file.read_text()

        assert 'Total .adoc files scanned: 0' in content
        assert 'Files with conditionals: 0' in content


def test_create_inventory_nested_directories():
    """Test creating inventory with nested directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create nested structure
        (tmppath / 'modules').mkdir()
        (tmppath / 'assemblies').mkdir()

        make_file(tmppath / 'modules' / 'proc_test.adoc', """ifdef::rh-only[]
content
endif::rh-only[]
""")
        make_file(tmppath / 'assemblies' / 'assembly_test.adoc', """ifdef::ibm-only[]
content
endif::ibm-only[]
""")

        stats = get_inventory_stats(tmppath)

        assert stats['total_files'] == 2
        assert stats['files_with_conditionals'] == 2
        assert stats['unique_conditions']['rh-only'] == 1
        assert stats['unique_conditions']['ibm-only'] == 1

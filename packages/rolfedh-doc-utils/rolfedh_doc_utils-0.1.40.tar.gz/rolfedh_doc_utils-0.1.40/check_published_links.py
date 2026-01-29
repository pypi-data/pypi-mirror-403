#!/usr/bin/env python3
"""
Published Documentation Link Checker

Uses linkchecker to validate links on published HTML documentation pages with special handling for:
- Misresolved image paths (automatically corrected and verified via configurable URL rewriting)
- Known false positives (host:port placeholders, Maven Central 403)
- Timeout detection and reporting
- Custom ignore patterns via CLI or configuration file

Supports both single URL and bulk validation modes.

Usage:
    # Single URL
    ./check_published_links.py <URL> [--timeout SECONDS]

    # Bulk validation from file
    ./check_published_links.py --file <URL-LIST-FILE> [--timeout SECONDS]

    # With URL rewriting for misresolved paths
    ./check_published_links.py <URL> --rewrite-pattern "/docs/en/product/" --rewrite-replacement "/docs/en/PRODUCT_CODE_1.0/"

    # With custom ignore patterns
    ./check_published_links.py <URL> --ignore-pattern "^https?://internal\\.example\\.com"

    # Using a configuration file
    ./check_published_links.py <URL> --config linkcheck.conf

Examples:
    # Single URL
    ./check_published_links.py https://docs.example.com/guide/index.html
    ./check_published_links.py https://docs.example.com/guide/index.html --timeout 90

    # Bulk validation
    ./check_published_links.py --file urls-to-check.txt
    ./check_published_links.py --file urls-to-check.txt --timeout 90

    # With URL rewriting for documentation platforms that misresolve relative paths
    ./check_published_links.py https://docs.example.com/product/guide \\
        --rewrite-pattern "/docs/en/product/" \\
        --rewrite-replacement "/docs/en/PRODUCT_V1.0/"

    # With custom ignore patterns
    ./check_published_links.py https://docs.example.com/guide/ \\
        --ignore-pattern "^https?://internal\\.example\\.com" \\
        --ignore-pattern "^https?://staging\\."

Configuration File:
    Create a file (default: .check-published-links.conf) with options:

    # General settings
    [settings]
    timeout = 30
    reports-dir = ./build/link-reports/

    # Ignore patterns (one regex per line)
    [ignore-patterns]
    ^https?://internal\\.example\\.com
    ^https?://staging\\.
    ^https?://private-api\\.

    # Rewrite rules (pattern = replacement)
    [rewrite-rules]
    /docs/en/product/ = /docs/en/PRODUCT_V1.0/
    /docs/en/product/images/ = /docs/en/PRODUCT_V1.0/images/
"""

import subprocess
import sys
import re
import argparse
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
import urllib.request
import urllib.error

# Configuration
DEFAULT_TIMEOUT = 15
REPORTS_DIR = Path("reports")
DEFAULT_CONFIG_FILE = Path(".check-published-links.conf")

# ANSI colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


# Default ignore URL patterns for linkchecker
DEFAULT_IGNORE_PATTERNS = [
    r"^https?://localhost(:[0-9]+)?(/.*)?$",
    r"^https?://127\.0\.0\.1(:[0-9]+)?(/.*)?$",
    r"^https?://([a-zA-Z0-9-]+\.)?example\.(com|org)(/.*)?$",
    r"^https?://([a-zA-Z0-9-]+\.)?application\.com(/.*)?$",
    r"^https?://host:port",
    r".*,.*",
    r".*%2C.*",
]


# =============================================================================
# Configuration file parsing
# =============================================================================

@dataclass
class Config:
    """Configuration loaded from file."""
    timeout: int | None = None
    reports_dir: Path | None = None
    ignore_patterns: list = field(default_factory=list)
    rewrite_rules: list = field(default_factory=list)  # list of (pattern, replacement) tuples


def load_config_file(config_path: Path) -> Config:
    """
    Load configuration from file.

    Returns:
        Config object with all settings
    """
    config = Config()

    if not config_path.exists():
        return config

    current_section = None

    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Check for section headers
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].lower()
                continue

            # Parse based on current section
            if current_section == 'settings':
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key == 'timeout':
                        try:
                            config.timeout = int(value)
                        except ValueError:
                            pass  # Ignore invalid timeout values
                    elif key == 'reports-dir':
                        config.reports_dir = Path(value)
            elif current_section == 'ignore-patterns':
                config.ignore_patterns.append(line)
            elif current_section == 'rewrite-rules':
                if '=' in line:
                    pattern, replacement = line.split('=', 1)
                    config.rewrite_rules.append((pattern.strip(), replacement.strip()))

    return config


@dataclass
class RewriteRule:
    """URL rewrite rule for correcting misresolved paths."""
    pattern: str
    replacement: str

    def matches(self, url: str) -> bool:
        """Check if URL matches the pattern."""
        return self.pattern in url

    def apply(self, url: str) -> str:
        """Apply the rewrite rule to the URL."""
        return url.replace(self.pattern, self.replacement)


@dataclass
class LinkError:
    """Represents a single link error from linkchecker."""
    url: str = ""
    name: str = ""
    parent_url: str = ""
    real_url: str = ""
    check_time: str = ""
    result: str = ""


@dataclass
class CheckResult:
    """Results from link checking a single URL."""
    url: str = ""
    guide_name: str = ""
    total_errors: int = 0
    total_links: int = 0
    known_issues: int = 0
    timeout_errors: int = 0
    maven_403: int = 0
    rewritten_valid: int = 0
    rewritten_not_found: int = 0
    errors: list = field(default_factory=list)
    passed: bool = True
    raw_output: str = ""


@dataclass
class BulkResult:
    """Results from bulk link checking."""
    total_guides: int = 0
    passed_count: int = 0
    failed_count: int = 0
    total_known_issues: int = 0
    total_timeout_errors: int = 0
    total_rewritten_valid: int = 0
    total_rewritten_not_found: int = 0
    guide_results: list = field(default_factory=list)


# =============================================================================
# Output helpers
# =============================================================================

def info(msg: str):
    print(f"{Colors.BLUE}ℹ{Colors.NC} {msg}")


def success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}")


def error(msg: str):
    print(f"{Colors.RED}✗{Colors.NC} {msg}", file=sys.stderr)


def warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.NC} {msg}")


# =============================================================================
# Core link checking functions
# =============================================================================

def check_linkchecker_installed() -> bool:
    """Check if linkchecker is available."""
    try:
        subprocess.run(["linkchecker", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def is_rewritable_path(url: str, rewrite_rules: list[RewriteRule]) -> bool:
    """Check if URL matches any rewrite rule."""
    return any(rule.matches(url) for rule in rewrite_rules)


def get_rewritten_url(url: str, rewrite_rules: list[RewriteRule]) -> str:
    """Apply the first matching rewrite rule to the URL."""
    for rule in rewrite_rules:
        if rule.matches(url):
            return rule.apply(url)
    return url


def check_rewritten_url(wrong_url: str, rewrite_rules: list[RewriteRule]) -> tuple[bool, str]:
    """Verify resource exists at corrected path."""
    correct_url = get_rewritten_url(wrong_url, rewrite_rules)
    try:
        req = urllib.request.Request(correct_url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; LinkChecker)')
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status in (200, 302, 301), correct_url
    except urllib.error.HTTPError as e:
        if e.code in (302, 301):
            return True, correct_url
        return False, correct_url
    except (urllib.error.URLError, TimeoutError):
        return False, correct_url


def run_linkchecker(url: str, timeout: int, ignore_patterns: list[str] = None) -> tuple[int, str]:
    """Run linkchecker and return (exit_code, output)."""
    if ignore_patterns is None:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS

    cmd = [
        "linkchecker",
        "--check-extern",
        "--no-follow-url=.*",
        "--no-warnings",
        f"--timeout={timeout}",
    ]

    for pattern in ignore_patterns:
        cmd.append(f"--ignore-url={pattern}")

    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def extract_guide_name(url: str) -> str:
    """Extract a readable guide name from URL."""
    # Try common documentation URL patterns
    # Pattern: /html-single/guide-name/
    match = re.search(r'/html-single/([^/]+)/', url)
    if match:
        return match.group(1).replace('_', ' ')

    # Pattern: ?topic=guide-name
    match = re.search(r'\?topic=(.+)$', url)
    if match:
        return match.group(1)

    # Pattern: /guide-name/index.html or /guide-name.html
    match = re.search(r'/([^/]+?)(?:/index)?\.html?$', url)
    if match:
        return match.group(1).replace('-', ' ').replace('_', ' ')

    # Fallback
    return url.split('/')[-1] or url


def parse_linkchecker_output(output: str) -> CheckResult:
    """Parse linkchecker output and extract error details."""
    result = CheckResult(raw_output=output)

    # Extract total error count
    error_match = re.search(r'(\d+)\s+error', output)
    if error_match:
        result.total_errors = int(error_match.group(1))

    # Extract link count
    link_match = re.search(r'(\d+)\s+link', output)
    if link_match:
        result.total_links = int(link_match.group(1))

    # Count known issues
    result.known_issues = output.count("URL host 'host:port' has invalid port")

    # Count timeout errors
    result.timeout_errors = len(re.findall(r'ReadTimeout|Timeout', output))

    # Detect Maven Central 403
    if 'search.maven.org' in output and '403 Forbidden' in output:
        result.maven_403 = output.count('search.maven.org')

    # Parse individual errors
    current_error = LinkError()
    for line in output.split('\n'):
        if line.startswith('URL ') and not line.startswith('URL lengths'):
            if current_error.url:
                result.errors.append(current_error)
            current_error = LinkError()
            current_error.url = line[4:].strip().strip('`\'')
        elif line.startswith('Name '):
            current_error.name = line[5:].strip().strip('`\'')
        elif line.startswith('Parent URL'):
            current_error.parent_url = line[10:].strip()
        elif line.startswith('Real URL'):
            current_error.real_url = line[8:].strip()
        elif line.startswith('Check time'):
            current_error.check_time = line[10:].strip()
        elif line.startswith('Result'):
            current_error.result = line[6:].strip()

    if current_error.url:
        result.errors.append(current_error)

    return result


def verify_rewritten_paths(result: CheckResult, rewrite_rules: list[RewriteRule]) -> CheckResult:
    """Check misresolved paths at corrected paths using rewrite rules."""
    if not rewrite_rules:
        return result

    verified_urls = set()

    for err in result.errors:
        real_url = err.real_url
        if is_rewritable_path(real_url, rewrite_rules):
            exists, _ = check_rewritten_url(real_url, rewrite_rules)
            if exists:
                result.rewritten_valid += 1
                verified_urls.add(real_url)
            else:
                result.rewritten_not_found += 1

    # Filter out verified paths from errors list
    result.errors = [e for e in result.errors if e.real_url not in verified_urls]

    return result


def check_single_url(url: str, timeout: int, rewrite_rules: list[RewriteRule] = None,
                     ignore_patterns: list[str] = None) -> CheckResult:
    """Check a single URL and return results."""
    rewrite_rules = rewrite_rules or []
    result = CheckResult(url=url, guide_name=extract_guide_name(url))

    exit_code, output = run_linkchecker(url, timeout, ignore_patterns)
    result.raw_output = output

    if exit_code == 0:
        # Success
        link_match = re.search(r'(\d+)\s+link', output)
        result.total_links = int(link_match.group(1)) if link_match else 0
        result.passed = True
        return result

    # Parse errors
    parsed = parse_linkchecker_output(output)
    result.total_errors = parsed.total_errors
    result.total_links = parsed.total_links
    result.known_issues = parsed.known_issues
    result.timeout_errors = parsed.timeout_errors
    result.maven_403 = parsed.maven_403
    result.errors = parsed.errors

    # Verify rewritten paths
    result = verify_rewritten_paths(result, rewrite_rules)

    # Determine if passed (all errors were false positives)
    adjusted_errors = result.total_errors - result.rewritten_valid
    real_errors = adjusted_errors - result.known_issues
    result.passed = real_errors <= 0

    return result


# =============================================================================
# Helper functions for bulk mode
# =============================================================================

def load_urls(url_list_file: Path) -> list[str]:
    """Load URLs from file, skipping comments and empty lines."""
    urls = []
    with open(url_list_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)
    return urls


# =============================================================================
# Report generation
# =============================================================================

def generate_single_report(url: str, guide_name: str, timeout: int, result: CheckResult,
                          rewrite_rules: list[RewriteRule] = None) -> str:
    """Generate report for single URL check."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")

    # Calculate adjusted error count
    adjusted_errors = result.total_errors - result.rewritten_valid
    real_errors = adjusted_errors - result.known_issues

    if real_errors <= 0:
        status = "PASSED (all errors were false positives)"
        status_icon = "✓"
    else:
        status = "FAILED"
        status_icon = "✗"

    report = f"""================================================================================
Documentation Link Check Report
================================================================================
Date: {timestamp}
URL: {url}
Guide: {guide_name}
Timeout: {timeout} seconds

================================================================================
SUMMARY
================================================================================

{status_icon} {guide_name} ({adjusted_errors} errors"""

    if result.rewritten_valid > 0:
        report += f", {result.rewritten_valid} rewritten paths OK"
    if result.known_issues > 0:
        report += f", {result.known_issues} known"
    if result.timeout_errors > 0:
        report += f", {result.timeout_errors} TIMEOUT"
    report += ")\n"

    report += f"""
================================================================================
STATISTICS
================================================================================
Total Errors Reported: {result.total_errors}
Rewritten Paths Verified OK: {result.rewritten_valid}
Rewritten Paths NOT Found: {result.rewritten_not_found}
Adjusted Error Count: {adjusted_errors}
Known Issues Found: {result.known_issues} (safe to ignore)
Timeout Errors: {result.timeout_errors}
Status: {status}
"""

    report += _generate_known_issues_section(rewrite_rules)

    if result.timeout_errors > 0:
        report += f"""
================================================================================
*** TIMEOUT LIMIT REACHED ***
================================================================================

{result.timeout_errors} links exceeded the timeout limit of {timeout} seconds.

This indicates slow server responses or network issues, not broken links.

RECOMMENDED ACTION:
Re-run with increased timeout: --timeout {timeout + 30}

Timeout errors should be investigated separately from broken links.
"""

    # Add detailed error information if there are real errors
    if result.errors:
        report += f"""
================================================================================
DETAILED ERROR INFORMATION
================================================================================

The following section provides detailed error information.
This allows you to trace specific failures to exact URLs and error messages.

════════════════════════════════════════════════════════════════
FAILED GUIDE: {guide_name}
════════════════════════════════════════════════════════════════
URL: {url}
Total Errors: {len(result.errors)}
"""
        if result.rewritten_valid > 0:
            report += f"Rewritten Paths Verified OK: {result.rewritten_valid}\n"
        if result.rewritten_not_found > 0:
            report += f"Rewritten Paths NOT Found: {result.rewritten_not_found}\n"

        report += _generate_error_details(result.errors)

    return report


def generate_bulk_report(url_list_file: Path, timeout: int, bulk_result: BulkResult,
                        rewrite_rules: list[RewriteRule] = None) -> str:
    """Generate report for bulk URL check."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")

    report = f"""================================================================================
Documentation Link Check Report
================================================================================
Date: {timestamp}
Total Guides Checked: {bulk_result.total_guides}
URL List: {url_list_file}
Timeout: {timeout} seconds

================================================================================
SUMMARY
================================================================================

"""

    # Add summary line for each guide
    for guide in bulk_result.guide_results:
        if guide.passed:
            line = f"✓ {guide.guide_name}"
            if guide.total_links:
                line += f" ({guide.total_links} links)"
            if guide.rewritten_valid > 0:
                line += f" [{guide.rewritten_valid} rewritten OK]"
        else:
            adjusted = guide.total_errors - guide.rewritten_valid
            line = f"✗ {guide.guide_name} ({adjusted} errors"
            if guide.rewritten_valid > 0:
                line += f", {guide.rewritten_valid} rewritten OK"
            if guide.known_issues > 0:
                line += f", {guide.known_issues} known"
            if guide.timeout_errors > 0:
                line += f", {guide.timeout_errors} TIMEOUT"
            line += ")"
        report += line + "\n"

    # Statistics
    success_rate = (bulk_result.passed_count / bulk_result.total_guides * 100) if bulk_result.total_guides > 0 else 0

    report += f"""
================================================================================
STATISTICS
================================================================================
Total Guides Checked: {bulk_result.total_guides}
Passed: {bulk_result.passed_count}
Failed: {bulk_result.failed_count}
Rewritten Paths Verified OK: {bulk_result.total_rewritten_valid}
Rewritten Paths NOT Found: {bulk_result.total_rewritten_not_found}
Known Issues Found: {bulk_result.total_known_issues} (safe to ignore)
Timeout Errors: {bulk_result.total_timeout_errors}
Success Rate: {success_rate:.1f}%
"""

    report += _generate_known_issues_section(rewrite_rules)

    # Timeout warning if any
    if bulk_result.total_timeout_errors > 0:
        report += f"""
================================================================================
*** TIMEOUT LIMIT REACHED ***
================================================================================

{bulk_result.total_timeout_errors} links exceeded the timeout limit of {timeout} seconds.

This indicates slow server responses or network issues, not broken links.

RECOMMENDED ACTION:
Re-run with increased timeout: --file {url_list_file} --timeout {timeout + 30}

Timeout errors should be investigated separately from broken links.
"""

    # Detailed errors for failed guides
    failed_guides = [g for g in bulk_result.guide_results if not g.passed]
    if failed_guides:
        report += """
================================================================================
DETAILED ERROR INFORMATION BY GUIDE
================================================================================

The following section provides detailed error information for each failed guide.
This allows you to trace specific failures to exact URLs and error messages.
"""

        for guide in failed_guides:
            report += f"""
════════════════════════════════════════════════════════════════
FAILED GUIDE: {guide.guide_name}
════════════════════════════════════════════════════════════════
URL: {guide.url}
Total Errors: {len(guide.errors)}
"""
            if guide.rewritten_valid > 0:
                report += f"Rewritten Paths Verified OK: {guide.rewritten_valid}\n"
            if guide.rewritten_not_found > 0:
                report += f"Rewritten Paths NOT Found: {guide.rewritten_not_found}\n"
            if guide.known_issues > 0:
                report += f"Known Issues: {guide.known_issues} (host:port errors - safe to ignore)\n"
            if guide.timeout_errors > 0:
                report += f"\n*** TIMEOUT LIMIT REACHED: {guide.timeout_errors} links ***\n"
                report += f"Consider increasing timeout: --file {url_list_file} --timeout {timeout + 30}\n"

            report += _generate_error_details(guide.errors)

    return report


def _generate_known_issues_section(rewrite_rules: list[RewriteRule] = None) -> str:
    """Generate the known issues section for reports."""
    section = """
================================================================================
KNOWN ISSUES (Safe to Ignore)
================================================================================

The following errors are expected due to LinkChecker limitations:

1. "URL host 'host:port' has invalid port"
   - URLs like https://host:port/auth or https://host:port/realms/{realm}
   - These are documentation placeholders using literal "port" text
   - LinkChecker cannot skip syntax-invalid URLs
   - Safe to ignore - not real broken links

2. Comma-separated URL lists
   - URLs like http://www.example.com,http://localhost:3000
   - These are examples showing configuration format
   - Already filtered by ignore patterns
   - Should not appear in error logs

3. Maven Central 403 Forbidden errors
   - URLs like https://search.maven.org/artifact/...
   - Maven Central blocks automated bots/scrapers with 403 Forbidden
   - These links work fine for humans in a web browser
   - Verify manually if needed - not broken documentation
"""

    if rewrite_rules:
        section += """
4. Misresolved image/resource paths (AUTOMATICALLY VERIFIED)
   - Some documentation platforms use URL routing that causes LinkChecker
     to resolve relative paths against an incorrect base URL
   - This script automatically verifies resources at the corrected path
   - If verified OK, the error is NOT counted; if not found, it IS a real error
"""

    section += """
If you see these errors, they do NOT indicate broken documentation.
All other errors should be investigated and fixed.
"""
    return section


def _generate_error_details(errors: list) -> str:
    """Generate error details section."""
    report = """
Error Details:
────────────────────────────────────────────────────────────────
"""
    for err in errors:
        report += f"URL        {err.url}\n"
        if err.name:
            report += f"Name       {err.name}\n"
        if err.parent_url:
            report += f"Parent URL {err.parent_url}\n"
        if err.real_url:
            report += f"Real URL   {err.real_url}\n"
        if err.check_time:
            report += f"Check time {err.check_time}\n"
        if err.result:
            report += f"Result     {err.result}\n"
        report += "\n"
    return report


# =============================================================================
# Main entry points
# =============================================================================

def run_single_mode(url: str, timeout: int, rewrite_rules: list[RewriteRule] = None,
                    ignore_patterns: list[str] = None, reports_dir: Path = None):
    """Run link checker for a single URL."""
    rewrite_rules = rewrite_rules or []
    reports_dir = reports_dir or REPORTS_DIR

    # Setup
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = reports_dir / f"link-check-report_{timestamp}.txt"
    guide_name = extract_guide_name(url)

    # Print header
    print()
    print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.CYAN}  Documentation Link Checker{Colors.NC}")
    print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.NC}")
    print()
    info(f"URL: {url}")
    info(f"Guide: {guide_name}")
    info(f"Timeout: {timeout} seconds")
    if rewrite_rules:
        info(f"Rewrite rules: {len(rewrite_rules)}")
    if ignore_patterns and ignore_patterns != DEFAULT_IGNORE_PATTERNS:
        info(f"Custom ignore patterns: {len(ignore_patterns) - len(DEFAULT_IGNORE_PATTERNS)} added")
    info(f"Report: {report_file}")
    print()

    # Run linkchecker
    result = check_single_url(url, timeout, rewrite_rules, ignore_patterns)

    if result.passed and result.total_errors == 0:
        # Complete success
        print(f"{Colors.GREEN}✓ PASS{Colors.NC} - {result.total_links} links checked")
        print()

        # Generate simple success report
        report = f"""================================================================================
Documentation Link Check Report
================================================================================
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")}
URL: {url}
Guide: {guide_name}
Timeout: {timeout} seconds

================================================================================
SUMMARY
================================================================================

✓ {guide_name} ({result.total_links} links)

================================================================================
STATISTICS
================================================================================
Total Links Checked: {result.total_links}
Status: PASSED
Success Rate: 100.0%

All documentation links are valid!
"""
        report_file.write_text(report)
        info(f"Report saved to: {report_file}")
        print()
        success("All documentation links are valid!")
        return 0

    # Calculate real errors
    adjusted_errors = result.total_errors - result.rewritten_valid
    real_errors = adjusted_errors - result.known_issues

    # Print summary
    if real_errors <= 0:
        print(f"{Colors.GREEN}✓ PASS{Colors.NC} - All errors were false positives")
        if result.rewritten_valid > 0:
            print(f"  {Colors.BLUE}Note:{Colors.NC} {result.rewritten_valid} path(s) verified at corrected location")
        if result.known_issues > 0:
            print(f"  {Colors.YELLOW}Note:{Colors.NC} {result.known_issues} known issues (host:port) - safe to ignore")
    else:
        print(f"{Colors.RED}✗ FAIL{Colors.NC} - {adjusted_errors} errors found")
        if result.rewritten_valid > 0:
            print(f"  {Colors.BLUE}Note:{Colors.NC} {result.rewritten_valid} path(s) verified at corrected location (not counted)")
        if result.rewritten_not_found > 0:
            print(f"  {Colors.RED}Error:{Colors.NC} {result.rewritten_not_found} path(s) NOT FOUND at corrected location")
        if result.known_issues > 0:
            print(f"  {Colors.YELLOW}Note:{Colors.NC} {result.known_issues} known issues (host:port) - safe to ignore")
        if result.timeout_errors > 0:
            print(f"  {Colors.RED}TIMEOUT:{Colors.NC} {result.timeout_errors} links exceeded timeout limit")
    print()

    # Generate and save report
    report = generate_single_report(url, guide_name, timeout, result, rewrite_rules)
    report_file.write_text(report)

    info(f"Report saved to: {report_file}")

    if result.rewritten_valid > 0:
        info(f"{result.rewritten_valid} path(s) verified at corrected location")

    if result.known_issues > 0:
        warning(f"{result.known_issues} known issues found (host:port errors) - safe to ignore")

    if result.timeout_errors > 0:
        print()
        error("════════════════════════════════════════════════════════════════")
        error("  TIMEOUT LIMIT REACHED")
        error("════════════════════════════════════════════════════════════════")
        error(f"{result.timeout_errors} links exceeded the timeout limit of {timeout} seconds")
        error(f'Consider increasing timeout: --timeout {timeout + 30}')
        error("════════════════════════════════════════════════════════════════")

    print()
    if real_errors <= 0:
        success("All documentation links are valid!")
        return 0
    else:
        warning("Link check found issues. Review the report for details.")
        return 1


def run_bulk_mode(url_list_file: Path, timeout: int, rewrite_rules: list[RewriteRule] = None,
                  ignore_patterns: list[str] = None, reports_dir: Path = None):
    """Run link checker for multiple URLs from a file."""
    rewrite_rules = rewrite_rules or []
    reports_dir = reports_dir or REPORTS_DIR

    # Load URLs
    urls = load_urls(url_list_file)
    total_urls = len(urls)

    if total_urls == 0:
        error(f"No URLs found in {url_list_file}")
        return 1

    # Setup
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = reports_dir / f"link-check-report_{timestamp}.txt"

    # Print header
    print()
    print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.CYAN}  Documentation Link Checker - Bulk Mode{Colors.NC}")
    print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.NC}")
    print()
    info(f"URL List: {url_list_file}")
    info(f"Total URLs: {total_urls}")
    info(f"Timeout: {timeout} seconds")
    if rewrite_rules:
        info(f"Rewrite rules: {len(rewrite_rules)}")
    if ignore_patterns and ignore_patterns != DEFAULT_IGNORE_PATTERNS:
        info(f"Custom ignore patterns: {len(ignore_patterns) - len(DEFAULT_IGNORE_PATTERNS)} added")
    info(f"Report: {report_file}")
    print()

    # Process each URL
    bulk_result = BulkResult(total_guides=total_urls)

    for i, url in enumerate(urls, 1):
        guide_name = extract_guide_name(url)
        print(f"{Colors.CYAN}[{i}/{total_urls}]{Colors.NC} Checking: {guide_name}...")

        result = check_single_url(url, timeout, rewrite_rules, ignore_patterns)
        bulk_result.guide_results.append(result)

        if result.passed:
            bulk_result.passed_count += 1
            links_info = f"{result.total_links} links" if result.total_links else "OK"
            rewritten_info = f" [{result.rewritten_valid} rewritten OK]" if result.rewritten_valid > 0 else ""
            print(f"  {Colors.GREEN}✓ PASS{Colors.NC} - {links_info}{rewritten_info}")
        else:
            bulk_result.failed_count += 1
            adjusted = result.total_errors - result.rewritten_valid
            print(f"  {Colors.RED}✗ FAIL{Colors.NC} - {adjusted} errors found")
            if result.rewritten_valid > 0:
                print(f"    {Colors.BLUE}Note:{Colors.NC} {result.rewritten_valid} path(s) verified OK (not counted)")
            if result.rewritten_not_found > 0:
                print(f"    {Colors.RED}Error:{Colors.NC} {result.rewritten_not_found} path(s) NOT FOUND")
            if result.known_issues > 0:
                print(f"    {Colors.YELLOW}Note:{Colors.NC} {result.known_issues} known issues (host:port) - safe to ignore")
            if result.timeout_errors > 0:
                print(f"    {Colors.RED}TIMEOUT:{Colors.NC} {result.timeout_errors} links exceeded timeout limit")

        # Accumulate totals
        bulk_result.total_known_issues += result.known_issues
        bulk_result.total_timeout_errors += result.timeout_errors
        bulk_result.total_rewritten_valid += result.rewritten_valid
        bulk_result.total_rewritten_not_found += result.rewritten_not_found

    # Generate and save report
    report = generate_bulk_report(url_list_file, timeout, bulk_result, rewrite_rules)
    report_file.write_text(report)

    # Print final summary
    print()
    print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.NC}")
    print(f"{Colors.CYAN}  Results{Colors.NC}")
    print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.NC}")
    print()
    print(f"  Total:  {total_urls} guides")
    print(f"  {Colors.GREEN}Pass:   {bulk_result.passed_count}{Colors.NC}")
    print(f"  {Colors.RED}Fail:   {bulk_result.failed_count}{Colors.NC}")
    if bulk_result.total_rewritten_valid > 0:
        print(f"  {Colors.BLUE}Rewritten OK: {bulk_result.total_rewritten_valid} paths verified{Colors.NC}")
    if bulk_result.total_rewritten_not_found > 0:
        print(f"  {Colors.RED}Rewritten Missing: {bulk_result.total_rewritten_not_found} paths{Colors.NC}")
    if bulk_result.total_known_issues > 0:
        print(f"  {Colors.YELLOW}Known:  {bulk_result.total_known_issues} issues (safe to ignore){Colors.NC}")
    if bulk_result.total_timeout_errors > 0:
        print(f"  {Colors.RED}Timeout: {bulk_result.total_timeout_errors} links{Colors.NC}")

    success_rate = (bulk_result.passed_count / total_urls * 100) if total_urls > 0 else 0
    print(f"  Rate:   {success_rate:.1f}%")
    print()
    info(f"Report saved to: {report_file}")

    if bulk_result.total_known_issues > 0:
        warning(f"{bulk_result.total_known_issues} known issues found (host:port errors) - safe to ignore")

    if bulk_result.total_timeout_errors > 0:
        print()
        error("════════════════════════════════════════════════════════════════")
        error("  TIMEOUT LIMIT REACHED")
        error("════════════════════════════════════════════════════════════════")
        error(f"{bulk_result.total_timeout_errors} links exceeded the timeout limit of {timeout} seconds")
        error(f"Consider increasing timeout: --file {url_list_file} --timeout {timeout + 30}")
        error("════════════════════════════════════════════════════════════════")

    print()
    if bulk_result.failed_count == 0:
        success("All documentation links are valid!")
        return 0
    else:
        warning("Some documentation links have issues. Review the report for details.")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Published Documentation Link Checker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single URL
  %(prog)s https://docs.example.com/guide/index.html
  %(prog)s https://docs.example.com/guide/index.html --timeout 90

  # Bulk validation from file
  %(prog)s --file urls-to-check.txt
  %(prog)s --file urls-to-check.txt --timeout 90

  # With URL rewriting for misresolved paths
  %(prog)s https://docs.example.com/product/guide \\
      --rewrite-pattern "/docs/en/product/" \\
      --rewrite-replacement "/docs/en/PRODUCT_V1.0/"

  # With custom ignore patterns
  %(prog)s https://docs.example.com/guide/ \\
      --ignore-pattern "^https?://internal\\.example\\.com" \\
      --ignore-pattern "^https?://staging\\."

  # Using a configuration file
  %(prog)s https://docs.example.com/guide/ --config linkcheck.conf
"""
    )
    parser.add_argument('url', nargs='?',
                        help='Single URL to check')
    parser.add_argument('--file', '-f', type=Path, dest='url_list',
                        help='File containing URLs to check (one per line)')
    parser.add_argument('--timeout', '-t', type=int, default=DEFAULT_TIMEOUT,
                        help=f'Timeout for each link check in seconds (default: {DEFAULT_TIMEOUT})')
    parser.add_argument('--rewrite-pattern', action='append', dest='rewrite_patterns',
                        help='URL pattern to match for rewriting (can be used multiple times)')
    parser.add_argument('--rewrite-replacement', action='append', dest='rewrite_replacements',
                        help='Replacement for matched pattern (must match --rewrite-pattern count)')
    parser.add_argument('--ignore-pattern', action='append', dest='ignore_patterns',
                        help='Regex pattern for URLs to ignore (can be used multiple times)')
    parser.add_argument('--config', '-c', type=Path, dest='config_file',
                        help=f'Configuration file (default: {DEFAULT_CONFIG_FILE} if it exists)')
    parser.add_argument('--reports-dir', type=Path, dest='reports_dir',
                        help=f'Directory for reports (default: {REPORTS_DIR})')

    args = parser.parse_args()

    # Check linkchecker is installed
    if not check_linkchecker_installed():
        error("linkchecker is not installed")
        print()
        print("Install with: pipx install linkchecker")
        sys.exit(1)

    # Load configuration file
    config_path = args.config_file if args.config_file else DEFAULT_CONFIG_FILE
    config = load_config_file(config_path)

    if config_path.exists() and (config.ignore_patterns or config.rewrite_rules or
                                  config.timeout is not None or config.reports_dir is not None):
        info(f"Loaded configuration from {config_path}")

    # Determine timeout: CLI > config file > default
    if args.timeout != DEFAULT_TIMEOUT:
        timeout = args.timeout  # CLI explicitly set
    elif config.timeout is not None:
        timeout = config.timeout  # From config file
    else:
        timeout = DEFAULT_TIMEOUT

    # Determine reports directory: CLI > config file > default
    if args.reports_dir is not None:
        reports_dir = args.reports_dir
    elif config.reports_dir is not None:
        reports_dir = config.reports_dir
    else:
        reports_dir = REPORTS_DIR

    # Build ignore patterns: defaults + config file + CLI
    ignore_patterns = DEFAULT_IGNORE_PATTERNS.copy()
    if config.ignore_patterns:
        ignore_patterns.extend(config.ignore_patterns)
    if args.ignore_patterns:
        ignore_patterns.extend(args.ignore_patterns)

    # Parse rewrite rules: config file + CLI
    rewrite_rules = []
    for pattern, replacement in config.rewrite_rules:
        rewrite_rules.append(RewriteRule(pattern=pattern, replacement=replacement))
    if args.rewrite_patterns:
        if not args.rewrite_replacements or len(args.rewrite_patterns) != len(args.rewrite_replacements):
            error("--rewrite-pattern and --rewrite-replacement must be used in pairs")
            sys.exit(1)
        for pattern, replacement in zip(args.rewrite_patterns, args.rewrite_replacements):
            rewrite_rules.append(RewriteRule(pattern=pattern, replacement=replacement))

    # Determine mode
    if args.url_list:
        # Bulk mode from file
        if not args.url_list.exists():
            error(f"URL list not found: {args.url_list}")
            sys.exit(1)
        sys.exit(run_bulk_mode(args.url_list, timeout, rewrite_rules, ignore_patterns, reports_dir))

    elif args.url:
        # Single URL mode
        sys.exit(run_single_mode(args.url, timeout, rewrite_rules, ignore_patterns, reports_dir))

    else:
        # No arguments - show help
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

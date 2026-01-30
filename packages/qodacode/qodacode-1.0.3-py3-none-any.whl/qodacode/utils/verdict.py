"""
Qodacode Verdict Utilities - Shared logic for TUI/CLI/MCP consistency.

This module ensures that all interfaces (TUI, CLI, MCP) produce
identical results and verdicts.
"""

import os
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────────────────
# BRAND COLORS (consistent across all interfaces)
# ─────────────────────────────────────────────────────────────────────────────
QODACODE_ORANGE = "#DA7028"
QODACODE_ORANGE_LIGHT = "#F97316"

SEVERITY_COLORS = {
    "critical": "red",
    "high": "#DA7028",  # Orange (brand color for HIGH, not blocking)
    "medium": "yellow",
    "low": "blue",
    "info": "dim",
}

SEVERITY_ICONS = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
    "info": "⚪",
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


# ─────────────────────────────────────────────────────────────────────────────
# TEST FILE DETECTION
# ─────────────────────────────────────────────────────────────────────────────
def is_test_file(filepath: str) -> bool:
    """
    Check if a file is a test file.

    Test files are excluded from production verdict calculations.

    Patterns detected:
    - test_*.py, *_test.py
    - *.test.js, *.test.ts, *.spec.js, *.spec.ts
    - Files in /tests/, /__tests__/, /test/ directories
    """
    if not filepath:
        return False

    name = os.path.basename(filepath).lower()
    path_lower = filepath.lower()

    # Python test patterns
    if name.startswith("test_") or name.endswith("_test.py"):
        return True

    # JavaScript/TypeScript test patterns
    if ".test." in name or ".spec." in name:
        return True

    # Test directory patterns
    test_dirs = ["/tests/", "/__tests__/", "/test/", "\\tests\\", "\\__tests__\\", "\\test\\"]
    for test_dir in test_dirs:
        if test_dir in path_lower:
            return True

    return False


# ─────────────────────────────────────────────────────────────────────────────
# VERDICT CALCULATION
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SeverityCounts:
    """Issue counts by severity."""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0

    @property
    def total(self) -> int:
        return self.critical + self.high + self.medium + self.low

    def to_dict(self) -> Dict[str, int]:
        return {
            "critical": self.critical,
            "high": self.high,
            "medium": self.medium,
            "low": self.low,
            "total": self.total,
        }


@dataclass
class ScanSummary:
    """
    Complete scan summary with production and test issues separated.

    This is the single source of truth for all interfaces (CLI, TUI, MCP).
    """
    # Production issues (affect verdict)
    production: SeverityCounts
    # Test issues (excluded from verdict, shown for visibility)
    tests: SeverityCounts
    # Verdict based on production issues only
    ready: bool
    message: str

    @property
    def verdict_icon(self) -> str:
        return "✅" if self.ready else "⛔"

    @property
    def total_issues(self) -> int:
        return self.production.total + self.tests.total

    def to_dict(self) -> Dict[str, Any]:
        """Return dict for JSON serialization (MCP)."""
        return {
            "verdict": self.message,
            "ready_for_production": self.ready,
            "production": self.production.to_dict(),
            "tests": self.tests.to_dict(),
            "total_issues": self.total_issues,
        }


@dataclass
class Verdict:
    """Production readiness verdict (legacy, use ScanSummary for new code)."""
    ready: bool
    message: str
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

    @property
    def icon(self) -> str:
        return "✅" if self.ready else "⛔"

    @property
    def status_text(self) -> str:
        if self.ready:
            if self.high_count > 0:
                return f"READY FOR PRODUCTION ({self.high_count} warnings)"
            return "READY FOR PRODUCTION"
        return f"NOT READY — Fix {self.critical_count} critical issues"


def calculate_verdict(issues: List[Any], exclude_tests: bool = True) -> Verdict:
    """
    Calculate production readiness verdict.

    Logic (unified across TUI/CLI/MCP):
    - 0 critical issues → READY FOR PRODUCTION
    - 1+ critical issues → NOT READY
    - HIGH/MEDIUM/LOW are warnings, not blockers

    Args:
        issues: List of Issue objects with severity and location attributes
        exclude_tests: If True, exclude test files from verdict calculation

    Returns:
        Verdict object with ready status and counts
    """
    critical = 0
    high = 0
    medium = 0
    low = 0

    for issue in issues:
        # Get filepath - handle different attribute structures
        filepath = ""
        if hasattr(issue, "location") and hasattr(issue.location, "filepath"):
            filepath = issue.location.filepath
        elif hasattr(issue, "filepath"):
            filepath = issue.filepath
        elif isinstance(issue, dict):
            filepath = issue.get("file", issue.get("filepath", ""))

        # Skip test files if requested
        if exclude_tests and is_test_file(filepath):
            continue

        # Get severity - handle different attribute structures
        severity = ""
        if hasattr(issue, "severity"):
            sev = issue.severity
            severity = sev.value if hasattr(sev, "value") else str(sev).lower()
        elif isinstance(issue, dict):
            severity = issue.get("severity", "").lower()

        # Count by severity
        if severity == "critical":
            critical += 1
        elif severity == "high":
            high += 1
        elif severity == "medium":
            medium += 1
        elif severity == "low":
            low += 1

    # Verdict: Only CRITICAL blocks production
    ready = critical == 0

    if ready:
        if high > 0:
            message = f"✅ READY FOR PRODUCTION ({high} warnings)"
        else:
            message = "✅ READY FOR PRODUCTION"
    else:
        message = f"⛔ NOT READY — Fix {critical} critical issues"

    return Verdict(
        ready=ready,
        message=message,
        critical_count=critical,
        high_count=high,
        medium_count=medium,
        low_count=low,
    )


def calculate_scan_summary(issues: List[Any]) -> ScanSummary:
    """
    Calculate complete scan summary with production and test issues separated.

    This is the PRIMARY function for all interfaces (CLI, TUI, MCP).
    Returns both production and test counts for full transparency.

    Logic:
    - Production issues: Files NOT in test directories
    - Test issues: Files in tests/, __tests__/, test_*.py, etc.
    - Verdict: Based ONLY on production critical count (0 = READY)

    Args:
        issues: List of Issue objects or dicts

    Returns:
        ScanSummary with production counts, test counts, and verdict
    """
    # Production counts
    prod_critical = 0
    prod_high = 0
    prod_medium = 0
    prod_low = 0

    # Test counts
    test_critical = 0
    test_high = 0
    test_medium = 0
    test_low = 0

    for issue in issues:
        # Get filepath - handle different attribute structures
        filepath = ""
        if hasattr(issue, "location") and hasattr(issue.location, "filepath"):
            filepath = issue.location.filepath
        elif hasattr(issue, "filepath"):
            filepath = issue.filepath
        elif isinstance(issue, dict):
            filepath = issue.get("file", issue.get("filepath", ""))

        # Get severity - handle different attribute structures
        severity = ""
        if hasattr(issue, "severity"):
            sev = issue.severity
            severity = sev.value if hasattr(sev, "value") else str(sev).lower()
        elif isinstance(issue, dict):
            severity = issue.get("severity", "").lower()

        # Route to production or test counts
        if is_test_file(filepath):
            if severity == "critical":
                test_critical += 1
            elif severity == "high":
                test_high += 1
            elif severity == "medium":
                test_medium += 1
            elif severity == "low":
                test_low += 1
        else:
            if severity == "critical":
                prod_critical += 1
            elif severity == "high":
                prod_high += 1
            elif severity == "medium":
                prod_medium += 1
            elif severity == "low":
                prod_low += 1

    # Verdict: Only production CRITICAL blocks
    ready = prod_critical == 0

    if ready:
        if prod_high > 0:
            message = f"✅ READY FOR PRODUCTION ({prod_high} warnings)"
        else:
            message = "✅ READY FOR PRODUCTION"
    else:
        message = f"⛔ NOT READY — Fix {prod_critical} critical issues"

    return ScanSummary(
        production=SeverityCounts(
            critical=prod_critical,
            high=prod_high,
            medium=prod_medium,
            low=prod_low,
        ),
        tests=SeverityCounts(
            critical=test_critical,
            high=test_high,
            medium=test_medium,
            low=test_low,
        ),
        ready=ready,
        message=message,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ISSUE SORTING
# ─────────────────────────────────────────────────────────────────────────────
def sort_issues_by_severity(issues: List[Any]) -> List[Any]:
    """
    Sort issues by severity (CRITICAL first, then HIGH, MEDIUM, LOW).

    This ensures consistent visual presentation across TUI/CLI/MCP.
    """
    def get_severity_rank(issue) -> int:
        if hasattr(issue, "severity"):
            sev = issue.severity
            severity = sev.value if hasattr(sev, "value") else str(sev).lower()
        elif isinstance(issue, dict):
            severity = issue.get("severity", "info").lower()
        else:
            severity = "info"
        return SEVERITY_ORDER.get(severity, 4)

    return sorted(issues, key=get_severity_rank)


def group_issues_by_file(issues: List[Any]) -> Dict[str, List[Any]]:
    """
    Group issues by file, with files sorted by most severe issue.

    Returns dict with filepath as key, issues as value.
    Files with critical issues appear first.
    """
    from collections import defaultdict

    by_file: Dict[str, List[Any]] = defaultdict(list)

    for issue in issues:
        # Get filepath
        if hasattr(issue, "location") and hasattr(issue.location, "filepath"):
            filepath = issue.location.filepath
        elif hasattr(issue, "filepath"):
            filepath = issue.filepath
        elif isinstance(issue, dict):
            filepath = issue.get("file", issue.get("filepath", "unknown"))
        else:
            filepath = "unknown"

        by_file[filepath].append(issue)

    # Sort issues within each file by severity
    for filepath in by_file:
        by_file[filepath] = sort_issues_by_severity(by_file[filepath])

    # Sort files by most severe issue
    def file_severity(filepath: str) -> int:
        file_issues = by_file[filepath]
        if not file_issues:
            return 999

        first_issue = file_issues[0]
        if hasattr(first_issue, "severity"):
            sev = first_issue.severity
            severity = sev.value if hasattr(sev, "value") else str(sev).lower()
        elif isinstance(first_issue, dict):
            severity = first_issue.get("severity", "info").lower()
        else:
            severity = "info"

        return SEVERITY_ORDER.get(severity, 4)

    # Return ordered dict
    sorted_files = sorted(by_file.keys(), key=file_severity)
    return {f: by_file[f] for f in sorted_files}


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTION COUNTS (excluding tests)
# ─────────────────────────────────────────────────────────────────────────────
def get_production_counts(issues: List[Any]) -> Dict[str, int]:
    """
    Get issue counts excluding test files.

    Returns dict with critical, high, medium, low counts.
    """
    verdict = calculate_verdict(issues, exclude_tests=True)
    return {
        "critical": verdict.critical_count,
        "high": verdict.high_count,
        "medium": verdict.medium_count,
        "low": verdict.low_count,
        "total": verdict.critical_count + verdict.high_count + verdict.medium_count + verdict.low_count,
    }

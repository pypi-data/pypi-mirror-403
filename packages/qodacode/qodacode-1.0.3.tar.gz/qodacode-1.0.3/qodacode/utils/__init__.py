"""
Qodacode utilities package.
"""

from .masking import mask_secrets, mask_snippet_for_issue, is_secret_issue
from .binaries import ensure_gitleaks, get_gitleaks_path, download_gitleaks
from .verdict import (
    is_test_file,
    calculate_verdict,
    sort_issues_by_severity,
    group_issues_by_file,
    get_production_counts,
    Verdict,
    QODACODE_ORANGE,
    SEVERITY_COLORS,
    SEVERITY_ICONS,
    SEVERITY_ORDER,
)

__all__ = [
    "mask_secrets",
    "mask_snippet_for_issue",
    "is_secret_issue",
    "ensure_gitleaks",
    "get_gitleaks_path",
    "download_gitleaks",
    # Verdict utilities
    "is_test_file",
    "calculate_verdict",
    "sort_issues_by_severity",
    "group_issues_by_file",
    "get_production_counts",
    "Verdict",
    "QODACODE_ORANGE",
    "SEVERITY_COLORS",
    "SEVERITY_ICONS",
    "SEVERITY_ORDER",
]

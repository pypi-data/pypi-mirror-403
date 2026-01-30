"""
Context management for Qodacode.

Handles deduplication, suppression, and semantic analysis of issues.
"""

from .deduplicator import Deduplicator, IssueFingerprint
from .semantic import (
    SemanticContext,
    SafePatternType,
    analyze_issue_context,
    is_likely_false_positive,
    filter_semantic_false_positives,
    is_safe_secret_context,
    is_safe_sql_context,
)

__all__ = [
    "Deduplicator",
    "IssueFingerprint",
    "SemanticContext",
    "SafePatternType",
    "analyze_issue_context",
    "is_likely_false_positive",
    "filter_semantic_false_positives",
    "is_safe_secret_context",
    "is_safe_sql_context",
]

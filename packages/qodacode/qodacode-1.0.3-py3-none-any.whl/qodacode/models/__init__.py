"""
Qodacode Data Models (Pydantic).

This module defines the unified data structures used across all engines.
All engine outputs MUST be normalized to these schemas before processing.
"""

from .issue import (
    Severity,
    Category,
    EngineSource,
    Location,
    Issue,
    ScanResult,
    ScanSummary,
    ScanMetadata,
)

__all__ = [
    "Severity",
    "Category",
    "EngineSource",
    "Location",
    "Issue",
    "ScanResult",
    "ScanSummary",
    "ScanMetadata",
]

"""
External analysis engines for Qodacode.

This module provides wrappers around external tools like Semgrep,
translating their output to Qodacode Issue objects.

All engines inherit from EngineRunner ABC to ensure consistent behavior.

NOTE: As of Phase 5, all engines return unified Pydantic Issue objects.
No conversion is needed - the dataclass Issue has been deprecated.
"""

from .base import EngineRunner, EngineError, EngineNotAvailableError
from .semgrep_runner import SemgrepRunner, check_semgrep_installed
from .gitleaks_runner import GitleaksRunner
from .osv_runner import OSVRunner


__all__ = [
    # Base classes
    "EngineRunner",
    "EngineError",
    "EngineNotAvailableError",
    # Runners
    "SemgrepRunner",
    "check_semgrep_installed",
    "GitleaksRunner",
    "OSVRunner",
]

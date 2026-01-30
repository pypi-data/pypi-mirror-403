"""
Qodacode - AI Governance Platform for Security + Alignment.

Combines code security scanning (Semgrep, Gitleaks) with AI alignment
auditing (Petri) for production-ready AI agent verification.
"""

__version__ = "1.0.3"
__author__ = "Nelson Padilla"

from qodacode.scanner import Scanner
from qodacode.rules.base import Rule, Issue, Severity, Category

__all__ = ["Scanner", "Rule", "Issue", "Severity", "Category", "__version__"]

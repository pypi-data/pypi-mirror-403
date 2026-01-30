"""
Qodacode Premium - Alignment Audit Engine (Petri Integration)

This module integrates Anthropic's Petri for automated alignment audits
of AI agents, providing unified Security + Alignment verdicts.
"""

from .auditor import AlignmentAuditor
from .verdict import UnifiedVerdict, create_unified_verdict
from .scenarios import (
    SELF_PRESERVATION_SCENARIO,
    DECEPTION_SCENARIO,
    WHISTLEBLOWING_SCENARIO,
    SITUATIONAL_AWARENESS_SCENARIO,
    get_scenario,
    list_scenarios,
)

__all__ = [
    "AlignmentAuditor",
    "UnifiedVerdict",
    "create_unified_verdict",
    "SELF_PRESERVATION_SCENARIO",
    "DECEPTION_SCENARIO",
    "WHISTLEBLOWING_SCENARIO",
    "SITUATIONAL_AWARENESS_SCENARIO",
    "get_scenario",
    "list_scenarios",
]

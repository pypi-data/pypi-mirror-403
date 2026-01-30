"""
Qodacode rules module.

Contains the base Rule class and all rule implementations organized by category:
- security: SEC-001 to SEC-007
- robustness: ROB-001 to ROB-005
- maintainability: MNT-001 to MNT-005
- operability: OPS-001 to OPS-005
- dependencies: DEP-001 to DEP-004
"""

from qodacode.rules.base import Rule, Issue, Severity, Category, RuleRegistry

# Import all rule modules to register them
from qodacode.rules import security
from qodacode.rules import robustness
from qodacode.rules import maintainability
from qodacode.rules import operability
from qodacode.rules import dependencies

__all__ = ["Rule", "Issue", "Severity", "Category", "RuleRegistry"]

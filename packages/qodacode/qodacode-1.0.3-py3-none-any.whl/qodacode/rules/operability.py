"""
Operability rules for Qodacode.

OPS-001: no-logging - Critical flows without logging
"""

import re
from typing import List

import tree_sitter

from qodacode.rules.base import Rule, Issue, Severity, Category


# Keywords that indicate critical operations needing logging
CRITICAL_OPERATIONS = [
    "payment",
    "checkout",
    "purchase",
    "transaction",
    "auth",
    "login",
    "signup",
    "register",
    "delete",
    "remove",
    "admin",
    "deploy",
    "migrate",
    "notify",
    "notification",
    "send",
    "email",
]

# HTTP request calls that should have logging
HTTP_CALL_PATTERNS = [
    r"requests\.(get|post|put|patch|delete|head|options)",
    r"httpx\.(get|post|put|patch|delete|head|options)",
    r"fetch\(",
    r"axios\.",
    r"urllib",
    r"aiohttp",
]

# Logging function patterns
LOGGING_PATTERNS = [
    r"logger\.",
    r"logging\.",
    r"log\.",
    r"console\.",
    r"print\(",  # Basic but counts
    r"sentry",
    r"datadog",
    r"newrelic",
]


class NoLoggingRule(Rule):
    """
    OPS-001: Detect critical operations without logging.

    Critical operations (payments, auth, admin actions) should have
    logging for debugging, auditing, and monitoring.
    """
    id = "OPS-001"
    name = "no-logging"
    description = "Detects critical flows without logging"
    severity = Severity.MEDIUM
    category = Category.OPERABILITY
    languages = ["python", "javascript", "typescript"]

    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        issues = []
        source_str = source.decode("utf-8", errors="replace")

        # Check if this file likely handles critical operations
        is_critical_file = any(
            op in filepath.lower() or op in source_str.lower()
            for op in CRITICAL_OPERATIONS
        )

        if not is_critical_file:
            return []

        # Check if file has any logging
        has_logging = any(
            re.search(pattern, source_str)
            for pattern in LOGGING_PATTERNS
        )

        if not has_logging:
            # Find functions in critical file without logging
            cursor = tree.walk()
            self._check_functions(cursor.node, source, filepath, issues)

        return issues

    def _check_functions(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Find functions that handle critical operations."""

        if node.type in ("function_definition", "function_declaration", "method_definition"):
            func_name = ""
            name_node = node.child_by_field_name("name")
            if name_node:
                func_name = self.get_node_text(name_node, source).lower()

            # Check if function name indicates critical operation
            is_critical_func = any(op in func_name for op in CRITICAL_OPERATIONS)

            if is_critical_func:
                # Check if function body has logging
                func_text = self.get_node_text(node, source)
                has_logging = any(
                    re.search(pattern, func_text)
                    for pattern in LOGGING_PATTERNS
                )

                if not has_logging:
                    issues.append(self.create_issue(
                        filepath=filepath,
                        node=node,
                        source=source,
                        message=f"Critical function '{func_name}' has no logging",
                        fix_suggestion="Add logging for auditing and debugging: logger.info(f'Processing {operation}...')",
                        context={"function": func_name},
                    ))

        for child in node.children:
            self._check_functions(child, source, filepath, issues)

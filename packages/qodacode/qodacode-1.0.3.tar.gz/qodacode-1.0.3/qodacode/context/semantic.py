"""
Semantic Context Analyzer for False Positive Reduction.

Analyzes code context to identify safe patterns that should NOT
be flagged as security issues.

Examples of safe patterns:
- decrypt_api_key() -> Decryption function, not a hardcoded secret
- hash_password() -> Hashing function, not exposing secrets
- os.environ.get("API_KEY") -> Reading from env, not hardcoded
- settings.SECRET_KEY -> Reference to settings, not the actual secret

This module reduces false positives by understanding code semantics.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set, Dict, Tuple

from qodacode.models.issue import Issue


class SafePatternType(Enum):
    """Types of safe patterns."""
    DECRYPT_FUNCTION = "decrypt_function"
    ENCRYPT_FUNCTION = "encrypt_function"
    HASH_FUNCTION = "hash_function"
    ENV_READ = "env_read"
    CONFIG_READ = "config_read"
    TEST_FIXTURE = "test_fixture"
    PLACEHOLDER = "placeholder"
    DOCUMENTATION = "documentation"


@dataclass
class SafePattern:
    """A pattern that indicates safe code."""
    pattern_type: SafePatternType
    regex: re.Pattern
    description: str
    applies_to_rules: Set[str]  # Empty = applies to all rules


# ─────────────────────────────────────────────────────────────────────────────
# SAFE PATTERNS DATABASE
# ─────────────────────────────────────────────────────────────────────────────

SAFE_PATTERNS: List[SafePattern] = [
    # Decryption functions - NOT leaking secrets
    SafePattern(
        pattern_type=SafePatternType.DECRYPT_FUNCTION,
        regex=re.compile(r'decrypt[_\w]*\s*\(', re.IGNORECASE),
        description="Decryption function call",
        applies_to_rules={"SEC-001", "SEC-002"},  # Secret detection rules
    ),
    SafePattern(
        pattern_type=SafePatternType.DECRYPT_FUNCTION,
        regex=re.compile(r'\.decrypt\s*\(', re.IGNORECASE),
        description="Decrypt method call",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),

    # Encryption functions - handling secrets safely
    SafePattern(
        pattern_type=SafePatternType.ENCRYPT_FUNCTION,
        regex=re.compile(r'encrypt[_\w]*\s*\(', re.IGNORECASE),
        description="Encryption function call",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.ENCRYPT_FUNCTION,
        regex=re.compile(r'\.encrypt\s*\(', re.IGNORECASE),
        description="Encrypt method call",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),

    # Hashing functions - NOT exposing secrets
    SafePattern(
        pattern_type=SafePatternType.HASH_FUNCTION,
        regex=re.compile(r'hash[_\w]*\s*\(', re.IGNORECASE),
        description="Hash function call",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.HASH_FUNCTION,
        regex=re.compile(r'\.hash\s*\(', re.IGNORECASE),
        description="Hash method call",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.HASH_FUNCTION,
        regex=re.compile(r'bcrypt|argon2|pbkdf2|scrypt', re.IGNORECASE),
        description="Known password hashing algorithm",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),

    # Environment variable reads - NOT hardcoded
    SafePattern(
        pattern_type=SafePatternType.ENV_READ,
        regex=re.compile(r'os\.environ\s*[\[\.]', re.IGNORECASE),
        description="Reading from os.environ",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.ENV_READ,
        regex=re.compile(r'os\.getenv\s*\(', re.IGNORECASE),
        description="Reading with os.getenv()",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.ENV_READ,
        regex=re.compile(r'getenv\s*\(', re.IGNORECASE),
        description="Reading with getenv()",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.ENV_READ,
        regex=re.compile(r'process\.env\.', re.IGNORECASE),
        description="Reading from process.env (Node.js)",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.ENV_READ,
        regex=re.compile(r'import\.meta\.env\.', re.IGNORECASE),
        description="Reading from import.meta.env (Vite)",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),

    # Config/settings reads - NOT the actual secret
    SafePattern(
        pattern_type=SafePatternType.CONFIG_READ,
        regex=re.compile(r'settings\.[A-Z_]+', re.IGNORECASE),
        description="Reading from settings object",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.CONFIG_READ,
        regex=re.compile(r'config\.[a-zA-Z_]+', re.IGNORECASE),
        description="Reading from config object",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.CONFIG_READ,
        regex=re.compile(r'Config\.[A-Z_]+', re.IGNORECASE),
        description="Reading from Config class",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),

    # Test fixtures - Safe in test context
    SafePattern(
        pattern_type=SafePatternType.TEST_FIXTURE,
        regex=re.compile(r'test_|_test\.py|tests/|spec/|__tests__/', re.IGNORECASE),
        description="Test file context",
        applies_to_rules={"SEC-001"},  # Allow test secrets
    ),
    SafePattern(
        pattern_type=SafePatternType.TEST_FIXTURE,
        regex=re.compile(r'mock_|fake_|stub_|dummy_', re.IGNORECASE),
        description="Mock/fake data",
        applies_to_rules={"SEC-001"},
    ),
    SafePattern(
        pattern_type=SafePatternType.TEST_FIXTURE,
        regex=re.compile(r'fixture|@pytest\.fixture', re.IGNORECASE),
        description="Test fixture",
        applies_to_rules={"SEC-001"},
    ),

    # Placeholder values - NOT real secrets
    SafePattern(
        pattern_type=SafePatternType.PLACEHOLDER,
        regex=re.compile(r'<[A-Z_]+>|YOUR_[A-Z_]+_HERE|\$\{[A-Z_]+\}', re.IGNORECASE),
        description="Placeholder value",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.PLACEHOLDER,
        regex=re.compile(r'xxx+|REPLACE_ME|INSERT_|CHANGE_ME', re.IGNORECASE),
        description="Obvious placeholder",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),
    SafePattern(
        pattern_type=SafePatternType.PLACEHOLDER,
        regex=re.compile(r'example\.com|localhost|127\.0\.0\.1', re.IGNORECASE),
        description="Example/localhost URL",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),

    # Documentation/comments
    SafePattern(
        pattern_type=SafePatternType.DOCUMENTATION,
        regex=re.compile(r'#\s*example:|#\s*e\.g\.|#\s*for example', re.IGNORECASE),
        description="Example in comment",
        applies_to_rules={"SEC-001"},
    ),

    # In-memory databases (safe for tests)
    SafePattern(
        pattern_type=SafePatternType.TEST_FIXTURE,
        regex=re.compile(r'sqlite.*:memory:|:memory:', re.IGNORECASE),
        description="In-memory SQLite database",
        applies_to_rules={"SEC-001", "SEC-002"},
    ),

    # Template literals (not actual values)
    SafePattern(
        pattern_type=SafePatternType.PLACEHOLDER,
        regex=re.compile(r'\{.*\}|\$\{.*\}|%\(.*\)s|%s', re.IGNORECASE),
        description="Template/format string",
        applies_to_rules={"SEC-001"},
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# SEMANTIC ANALYZER
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SemanticContext:
    """Result of semantic analysis for an issue."""
    is_safe: bool
    pattern_type: Optional[SafePatternType]
    reason: str
    confidence: float  # 0.0 to 1.0


def analyze_issue_context(issue: Issue) -> SemanticContext:
    """
    Analyze the semantic context of an issue.

    Checks if the code pattern indicates safe usage that should
    NOT be flagged as a security issue.

    Args:
        issue: The issue to analyze

    Returns:
        SemanticContext with analysis result
    """
    # Get code snippet and file path
    snippet = issue.snippet or ""
    filepath = issue.location.filepath
    rule_id = issue.rule_id.upper()

    # Also check the message (sometimes contains context)
    full_context = f"{snippet} {filepath} {issue.message}"

    # Check each safe pattern
    for pattern in SAFE_PATTERNS:
        # Check if pattern applies to this rule
        if pattern.applies_to_rules and rule_id not in pattern.applies_to_rules:
            continue

        # Check if pattern matches
        if pattern.regex.search(full_context):
            return SemanticContext(
                is_safe=True,
                pattern_type=pattern.pattern_type,
                reason=pattern.description,
                confidence=0.9,
            )

    # No safe pattern matched
    return SemanticContext(
        is_safe=False,
        pattern_type=None,
        reason="No safe pattern detected",
        confidence=0.0,
    )


def is_likely_false_positive(issue: Issue) -> Tuple[bool, str]:
    """
    Quick check if an issue is likely a false positive.

    Args:
        issue: The issue to check

    Returns:
        Tuple of (is_false_positive, reason)
    """
    context = analyze_issue_context(issue)
    return context.is_safe, context.reason


def filter_semantic_false_positives(
    issues: List[Issue],
    enabled: bool = True
) -> Tuple[List[Issue], int, List[Tuple[Issue, str]]]:
    """
    Filter out likely false positives based on semantic analysis.

    Args:
        issues: List of issues to filter
        enabled: Whether semantic filtering is enabled

    Returns:
        Tuple of (filtered_issues, removed_count, removed_with_reasons)
    """
    if not enabled:
        return issues, 0, []

    filtered = []
    removed = []

    for issue in issues:
        is_fp, reason = is_likely_false_positive(issue)

        if is_fp:
            removed.append((issue, reason))
        else:
            filtered.append(issue)

    return filtered, len(removed), removed


# ─────────────────────────────────────────────────────────────────────────────
# RULE-SPECIFIC CONTEXT CHECKS
# ─────────────────────────────────────────────────────────────────────────────

def is_safe_secret_context(snippet: str, filepath: str) -> Tuple[bool, str]:
    """
    Check if a potential secret is in a safe context.

    Specifically for SEC-001 (hardcoded secrets) rule.

    Args:
        snippet: Code snippet containing the potential secret
        filepath: File path

    Returns:
        Tuple of (is_safe, reason)
    """
    combined = f"{snippet} {filepath}"

    # Environment variable reads
    if re.search(r'os\.environ|os\.getenv|getenv\(|process\.env', combined, re.IGNORECASE):
        return True, "Reading from environment variable"

    # Decrypt/encrypt operations
    if re.search(r'decrypt|encrypt|\.decrypt\(|\.encrypt\(', combined, re.IGNORECASE):
        return True, "Encryption/decryption operation"

    # Hash operations
    if re.search(r'hash|bcrypt|argon2|pbkdf2', combined, re.IGNORECASE):
        return True, "Hashing operation"

    # Test files
    if re.search(r'test_|_test\.py|/tests/|/test/|conftest\.py', filepath, re.IGNORECASE):
        return True, "Test file context"

    # Config/settings reference
    if re.search(r'settings\.|config\.|Config\.', combined, re.IGNORECASE):
        return True, "Config/settings reference"

    # Placeholder values
    if re.search(r'<[A-Z_]+>|YOUR_|REPLACE_|xxx+|example\.com', combined, re.IGNORECASE):
        return True, "Placeholder value"

    # In-memory database
    if re.search(r':memory:|sqlite.*memory', combined, re.IGNORECASE):
        return True, "In-memory database (test)"

    return False, ""


def is_safe_sql_context(snippet: str, filepath: str) -> Tuple[bool, str]:
    """
    Check if a potential SQL injection is in a safe context.

    Specifically for SQL injection rules.

    Args:
        snippet: Code snippet
        filepath: File path

    Returns:
        Tuple of (is_safe, reason)
    """
    combined = f"{snippet} {filepath}"

    # Parameterized queries
    if re.search(r'\?\s*,|\%s|:\w+|\$\d+', combined):
        return True, "Parameterized query"

    # ORM usage
    if re.search(r'\.filter\(|\.where\(|\.select\(|\.query\(', combined, re.IGNORECASE):
        return True, "ORM method (likely safe)"

    # Test context
    if re.search(r'test_|_test\.py|/tests/', filepath, re.IGNORECASE):
        return True, "Test file context"

    return False, ""

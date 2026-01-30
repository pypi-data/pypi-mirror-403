"""
Secret masking utilities for Qodacode.

Defense-in-depth: Even if secrets slip through engine processing,
the output layer must NEVER display real secrets.

This module provides pattern-based redaction for common secret formats.
"""

import re
from typing import Optional

# Common secret patterns that should be masked in output
# Each tuple: (name, regex_pattern, keep_prefix_length)
SECRET_PATTERNS = [
    # API Keys with known prefixes (include underscores, flexible length)
    ("stripe_live", r"sk_live_[a-zA-Z0-9_]{8,}", 8),
    ("stripe_test", r"sk_test_[a-zA-Z0-9_]{8,}", 8),
    ("stripe_pk", r"pk_live_[a-zA-Z0-9_]{8,}", 8),
    ("openai", r"sk-[a-zA-Z0-9_]{20,}", 3),
    ("anthropic", r"sk-ant-[a-zA-Z0-9_-]{20,}", 7),
    ("github_token", r"ghp_[a-zA-Z0-9_]{20,}", 4),
    ("github_oauth", r"gho_[a-zA-Z0-9_]{20,}", 4),
    ("github_app", r"ghu_[a-zA-Z0-9_]{20,}", 4),
    ("github_refresh", r"ghr_[a-zA-Z0-9_]{20,}", 4),
    ("aws_access", r"AKIA[0-9A-Z]{16}", 4),
    ("aws_secret", r"[a-zA-Z0-9/+=]{40}", 4),
    ("slack_token", r"xox[baprs]-[0-9]{10,13}-[a-zA-Z0-9_-]{20,}", 4),
    ("slack_webhook", r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8,}/B[a-zA-Z0-9_]{8,}/[a-zA-Z0-9_]{24}", 30),
    ("google_api", r"AIza[0-9A-Za-z_-]{35}", 4),
    ("firebase", r"[a-zA-Z0-9_-]*:[a-zA-Z0-9_-]{100,}", 10),
    ("twilio_sid", r"AC[a-zA-Z0-9]{32}", 2),
    ("twilio_token", r"SK[a-zA-Z0-9]{32}", 2),
    ("sendgrid", r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}", 3),
    ("npm_token", r"npm_[a-zA-Z0-9_]{20,}", 4),
    ("pypi_token", r"pypi-[a-zA-Z0-9_-]{20,}", 5),

    # Generic patterns (catch-all, less specific)
    ("private_key", r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", 30),
    ("jwt_token", r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*", 10),
    ("bearer_token", r"Bearer [a-zA-Z0-9_-]{20,}", 7),
    ("basic_auth", r"Basic [a-zA-Z0-9+/=]{20,}", 6),

    # Database URLs with passwords
    ("postgres_url", r"postgres(ql)?://[^:]+:([^@]+)@", 15),
    ("mysql_url", r"mysql://[^:]+:([^@]+)@", 10),
    ("mongodb_url", r"mongodb(\+srv)?://[^:]+:([^@]+)@", 15),
    ("redis_url", r"redis://:[^@]+@", 8),
]


def mask_secrets(text: str, mask_char: str = "*") -> str:
    """
    Mask any detected secrets in the given text.

    Args:
        text: The text that may contain secrets
        mask_char: Character to use for masking (default: *)

    Returns:
        Text with secrets masked, preserving a recognizable prefix

    Example:
        >>> mask_secrets("api_key = 'sk_live_" + "abc123def456'")
        "api_key = 'sk_live_***'"
    """
    if not text:
        return text

    result = text

    for name, pattern, keep_prefix in SECRET_PATTERNS:
        try:
            matches = re.finditer(pattern, result)
            for match in matches:
                secret = match.group(0)
                # Create masked version
                if len(secret) > keep_prefix:
                    masked = secret[:keep_prefix] + mask_char * 3
                else:
                    masked = mask_char * 3
                result = result.replace(secret, masked)
        except re.error:
            # Skip invalid patterns
            continue

    return result


def mask_snippet_for_issue(snippet: str, rule_id: str, engine: str) -> str:
    """
    Mask a code snippet based on the issue type.

    For SECRET-related issues (Gitleaks, SEC-001), always mask.
    For other issues, return the snippet unchanged.

    Args:
        snippet: Code snippet from the issue
        rule_id: The rule ID (e.g., "SEC-001", "GL-aws-access-key")
        engine: Source engine name (e.g., "gitleaks", "tree-sitter")

    Returns:
        Masked snippet if it's a secret issue, original otherwise
    """
    if not snippet:
        return snippet

    # Always mask for Gitleaks findings
    if engine.lower() == "gitleaks":
        return mask_secrets(snippet)

    # Always mask for secret-related rules
    secret_rule_patterns = [
        "SEC-001",  # Our hardcoded secret rule
        "GL-",      # All Gitleaks rules
        "secret",   # Any rule with "secret" in the name
        "api-key",
        "password",
        "credential",
        "token",
    ]

    rule_lower = rule_id.lower()
    if any(pattern.lower() in rule_lower for pattern in secret_rule_patterns):
        return mask_secrets(snippet)

    # For non-secret issues, still run through masking
    # as defense-in-depth (the code might contain secrets
    # even if the issue is about something else)
    return mask_secrets(snippet)


def is_secret_issue(rule_id: str, engine: str) -> bool:
    """
    Determine if an issue is related to secrets.

    Args:
        rule_id: The rule ID
        engine: Source engine name

    Returns:
        True if this is a secret-related issue
    """
    if engine.lower() == "gitleaks":
        return True

    secret_indicators = [
        "SEC-001",
        "secret",
        "api-key",
        "password",
        "credential",
        "token",
        "private-key",
    ]

    rule_lower = rule_id.lower()
    return any(ind.lower() in rule_lower for ind in secret_indicators)

"""
Comprehensive secret detection patterns.

Based on Gitleaks patterns (https://github.com/gitleaks/gitleaks)
with additional patterns for modern services.

Patterns are organized by service/type for easy maintenance.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Pattern, Optional, Tuple


@dataclass
class SecretPattern:
    """Defines a secret pattern with metadata."""
    id: str
    name: str
    pattern: Pattern
    entropy_threshold: float = 3.5  # Shannon entropy threshold
    keywords: List[str] = None  # Keywords that must be near the match

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


# =============================================================================
# CLOUD PROVIDERS
# =============================================================================

AWS_PATTERNS = [
    SecretPattern(
        id="aws-access-key-id",
        name="AWS Access Key ID",
        pattern=re.compile(r"(?:A3T[A-Z0-9]|AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}"),
    ),
    SecretPattern(
        id="aws-secret-access-key",
        name="AWS Secret Access Key",
        pattern=re.compile(r"(?i)(?:aws)?_?(?:secret)?_?(?:access)?_?key['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"),
    ),
    SecretPattern(
        id="aws-mws-key",
        name="AWS MWS Key",
        pattern=re.compile(r"amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),
    ),
]

GCP_PATTERNS = [
    SecretPattern(
        id="gcp-api-key",
        name="GCP API Key",
        pattern=re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    ),
    SecretPattern(
        id="gcp-service-account",
        name="GCP Service Account",
        pattern=re.compile(r"\"type\":\s*\"service_account\""),
        keywords=["private_key", "client_email"],
    ),
]

AZURE_PATTERNS = [
    SecretPattern(
        id="azure-storage-key",
        name="Azure Storage Account Key",
        pattern=re.compile(r"(?i)(?:storage|account)_?key['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9+/=]{88})['\"]?"),
    ),
    SecretPattern(
        id="azure-connection-string",
        name="Azure Connection String",
        pattern=re.compile(r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{88}"),
    ),
]

# =============================================================================
# PAYMENT PROVIDERS
# =============================================================================

STRIPE_PATTERNS = [
    SecretPattern(
        id="stripe-secret-key",
        name="Stripe Secret Key",
        pattern=re.compile(r"sk_live_[0-9a-zA-Z]{24,}"),
    ),
    SecretPattern(
        id="stripe-publishable-key",
        name="Stripe Publishable Key",
        pattern=re.compile(r"pk_live_[0-9a-zA-Z]{24,}"),
    ),
    SecretPattern(
        id="stripe-restricted-key",
        name="Stripe Restricted Key",
        pattern=re.compile(r"rk_live_[0-9a-zA-Z]{24,}"),
    ),
]

PAYPAL_PATTERNS = [
    SecretPattern(
        id="paypal-braintree-access-token",
        name="PayPal Braintree Access Token",
        pattern=re.compile(r"access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}"),
    ),
]

SQUARE_PATTERNS = [
    SecretPattern(
        id="square-access-token",
        name="Square Access Token",
        pattern=re.compile(r"sq0atp-[0-9A-Za-z\-_]{22}"),
    ),
    SecretPattern(
        id="square-oauth-secret",
        name="Square OAuth Secret",
        pattern=re.compile(r"sq0csp-[0-9A-Za-z\-_]{43}"),
    ),
]

# =============================================================================
# AUTH PROVIDERS
# =============================================================================

GITHUB_PATTERNS = [
    SecretPattern(
        id="github-pat",
        name="GitHub Personal Access Token",
        pattern=re.compile(r"ghp_[0-9a-zA-Z]{36}"),
    ),
    SecretPattern(
        id="github-oauth",
        name="GitHub OAuth Access Token",
        pattern=re.compile(r"gho_[0-9a-zA-Z]{36}"),
    ),
    SecretPattern(
        id="github-app-token",
        name="GitHub App Token",
        pattern=re.compile(r"(?:ghu|ghs)_[0-9a-zA-Z]{36}"),
    ),
    SecretPattern(
        id="github-refresh-token",
        name="GitHub Refresh Token",
        pattern=re.compile(r"ghr_[0-9a-zA-Z]{36}"),
    ),
]

GITLAB_PATTERNS = [
    SecretPattern(
        id="gitlab-pat",
        name="GitLab Personal Access Token",
        pattern=re.compile(r"glpat-[0-9a-zA-Z\-_]{20}"),
    ),
    SecretPattern(
        id="gitlab-pipeline-token",
        name="GitLab Pipeline Token",
        pattern=re.compile(r"glptt-[0-9a-zA-Z\-_]{20}"),
    ),
]

# =============================================================================
# DATABASE CONNECTIONS
# =============================================================================

DATABASE_PATTERNS = [
    SecretPattern(
        id="postgres-uri",
        name="PostgreSQL Connection URI",
        pattern=re.compile(r"postgres(?:ql)?://[^:]+:[^@]+@[^/]+/\w+"),
    ),
    SecretPattern(
        id="mysql-uri",
        name="MySQL Connection URI",
        pattern=re.compile(r"mysql://[^:]+:[^@]+@[^/]+/\w+"),
    ),
    SecretPattern(
        id="mongodb-uri",
        name="MongoDB Connection URI",
        pattern=re.compile(r"mongodb(?:\+srv)?://[^:]+:[^@]+@[^/]+"),
    ),
    SecretPattern(
        id="redis-uri",
        name="Redis Connection URI",
        pattern=re.compile(r"redis://[^:]+:[^@]+@[^:]+:\d+"),
    ),
]

# =============================================================================
# MESSAGING & COMMUNICATION
# =============================================================================

SLACK_PATTERNS = [
    SecretPattern(
        id="slack-token",
        name="Slack Token",
        pattern=re.compile(r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*"),
    ),
    SecretPattern(
        id="slack-webhook",
        name="Slack Webhook",
        pattern=re.compile(r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+"),
    ),
]

DISCORD_PATTERNS = [
    SecretPattern(
        id="discord-token",
        name="Discord Bot Token",
        pattern=re.compile(r"[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27}"),
    ),
    SecretPattern(
        id="discord-webhook",
        name="Discord Webhook",
        pattern=re.compile(r"https://discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+"),
    ),
]

TWILIO_PATTERNS = [
    SecretPattern(
        id="twilio-api-key",
        name="Twilio API Key",
        pattern=re.compile(r"SK[0-9a-fA-F]{32}"),
    ),
    SecretPattern(
        id="twilio-account-sid",
        name="Twilio Account SID",
        pattern=re.compile(r"AC[a-zA-Z0-9]{32}"),
    ),
]

SENDGRID_PATTERNS = [
    SecretPattern(
        id="sendgrid-api-key",
        name="SendGrid API Key",
        pattern=re.compile(r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}"),
    ),
]

# =============================================================================
# GENERAL PATTERNS
# =============================================================================

GENERAL_PATTERNS = [
    SecretPattern(
        id="private-key",
        name="Private Key",
        pattern=re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    ),
    SecretPattern(
        id="jwt-token",
        name="JWT Token",
        pattern=re.compile(r"eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+"),
    ),
    SecretPattern(
        id="basic-auth",
        name="Basic Auth Credentials",
        pattern=re.compile(r"(?i)(?:basic)\s+[A-Za-z0-9+/=]{20,}"),
    ),
    SecretPattern(
        id="bearer-token",
        name="Bearer Token",
        pattern=re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"),
    ),
]

# =============================================================================
# GENERIC API KEY PATTERNS
# =============================================================================

GENERIC_API_PATTERNS = [
    SecretPattern(
        id="generic-api-key",
        name="Generic API Key",
        pattern=re.compile(r"(?i)(?:api[_-]?key|apikey|api[_-]?secret)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?"),
        entropy_threshold=4.0,
    ),
    SecretPattern(
        id="generic-secret",
        name="Generic Secret",
        pattern=re.compile(r"(?i)(?:secret|password|passwd|pwd|token|credential)['\"]?\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?"),
        entropy_threshold=4.0,
    ),
    SecretPattern(
        id="high-entropy-string",
        name="High Entropy String",
        pattern=re.compile(r"['\"]([A-Za-z0-9+/=_\-]{32,})['\"]"),
        entropy_threshold=4.5,
    ),
]

# =============================================================================
# ALL PATTERNS COMBINED
# =============================================================================

ALL_SECRET_PATTERNS: List[SecretPattern] = (
    AWS_PATTERNS +
    GCP_PATTERNS +
    AZURE_PATTERNS +
    STRIPE_PATTERNS +
    PAYPAL_PATTERNS +
    SQUARE_PATTERNS +
    GITHUB_PATTERNS +
    GITLAB_PATTERNS +
    DATABASE_PATTERNS +
    SLACK_PATTERNS +
    DISCORD_PATTERNS +
    TWILIO_PATTERNS +
    SENDGRID_PATTERNS +
    GENERAL_PATTERNS +
    GENERIC_API_PATTERNS
)


def calculate_entropy(data: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not data:
        return 0.0

    import math
    from collections import Counter

    counts = Counter(data)
    length = len(data)
    entropy = 0.0

    for count in counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)

    return entropy


def is_likely_secret(match: str, pattern: SecretPattern) -> bool:
    """
    Determine if a match is likely a real secret vs false positive.

    Checks entropy and common false positive patterns.
    """
    # Skip very short matches
    if len(match) < 8:
        return False

    # Check entropy for patterns that require it
    if pattern.entropy_threshold > 0:
        entropy = calculate_entropy(match)
        if entropy < pattern.entropy_threshold:
            return False

    # Common false positives
    false_positives = [
        "example",
        "sample",
        "test",
        "dummy",
        "placeholder",
        "your_",
        "my_",
        "xxx",
        "yyy",
        "zzz",
        "12345",
        "abcde",
        "foobar",
        "changeme",
        "password123",
        "REPLACE_ME",
        "INSERT_",
        "<YOUR_",
        "${",
        "{{",
        "process.env",
        "os.environ",
        "getenv",
    ]

    match_lower = match.lower()
    for fp in false_positives:
        if fp.lower() in match_lower:
            return False

    return True


def scan_for_secrets(content: str) -> List[Dict]:
    """
    Scan content for secrets using all patterns.

    Returns list of findings with:
    - pattern_id: ID of matched pattern
    - pattern_name: Human-readable name
    - match: The matched string
    - line: Line number (1-indexed)
    - column: Column number (0-indexed)
    """
    findings = []
    lines = content.split("\n")

    for pattern in ALL_SECRET_PATTERNS:
        for line_num, line in enumerate(lines, 1):
            for match in pattern.pattern.finditer(line):
                matched_text = match.group(0)

                # For patterns with capture groups, use the group
                if match.lastindex:
                    matched_text = match.group(1)

                # Verify it's likely a real secret
                if not is_likely_secret(matched_text, pattern):
                    continue

                findings.append({
                    "pattern_id": pattern.id,
                    "pattern_name": pattern.name,
                    "match": matched_text[:50] + "..." if len(matched_text) > 50 else matched_text,
                    "line": line_num,
                    "column": match.start(),
                    "full_match": matched_text,
                })

    return findings


# Files/paths to skip
SKIP_PATHS = [
    ".git/",
    "node_modules/",
    "__pycache__/",
    ".venv/",
    "venv/",
    ".env.example",
    ".env.sample",
    "test_",
    "_test.py",
    ".test.",
    "mock",
    "fixture",
]


def should_skip_file(filepath: str) -> bool:
    """Check if file should be skipped for secret scanning."""
    filepath_lower = filepath.lower()
    return any(skip in filepath_lower for skip in SKIP_PATHS)

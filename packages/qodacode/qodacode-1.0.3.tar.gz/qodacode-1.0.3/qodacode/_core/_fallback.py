"""
Pure Python fallback implementations for qodacode_core.

These implementations are used when the Rust module is not available.
They provide the same API but with lower performance.

Note: This file is intentionally readable as it serves as documentation
for the algorithm specifications. The Rust implementation is compiled
and provides the actual production performance.
"""

import hashlib
import re
import unicodedata
from typing import List, Optional, Tuple

# ============================================================================
# Homoglyph mappings (subset - full mapping in Rust)
# ============================================================================

HOMOGLYPHS: dict[str, list[str]] = {
    'a': ['а', 'ɑ', 'α'],  # Cyrillic а, Latin ɑ, Greek α
    'c': ['с', 'ϲ'],       # Cyrillic с
    'e': ['е', 'ё', 'ε'],  # Cyrillic е, Greek ε
    'o': ['о', 'ο', '0'],  # Cyrillic о, Greek ο, digit 0
    'p': ['р', 'ρ'],       # Cyrillic р, Greek ρ
    'i': ['і', 'ι', '1', 'l'],  # Cyrillic і, Greek ι
    'l': ['1', 'I', '|'],
    's': ['ѕ'],            # Cyrillic ѕ
    'x': ['х'],            # Cyrillic х
    'y': ['у'],            # Cyrillic у
}

# Reverse mapping
HOMOGLYPHS_REVERSE: dict[str, str] = {}
for original, lookalikes in HOMOGLYPHS.items():
    for lookalike in lookalikes:
        HOMOGLYPHS_REVERSE[lookalike] = original

# ============================================================================
# QWERTY keyboard adjacency
# ============================================================================

QWERTY_ADJACENT: dict[str, list[str]] = {
    'q': ['w', 'a', '1', '2'],
    'w': ['q', 'e', 'a', 's', '2', '3'],
    'e': ['w', 'r', 's', 'd', '3', '4'],
    'r': ['e', 't', 'd', 'f', '4', '5'],
    't': ['r', 'y', 'f', 'g', '5', '6'],
    'y': ['t', 'u', 'g', 'h', '6', '7'],
    'u': ['y', 'i', 'h', 'j', '7', '8'],
    'i': ['u', 'o', 'j', 'k', '8', '9'],
    'o': ['i', 'p', 'k', 'l', '9', '0'],
    'p': ['o', 'l', '0', '-'],
    'a': ['q', 'w', 's', 'z'],
    's': ['a', 'w', 'e', 'd', 'z', 'x'],
    'd': ['s', 'e', 'r', 'f', 'x', 'c'],
    'f': ['d', 'r', 't', 'g', 'c', 'v'],
    'g': ['f', 't', 'y', 'h', 'v', 'b'],
    'h': ['g', 'y', 'u', 'j', 'b', 'n'],
    'j': ['h', 'u', 'i', 'k', 'n', 'm'],
    'k': ['j', 'i', 'o', 'l', 'm'],
    'l': ['k', 'o', 'p'],
    'z': ['a', 's', 'x'],
    'x': ['z', 's', 'd', 'c'],
    'c': ['x', 'd', 'f', 'v'],
    'v': ['c', 'f', 'g', 'b'],
    'b': ['v', 'g', 'h', 'n'],
    'n': ['b', 'h', 'j', 'm'],
    'm': ['n', 'j', 'k'],
}

# ============================================================================
# Safe patterns for false positive reduction
# ============================================================================

SAFE_PATTERNS: list[tuple[str, str]] = [
    # Environment variable reads
    (r"os\.environ", "Environment variable read"),
    (r"os\.getenv", "Environment variable read"),
    (r"process\.env\.", "Node.js environment read"),
    (r"import\.meta\.env\.", "Vite environment read"),
    (r"dotenv\.get", "Dotenv read"),

    # Cryptographic operations
    (r"decrypt", "Decryption operation"),
    (r"encrypt", "Encryption operation"),
    (r"hash", "Hash operation"),
    (r"bcrypt\.", "Bcrypt operation"),

    # Configuration reads
    (r"settings\.", "Settings object access"),
    (r"config\.", "Config object access"),

    # Test/mock data
    (r"mock_", "Mock data prefix"),
    (r"test_", "Test data prefix"),
    (r"fake_", "Fake data prefix"),

    # Placeholders
    (r"<YOUR_", "Placeholder"),
    (r"YOUR_.*_HERE", "Placeholder"),
    (r"xxx", "Placeholder"),
    (r"changeme", "Placeholder"),

    # Test database URLs
    (r"sqlite:///:memory:", "In-memory SQLite"),
    (r"localhost", "Localhost reference"),
    (r"example\.com", "Example domain"),
]

TEST_PATH_PATTERN = re.compile(
    r"(?i)(test[s_]?|spec[s_]?|__test__|__spec__|fixtures?|mocks?)"
)

# ============================================================================
# Fingerprint computation
# ============================================================================

FINGERPRINT_SALT = b"qodacode_fp_v1_2025"


def normalize_code(snippet: str) -> str:
    """
    Normalize code snippet for stable fingerprinting.

    Removes noise that doesn't affect semantics:
    - Whitespace normalization
    - Unicode normalization (NFKC)
    - Case normalization
    """
    # Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", snippet)

    # Normalize whitespace
    normalized = " ".join(normalized.split())

    # Lowercase
    normalized = normalized.lower()

    return normalized.strip()


def compute_fingerprint(filepath: str, rule_id: str, snippet: str) -> str:
    """
    Compute a stable fingerprint for an issue.

    Args:
        filepath: Relative path to the file
        rule_id: The rule that detected this issue
        snippet: The code snippet containing the issue

    Returns:
        A 12-character hex string that uniquely identifies this issue
    """
    # Normalize inputs
    normalized_snippet = normalize_code(snippet)
    normalized_path = filepath.replace("\\", "/").lower()
    normalized_rule = rule_id.upper()

    # Create input for hashing
    input_str = f"{normalized_path}:{normalized_rule}:{normalized_snippet}"

    # Use SHA-256 with salt (simpler than BLAKE3 for Python)
    hasher = hashlib.sha256()
    hasher.update(FINGERPRINT_SALT)
    hasher.update(input_str.encode("utf-8"))

    # Return first 6 bytes as 12-char hex string
    return hasher.hexdigest()[:12]


# ============================================================================
# Levenshtein distance
# ============================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute Levenshtein (edit) distance between two strings.

    Uses dynamic programming with O(min(m,n)) space.
    """
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))

    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost is 0 if characters match, 1 otherwise
            cost = 0 if c1 == c2 else 1
            curr_row.append(min(
                prev_row[j + 1] + 1,      # Deletion
                curr_row[j] + 1,          # Insertion
                prev_row[j] + cost        # Substitution
            ))
        prev_row = curr_row

    return prev_row[-1]


# ============================================================================
# Homoglyph detection
# ============================================================================

def normalize_homoglyphs(s: str) -> str:
    """Replace homoglyph characters with their ASCII equivalents."""
    return "".join(HOMOGLYPHS_REVERSE.get(c, c) for c in s)


def is_homoglyph_attack(suspicious: str, legitimate: str) -> bool:
    """Check if suspicious string is a homoglyph variant of legitimate."""
    if suspicious == legitimate:
        return False

    normalized_suspicious = normalize_homoglyphs(suspicious)
    normalized_legitimate = normalize_homoglyphs(legitimate)

    return (
        normalized_suspicious == normalized_legitimate or
        levenshtein_distance(normalized_suspicious, normalized_legitimate) <= 1
    )


# ============================================================================
# Keyboard proximity
# ============================================================================

def are_adjacent(c1: str, c2: str) -> bool:
    """Check if two characters are adjacent on QWERTY keyboard."""
    c1_lower = c1.lower()
    c2_lower = c2.lower()
    return c2_lower in QWERTY_ADJACENT.get(c1_lower, [])


def keyboard_distance(s1: str, s2: str) -> int:
    """
    Compute keyboard distance between two strings.

    Returns the number of character pairs that differ by keyboard adjacency.
    """
    if len(s1) != len(s2):
        return 999999  # Very large number for different lengths

    return sum(
        1 for c1, c2 in zip(s1, s2)
        if c1 != c2 and are_adjacent(c1, c2)
    )


# ============================================================================
# Combined similarity score
# ============================================================================

def compute_similarity_score(suspicious: str, legitimate: str) -> float:
    """
    Compute comprehensive similarity score between package names.

    Returns a score from 0.0 to 1.0 where:
    - 1.0 = definitely a typosquatting attempt
    - 0.0 = no similarity
    """
    # Exact match = not suspicious
    if suspicious == legitimate:
        return 0.0

    s1 = suspicious.lower()
    s2 = legitimate.lower()

    # Homoglyph attack = very high score
    if is_homoglyph_attack(s1, s2):
        return 0.95

    # Edit distance
    edit_dist = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))

    # Too different = not suspicious
    if edit_dist > 3 or (edit_dist / max_len) > 0.4:
        return 0.0

    # Base score from edit distance
    edit_score = 1.0 - (edit_dist / max_len)

    # Keyboard proximity bonus
    kbd_dist = keyboard_distance(s1, s2)
    kbd_bonus = 0.15 * (kbd_dist / 2.0) if 0 < kbd_dist <= 2 else 0.0

    # Length similarity bonus
    len_ratio = min(len(s1), len(s2)) / max(len(s1), len(s2))
    len_bonus = 0.1 if len_ratio > 0.8 else 0.0

    # Combine scores
    final_score = min((edit_score * 0.7 + kbd_bonus + len_bonus), 1.0)

    return final_score if final_score >= 0.5 else 0.0


# ============================================================================
# Pattern matching
# ============================================================================

def is_safe_pattern(snippet: str, filepath: str) -> Tuple[bool, str, str]:
    """
    Check if a code snippet matches any safe pattern.

    Args:
        snippet: The code snippet to check
        filepath: Path to the file

    Returns:
        Tuple of (is_safe, pattern, reason)
    """
    # Check if file is a test file
    if TEST_PATH_PATTERN.search(filepath):
        return (True, "test_file", "Test file - likely test fixture")

    # Check against safe patterns
    snippet_lower = snippet.lower()
    for pattern, reason in SAFE_PATTERNS:
        if re.search(pattern, snippet_lower, re.IGNORECASE):
            return (True, pattern, reason)

    return (False, "", "")


def match_patterns(snippet: str) -> List[Tuple[str, str, int]]:
    """
    Match all safe patterns in a snippet.

    Returns:
        List of (pattern, reason, position) tuples
    """
    matches = []
    snippet_lower = snippet.lower()

    for pattern, reason in SAFE_PATTERNS:
        for match in re.finditer(pattern, snippet_lower, re.IGNORECASE):
            matches.append((pattern, reason, match.start()))

    return matches


# ============================================================================
# Embedded security data (Data Moats - Python fallback)
# ============================================================================

# Known malicious packages: suspicious_name -> legitimate_name
KNOWN_MALICIOUS: dict[str, str] = {
    # Python (PyPI) - Confirmed Attacks
    "reqeusts": "requests",
    "requets": "requests",
    "request": "requests",
    "reequests": "requests",
    "requsts": "requests",
    "djang": "django",
    "djagno": "django",
    "dajngo": "django",
    "flaask": "flask",
    "falsk": "flask",
    "numpyy": "numpy",
    "nunpy": "numpy",
    "panadas": "pandas",
    "pandsa": "pandas",
    "colourama": "colorama",
    "coloramma": "colorama",
    "boto": "boto3",
    "botto3": "boto3",
    "urllib": "urllib3",
    "urllib33": "urllib3",
    "setup-tools": "setuptools",
    "cyptography": "cryptography",
    "crytography": "cryptography",
    "pilllow": "pillow",
    "pilow": "pillow",
    "pyaml": "pyyaml",
    "tenserflow": "tensorflow",
    "pytoch": "pytorch",

    # AI/ML Separator Confusion (2024-2025)
    "huggingface-hub": "huggingface_hub",
    "hugging-face-hub": "huggingface_hub",
    "huggingfacehub": "huggingface_hub",
    "lang-chain": "langchain",
    "lang_chain": "langchain",
    "langchainn": "langchain",
    "openai-python": "openai",
    "open-ai": "openai",
    "openaai": "openai",
    "chatgpt": "openai",
    "opencv": "opencv-python",
    "cv2": "opencv-python",
    "py-torch": "torch",
    "pytorch-gpu": "torch",
    "stream-lit": "streamlit",
    "py-spark": "pyspark",
    "llama-index": "llamaindex",
    "llama_index": "llamaindex",
    "chroma-db": "chromadb",
    "pinecone": "pinecone-client",
    "tranformers": "transformers",
    "huggingface-transformers": "transformers",

    # JavaScript (NPM) - Confirmed Attacks
    "loadash": "lodash",
    "lodashs": "lodash",
    "lodsh": "lodash",
    "expres": "express",
    "expresss": "express",
    "axois": "axios",
    "axioss": "axios",
    "reactt": "react",
    "reacct": "react",
    "chalkk": "chalk",
    "event-steram": "event-stream",
    "crossenv": "cross-env",
    "babelcli": "babel-cli",
    "jquerry": "jquery",
    "electorn": "electron",
    "mongose": "mongoose",
    "wepback": "webpack",
    "comander": "commander",
    "momment": "moment",

    # NPM Modern Frontend (2024-2025)
    "nextjs": "next",
    "next-js": "next",
    "tailwind": "tailwindcss",
    "typescrip": "typescript",
    "vuejs": "vue",
    "node-sass": "sass",

    # NPM Scoped Package Attacks (Dec 2024)
    "@typescript_eslinter/eslint": "@typescript-eslint/eslint-plugin",
    "@typescript_eslinter/prettier": "prettier",
    "types-node": "@types/node",
    "types-react": "@types/react",

    # Cargo (Rust) Typosquats (Sep 2025)
    "faster_log": "fast_log",
    "async_println": "fast_log",
    "serdee": "serde",
    "tokioo": "tokio",
    "reqwests": "reqwest",

    # Go Modules Typosquats (Feb 2025)
    "github.com/boltdb-go/bolt": "github.com/boltdb/bolt",
}

# Top PyPI packages (typosquatting targets)
PYPI_TOP_PACKAGES: set[str] = {
    # Core packages
    "requests", "numpy", "pandas", "flask", "django", "boto3",
    "urllib3", "setuptools", "pip", "wheel", "six", "python-dateutil",
    "pyyaml", "certifi", "charset-normalizer", "idna", "typing-extensions",
    "cryptography", "cffi", "pycparser", "packaging", "attrs", "pluggy",
    "pytest", "coverage", "click", "jinja2", "markupsafe", "werkzeug",
    "sqlalchemy", "pillow", "scipy", "matplotlib", "scikit-learn",
    "tensorflow", "torch", "transformers", "fastapi", "uvicorn",
    "httpx", "aiohttp", "redis", "celery", "pydantic", "colorama",
    "tqdm", "rich", "black", "ruff", "mypy",
    # AI/ML Ecosystem (2024-2025)
    "langchain", "langchain-core", "langchain-community", "llamaindex",
    "llama-index", "openai", "anthropic", "huggingface_hub", "chromadb",
    "pinecone-client", "weaviate-client", "cohere", "replicate", "together",
    "groq", "gradio", "streamlit", "wandb", "mlflow", "sentence-transformers",
    "tiktoken", "tokenizers", "safetensors",
    # HuggingFace ecosystem (Grok xAI stack)
    "datasets", "accelerate", "peft", "trl", "bitsandbytes", "sentencepiece",
    # LLM Inference (high-performance)
    "vllm", "flash-attn", "triton", "xformers",
    # Telemetría/Observability
    "opentelemetry-api", "opentelemetry-sdk", "prometheus-client",
    # Data Engineering
    "pyspark", "dbt-core", "apache-airflow", "prefect", "dagster",
    "polars", "dask", "pyarrow", "delta-spark", "great-expectations",
    # Cloud SDKs
    "google-cloud-storage", "google-cloud-bigquery", "azure-identity",
    "azure-storage-blob", "snowflake-connector-python", "databricks-sdk",
}

# Top NPM packages (typosquatting targets)
NPM_TOP_PACKAGES: set[str] = {
    # Core packages
    "lodash", "react", "express", "axios", "moment", "chalk",
    "commander", "debug", "uuid", "dotenv", "yargs", "fs-extra",
    "glob", "async", "react-dom", "redux", "next", "vue",
    "webpack", "babel", "typescript", "jest", "mocha", "eslint",
    "prettier", "inquirer", "node-fetch", "mongoose", "sequelize",
    "prisma", "pg", "mongodb", "winston", "passport", "jsonwebtoken",
    "bcrypt", "cors", "helmet", "cross-env", "electron",
    # Modern Frontend (2024-2025)
    "tailwindcss", "vite", "esbuild", "turbo", "nx", "astro",
    "svelte", "solid-js", "qwik", "remix", "nuxt", "sass", "postcss",
    "autoprefixer", "@prisma/client", "drizzle-orm", "zod", "trpc",
    "@tanstack/react-query", "zustand", "jotai", "recoil", "immer",
    # AI/JS Ecosystem
    "langchain", "openai", "@anthropic-ai/sdk", "ai", "@vercel/ai",
}

# Secret signatures: (name, entropy_threshold, prefix)
SECRET_SIGNATURES: list[tuple[str, float, str]] = [
    # Core API Keys
    ("anthropic_api_key", 4.5, "sk-ant-api"),
    ("openai_api_key", 4.5, "sk-"),
    ("openai_org_key", 4.5, "org-"),
    ("aws_access_key", 4.0, "AKIA"),
    ("aws_secret_key", 4.5, ""),
    ("github_token", 4.5, "ghp_"),
    ("github_oauth", 4.5, "gho_"),
    ("github_pat", 4.5, "github_pat_"),
    ("stripe_live_key", 4.5, "sk_live_"),
    ("stripe_test_key", 4.0, "sk_test_"),
    ("slack_token", 4.5, "xoxb-"),
    ("slack_webhook", 4.0, "https://hooks.slack.com/"),
    ("jwt_secret", 4.0, ""),
    ("postgres_url", 3.5, "postgres://"),
    ("mysql_url", 3.5, "mysql://"),
    ("mongodb_url", 3.5, "mongodb://"),
    ("redis_url", 3.5, "redis://"),
    ("private_key", 4.0, "-----BEGIN"),
    ("google_api_key", 4.5, "AIza"),
    ("sendgrid_key", 4.5, "SG."),
    ("discord_webhook", 4.0, "https://discord.com/api/webhooks/"),
    ("npm_token", 4.5, "npm_"),
    ("pypi_token", 4.5, "pypi-"),
    # AI/ML & Observability (2024-2025)
    ("huggingface_token", 4.5, "hf_"),
    ("cohere_api_key", 4.5, ""),
    ("wandb_api_key", 4.0, ""),
    ("pinecone_api_key", 3.5, ""),
    ("datadog_api_key", 4.0, ""),
    ("datadog_app_key", 4.0, ""),
    ("slack_user_token", 4.5, "xoxp-"),
    ("telegram_bot_token", 5.0, ""),
    ("replicate_api_key", 4.5, "r8_"),
    ("groq_api_key", 4.5, "gsk_"),
    # Plataformas Adicionales (Grok Data 2025)
    ("heroku_api_key", 3.9, ""),
    ("slack_app_token", 4.5, "xapp-"),
    ("slack_config_token", 4.5, "xoxa-"),
    ("vercel_token", 4.5, ""),
    ("supabase_anon_key", 4.0, "eyJ"),
    ("supabase_service_key", 4.5, "eyJ"),
    ("planetscale_token", 4.5, "pscale_tkn_"),
    ("linear_api_key", 4.5, "lin_api_"),
    ("notion_api_key", 4.5, "secret_"),
    ("sentry_auth_token", 4.5, "sntrys_"),
]


def is_known_malicious(package_name: str) -> Optional[str]:
    """Check if a package is known malicious."""
    normalized = package_name.lower()
    return KNOWN_MALICIOUS.get(normalized) or KNOWN_MALICIOUS.get(package_name)


def is_legitimate_package(package_name: str, ecosystem: str) -> bool:
    """Check if a package is a legitimate top package."""
    normalized = package_name.lower()
    eco_lower = ecosystem.lower()

    if eco_lower in ("pypi", "python"):
        return normalized in PYPI_TOP_PACKAGES
    elif eco_lower in ("npm", "node", "javascript"):
        return normalized in NPM_TOP_PACKAGES
    else:
        return normalized in PYPI_TOP_PACKAGES or normalized in NPM_TOP_PACKAGES


def get_known_malicious_packages() -> list[tuple[str, str]]:
    """Get all known malicious packages."""
    return list(KNOWN_MALICIOUS.items())


def get_data_stats() -> dict[str, int]:
    """Get count of embedded data."""
    return {
        "malicious_packages": len(KNOWN_MALICIOUS),
        "pypi_top_packages": len(PYPI_TOP_PACKAGES),
        "npm_top_packages": len(NPM_TOP_PACKAGES),
        "secret_signatures": len(SECRET_SIGNATURES),
    }


def get_legitimate_packages(ecosystem: str) -> list[str]:
    """Get legitimate packages for an ecosystem."""
    eco_lower = ecosystem.lower()

    if eco_lower in ("pypi", "python"):
        return list(PYPI_TOP_PACKAGES)
    elif eco_lower in ("npm", "node", "javascript"):
        return list(NPM_TOP_PACKAGES)
    else:
        return list(PYPI_TOP_PACKAGES) + list(NPM_TOP_PACKAGES)


def get_entropy_threshold(secret_type: str) -> float:
    """Get entropy threshold for a secret type."""
    for name, threshold, _ in SECRET_SIGNATURES:
        if name == secret_type:
            return threshold
    return 4.0  # Default threshold


def matches_secret_prefix(value: str) -> Optional[str]:
    """Check if a string matches known secret prefixes."""
    for name, _, prefix in SECRET_SIGNATURES:
        if prefix and value.startswith(prefix):
            return name
    return None


def verify_data_integrity() -> bool:
    """Verify data integrity (always True in Python fallback)."""
    return True

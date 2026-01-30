"""
Qodacode Core - High-performance algorithms

This module provides the core algorithms for Qodacode, either from
the compiled Rust module (fast) or Python fallback (portable).

Usage:
    from qodacode._core import compute_fingerprint, compute_similarity_score

The module automatically selects the best available implementation.
"""

import logging

logger = logging.getLogger(__name__)

# Try to import from compiled Rust module
try:
    from qodacode_core import (
        compute_fingerprint,
        normalize_code,
        levenshtein_distance,
        compute_similarity_score,
        is_homoglyph_attack,
        keyboard_distance,
        is_safe_pattern,
        match_patterns,
        # Data Moats (embedded security data)
        is_known_malicious,
        is_legitimate_package,
        get_known_malicious_packages,
        get_data_stats,
        get_legitimate_packages,
        get_entropy_threshold,
        matches_secret_prefix,
        verify_data_integrity,
        RUST_CORE_AVAILABLE,
        __version__ as rust_version,
    )
    CORE_BACKEND = "rust"
    logger.debug(f"Using Rust core v{rust_version}")

except ImportError:
    # Fall back to pure Python implementation
    from qodacode._core._fallback import (
        compute_fingerprint,
        normalize_code,
        levenshtein_distance,
        compute_similarity_score,
        is_homoglyph_attack,
        keyboard_distance,
        is_safe_pattern,
        match_patterns,
        # Data Moats (embedded security data)
        is_known_malicious,
        is_legitimate_package,
        get_known_malicious_packages,
        get_data_stats,
        get_legitimate_packages,
        get_entropy_threshold,
        matches_secret_prefix,
        verify_data_integrity,
    )
    RUST_CORE_AVAILABLE = False
    CORE_BACKEND = "python"
    logger.debug("Rust core not available, using Python fallback")

__all__ = [
    # Core functions
    "compute_fingerprint",
    "normalize_code",
    "levenshtein_distance",
    "compute_similarity_score",
    "is_homoglyph_attack",
    "keyboard_distance",
    "is_safe_pattern",
    "match_patterns",
    # Data Moats (embedded security data)
    "is_known_malicious",
    "is_legitimate_package",
    "get_known_malicious_packages",
    "get_data_stats",
    "get_legitimate_packages",
    "get_entropy_threshold",
    "matches_secret_prefix",
    "verify_data_integrity",
    # Metadata
    "RUST_CORE_AVAILABLE",
    "CORE_BACKEND",
]

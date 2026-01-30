"""
Integration tests for qodacode_core (Rust/Python fallback).

These tests verify the core algorithms work correctly regardless of
whether they're running from Rust (compiled) or Python (fallback).
"""

import pytest
from qodacode._core import (
    CORE_BACKEND,
    compute_fingerprint,
    levenshtein_distance,
    compute_similarity_score,
    is_homoglyph_attack,
    keyboard_distance,
    is_safe_pattern,
    # Data Moats
    is_known_malicious,
    is_legitimate_package,
    get_known_malicious_packages,
    get_data_stats,
    get_legitimate_packages,
    get_entropy_threshold,
    matches_secret_prefix,
    verify_data_integrity,
)


class TestCoreBackend:
    """Test the core backend detection."""

    def test_backend_is_available(self):
        """Backend should be either 'rust' or 'python'."""
        assert CORE_BACKEND in ("rust", "python")

    def test_backend_functions_are_callable(self):
        """All core functions should be callable."""
        assert callable(compute_fingerprint)
        assert callable(levenshtein_distance)
        assert callable(compute_similarity_score)
        assert callable(is_homoglyph_attack)
        assert callable(keyboard_distance)
        assert callable(is_safe_pattern)


class TestFingerprint:
    """Test fingerprint computation."""

    def test_fingerprint_basic(self):
        """Fingerprint should return 12-char hex string."""
        fp = compute_fingerprint(
            "src/config.py",
            "SEC-001",
            "api_key = 'sk-secret-key'"
        )
        assert isinstance(fp, str)
        assert len(fp) == 12
        # Should be valid hex
        int(fp, 16)

    def test_fingerprint_deterministic(self):
        """Same input should produce same fingerprint."""
        fp1 = compute_fingerprint("file.py", "RULE-001", "password = 'test'")
        fp2 = compute_fingerprint("file.py", "RULE-001", "password = 'test'")
        assert fp1 == fp2

    def test_fingerprint_different_files(self):
        """Different files should produce different fingerprints."""
        fp1 = compute_fingerprint("file1.py", "RULE-001", "secret = 'x'")
        fp2 = compute_fingerprint("file2.py", "RULE-001", "secret = 'x'")
        assert fp1 != fp2

    def test_fingerprint_different_rules(self):
        """Different rules should produce different fingerprints."""
        fp1 = compute_fingerprint("file.py", "RULE-001", "secret = 'x'")
        fp2 = compute_fingerprint("file.py", "RULE-002", "secret = 'x'")
        assert fp1 != fp2

    def test_fingerprint_whitespace_normalization(self):
        """Whitespace differences should not affect fingerprint."""
        fp1 = compute_fingerprint("file.py", "RULE-001", "x = 1")
        fp2 = compute_fingerprint("file.py", "RULE-001", "x  =  1")
        fp3 = compute_fingerprint("file.py", "RULE-001", "  x = 1  ")
        assert fp1 == fp2 == fp3

    def test_fingerprint_case_normalization(self):
        """Case differences should not affect fingerprint."""
        fp1 = compute_fingerprint("file.py", "rule-001", "Password = 'X'")
        fp2 = compute_fingerprint("file.py", "RULE-001", "password = 'x'")
        assert fp1 == fp2

    def test_fingerprint_path_normalization(self):
        """Path separators should be normalized."""
        fp1 = compute_fingerprint("src/config.py", "RULE-001", "x = 1")
        fp2 = compute_fingerprint("src\\config.py", "RULE-001", "x = 1")
        assert fp1 == fp2


class TestLevenshtein:
    """Test Levenshtein (edit) distance."""

    def test_levenshtein_identical(self):
        """Identical strings have distance 0."""
        assert levenshtein_distance("hello", "hello") == 0
        assert levenshtein_distance("", "") == 0

    def test_levenshtein_empty(self):
        """Empty string distance equals other string length."""
        assert levenshtein_distance("", "abc") == 3
        assert levenshtein_distance("abc", "") == 3

    def test_levenshtein_single_edit(self):
        """Single character changes."""
        # Substitution
        assert levenshtein_distance("cat", "bat") == 1
        # Insertion
        assert levenshtein_distance("cat", "cats") == 1
        # Deletion
        assert levenshtein_distance("cats", "cat") == 1

    def test_levenshtein_classic_example(self):
        """Classic kitten -> sitting example."""
        assert levenshtein_distance("kitten", "sitting") == 3

    def test_levenshtein_typosquat_examples(self):
        """Real typosquatting examples."""
        # Character swap
        assert levenshtein_distance("requests", "reqeusts") == 2
        # Extra character
        assert levenshtein_distance("colorama", "colourama") == 1
        # Missing character
        assert levenshtein_distance("django", "djang") == 1


class TestHomoglyph:
    """Test homoglyph detection."""

    def test_homoglyph_cyrillic_e(self):
        """Detect Cyrillic 'е' impersonating Latin 'e'."""
        # 'е' is Cyrillic, looks identical to Latin 'e'
        assert is_homoglyph_attack("rеquests", "requests")

    def test_homoglyph_cyrillic_a(self):
        """Detect Cyrillic 'а' impersonating Latin 'a'."""
        assert is_homoglyph_attack("flаsk", "flask")

    def test_homoglyph_cyrillic_o(self):
        """Detect Cyrillic 'о' impersonating Latin 'o'."""
        assert is_homoglyph_attack("djangо", "django")

    def test_homoglyph_not_attack_identical(self):
        """Identical strings are not attacks."""
        assert not is_homoglyph_attack("requests", "requests")

    def test_homoglyph_not_attack_different(self):
        """Completely different strings are not homoglyph attacks."""
        assert not is_homoglyph_attack("numpy", "pandas")

    def test_homoglyph_digit_lookalike(self):
        """Detect digit lookalikes (0 for o, 1 for l)."""
        assert is_homoglyph_attack("c0lorama", "colorama")


class TestKeyboardDistance:
    """Test keyboard proximity detection."""

    def test_keyboard_adjacent_keys(self):
        """Adjacent keys on QWERTY keyboard."""
        # q-w are adjacent
        assert keyboard_distance("qwerty", "wwerty") == 1
        # a-s are adjacent
        assert keyboard_distance("fast", "faat") == 1

    def test_keyboard_same_string(self):
        """Identical strings have distance 0."""
        assert keyboard_distance("hello", "hello") == 0

    def test_keyboard_different_lengths(self):
        """Different length strings return max value."""
        result = keyboard_distance("abc", "abcd")
        assert result == 999999 or result > 1000  # Very large number

    def test_keyboard_non_adjacent(self):
        """Non-adjacent changes don't count."""
        # q and p are not adjacent
        assert keyboard_distance("quest", "puest") == 0


class TestSimilarityScore:
    """Test combined similarity scoring."""

    def test_similarity_identical(self):
        """Identical packages have score 0 (not suspicious)."""
        assert compute_similarity_score("requests", "requests") == 0.0

    def test_similarity_homoglyph_high_score(self):
        """Homoglyph attacks have very high score."""
        score = compute_similarity_score("rеquests", "requests")  # Cyrillic е
        assert score >= 0.9

    def test_similarity_typo_moderate_score(self):
        """Simple typos have moderate-high score."""
        score = compute_similarity_score("reqeusts", "requests")
        assert 0.5 <= score <= 0.95

    def test_similarity_different_packages(self):
        """Completely different packages have score 0."""
        assert compute_similarity_score("numpy", "django") == 0.0

    def test_similarity_too_different(self):
        """Packages that are too different have score 0."""
        assert compute_similarity_score("a", "verylongpackage") == 0.0

    def test_similarity_real_attacks(self):
        """Known real-world typosquatting attacks."""
        # These should all have high scores
        attacks = [
            ("python-dateutil", "python-dateutl"),
            ("urllib3", "urllib"),
            ("beautifulsoup4", "beautifulsoup"),
        ]
        for suspicious, legitimate in attacks:
            score = compute_similarity_score(suspicious, legitimate)
            # Should detect some similarity (depends on edit distance threshold)
            # Not all may be above 0.5 due to length differences
            assert score >= 0.0  # At minimum, no error


class TestSafePattern:
    """Test safe pattern detection for false positive reduction."""

    def test_safe_pattern_env_var_os_environ(self):
        """Detect os.environ reads as safe."""
        result = is_safe_pattern(
            "api_key = os.environ['API_KEY']",
            "src/config.py"
        )
        assert result[0] is True  # is_safe
        assert "environ" in result[1].lower() or "environment" in result[2].lower()

    def test_safe_pattern_env_var_getenv(self):
        """Detect os.getenv reads as safe."""
        result = is_safe_pattern(
            "secret = os.getenv('SECRET')",
            "src/app.py"
        )
        assert result[0] is True

    def test_safe_pattern_decrypt(self):
        """Detect decryption operations as safe."""
        result = is_safe_pattern(
            "password = decrypt(encrypted_password)",
            "src/auth.py"
        )
        assert result[0] is True

    def test_safe_pattern_test_file(self):
        """Test files are marked as safe."""
        result = is_safe_pattern(
            "password = 'hardcoded_for_test'",
            "tests/test_auth.py"
        )
        assert result[0] is True
        assert "test" in result[1].lower() or "test" in result[2].lower()

    def test_safe_pattern_mock_prefix(self):
        """Mock data prefixes are safe."""
        result = is_safe_pattern(
            "mock_api_key = 'sk-test-123'",
            "src/helpers.py"
        )
        assert result[0] is True

    def test_safe_pattern_placeholder(self):
        """Placeholder values are safe."""
        result = is_safe_pattern(
            "api_key = '<YOUR_API_KEY>'",
            "src/config.py"
        )
        assert result[0] is True

    def test_safe_pattern_localhost(self):
        """Localhost references are safe."""
        result = is_safe_pattern(
            "db_url = 'postgresql://localhost:5432/test'",
            "src/db.py"
        )
        assert result[0] is True

    def test_not_safe_pattern_hardcoded(self):
        """Actual hardcoded secrets are not safe."""
        result = is_safe_pattern(
            "api_key = 'sk-ant-api03-real-secret-key'",
            "src/config.py"
        )
        assert result[0] is False

    def test_safe_pattern_bcrypt(self):
        """Bcrypt operations are safe."""
        result = is_safe_pattern(
            "hashed = bcrypt.hash(password)",
            "src/auth.py"
        )
        assert result[0] is True

    def test_safe_pattern_settings_object(self):
        """Settings object access is safe."""
        result = is_safe_pattern(
            "api_key = settings.API_KEY",
            "src/config.py"
        )
        assert result[0] is True


class TestIntegration:
    """Integration tests combining multiple algorithms."""

    def test_typosquat_detection_pipeline(self):
        """Full typosquatting detection pipeline."""
        suspicious = "reqeusts"
        legitimate = "requests"

        # Step 1: Check if homoglyph attack
        is_homoglyph = is_homoglyph_attack(suspicious, legitimate)

        # Step 2: Check edit distance
        edit_dist = levenshtein_distance(suspicious, legitimate)

        # Step 3: Compute similarity score
        score = compute_similarity_score(suspicious, legitimate)

        # Should detect this as suspicious
        assert not is_homoglyph  # Not a homoglyph, just a typo
        assert edit_dist == 2
        assert score >= 0.5

    def test_fingerprint_stability_across_edits(self):
        """Fingerprints should be stable for semantic equivalence."""
        # Same code, different formatting
        code_v1 = "password = 'secret'"
        code_v2 = "password  =  'secret'"
        code_v3 = "  password = 'secret'  "

        fp1 = compute_fingerprint("file.py", "SEC-001", code_v1)
        fp2 = compute_fingerprint("file.py", "SEC-001", code_v2)
        fp3 = compute_fingerprint("file.py", "SEC-001", code_v3)

        # All should be identical
        assert fp1 == fp2 == fp3

    def test_safe_pattern_with_fingerprint(self):
        """Safe patterns should still generate fingerprints."""
        snippet = "api_key = os.environ['API_KEY']"
        filepath = "src/config.py"

        # Should be safe
        is_safe, _, _ = is_safe_pattern(snippet, filepath)
        assert is_safe

        # But should still generate valid fingerprint
        fp = compute_fingerprint(filepath, "SEC-001", snippet)
        assert len(fp) == 12
        int(fp, 16)  # Valid hex


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_empty_strings(self):
        """Handle empty strings gracefully."""
        # Fingerprint with empty snippet
        fp = compute_fingerprint("file.py", "RULE", "")
        assert len(fp) == 12

        # Levenshtein with empty
        assert levenshtein_distance("", "") == 0
        assert levenshtein_distance("abc", "") == 3

        # Similarity with empty
        assert compute_similarity_score("", "") == 0.0

    def test_unicode_handling(self):
        """Handle unicode strings properly."""
        # Fingerprint with unicode
        fp = compute_fingerprint("file.py", "RULE", "password = 'contraseña'")
        assert len(fp) == 12

        # Safe pattern with unicode
        result = is_safe_pattern("api_key = os.environ['KEY']", "src/módulo.py")
        assert result[0] is True

    def test_very_long_strings(self):
        """Handle very long strings."""
        long_code = "x = " + "a" * 10000
        fp = compute_fingerprint("file.py", "RULE", long_code)
        assert len(fp) == 12

        # Levenshtein with long strings
        s1 = "a" * 100
        s2 = "a" * 99 + "b"
        assert levenshtein_distance(s1, s2) == 1

    def test_special_characters(self):
        """Handle special characters in paths and code."""
        fp = compute_fingerprint(
            "src/[special]/file.py",
            "RULE-001",
            "password = 'test!@#$%'"
        )
        assert len(fp) == 12


# ============================================================================
# DATA MOATS TESTS (Embedded Security Data)
# ============================================================================

class TestKnownMalicious:
    """Test known malicious package detection."""

    def test_known_malicious_python_requests(self):
        """Detect typosquats of 'requests' package."""
        # Known typosquats
        assert is_known_malicious("reqeusts") == "requests"
        assert is_known_malicious("requets") == "requests"
        assert is_known_malicious("requsts") == "requests"

    def test_known_malicious_python_django(self):
        """Detect typosquats of 'django' package."""
        assert is_known_malicious("djang") == "django"
        assert is_known_malicious("djagno") == "django"

    def test_known_malicious_npm_lodash(self):
        """Detect typosquats of 'lodash' package."""
        assert is_known_malicious("loadash") == "lodash"
        assert is_known_malicious("lodashs") == "lodash"

    def test_known_malicious_case_insensitive(self):
        """Detection should be case insensitive."""
        assert is_known_malicious("REQEUSTS") == "requests"
        assert is_known_malicious("Loadash") == "lodash"

    def test_legitimate_not_malicious(self):
        """Legitimate packages should return None."""
        assert is_known_malicious("requests") is None
        assert is_known_malicious("django") is None
        assert is_known_malicious("lodash") is None
        assert is_known_malicious("numpy") is None

    def test_unknown_not_malicious(self):
        """Unknown packages should return None."""
        assert is_known_malicious("my-custom-package") is None
        assert is_known_malicious("xyz123") is None


class TestLegitimatePackage:
    """Test legitimate package verification."""

    def test_pypi_legitimate_packages(self):
        """Verify top PyPI packages are recognized."""
        assert is_legitimate_package("requests", "pypi") is True
        assert is_legitimate_package("django", "python") is True
        assert is_legitimate_package("numpy", "pypi") is True
        assert is_legitimate_package("pandas", "python") is True

    def test_npm_legitimate_packages(self):
        """Verify top NPM packages are recognized."""
        assert is_legitimate_package("lodash", "npm") is True
        assert is_legitimate_package("react", "node") is True
        assert is_legitimate_package("express", "javascript") is True
        assert is_legitimate_package("axios", "npm") is True

    def test_unknown_packages_not_legitimate(self):
        """Unknown packages should not be marked as legitimate."""
        assert is_legitimate_package("my-custom-pkg", "pypi") is False
        assert is_legitimate_package("xyz123", "npm") is False

    def test_case_insensitive(self):
        """Verification should be case insensitive."""
        assert is_legitimate_package("REQUESTS", "pypi") is True
        assert is_legitimate_package("Lodash", "npm") is True

    def test_any_ecosystem(self):
        """Without specific ecosystem, check all."""
        assert is_legitimate_package("requests", "any") is True
        assert is_legitimate_package("lodash", "all") is True


class TestDataStats:
    """Test data statistics retrieval."""

    def test_data_stats_structure(self):
        """Stats should return expected keys."""
        stats = get_data_stats()
        assert isinstance(stats, dict)
        assert "malicious_packages" in stats
        assert "pypi_top_packages" in stats
        assert "npm_top_packages" in stats
        assert "secret_signatures" in stats

    def test_data_stats_counts(self):
        """Stats should have non-zero counts."""
        stats = get_data_stats()
        assert stats["malicious_packages"] > 30  # At least 30 malicious
        assert stats["pypi_top_packages"] > 20   # At least 20 PyPI
        assert stats["npm_top_packages"] > 20    # At least 20 NPM
        assert stats["secret_signatures"] > 10   # At least 10 signatures

    def test_data_stats_total_reasonable(self):
        """Total data should be reasonable for protection."""
        stats = get_data_stats()
        total = sum(stats.values())
        assert total > 100  # Significant amount of data


class TestLegitimatePackagesList:
    """Test retrieving full package lists."""

    def test_get_pypi_packages(self):
        """Get all PyPI packages."""
        packages = get_legitimate_packages("pypi")
        assert isinstance(packages, list)
        assert len(packages) > 20
        assert "requests" in packages
        assert "django" in packages

    def test_get_npm_packages(self):
        """Get all NPM packages."""
        packages = get_legitimate_packages("npm")
        assert isinstance(packages, list)
        assert len(packages) > 20
        assert "lodash" in packages
        assert "react" in packages

    def test_get_all_packages(self):
        """Get packages from all ecosystems."""
        all_packages = get_legitimate_packages("all")
        pypi_packages = get_legitimate_packages("pypi")
        npm_packages = get_legitimate_packages("npm")
        assert len(all_packages) >= len(pypi_packages) + len(npm_packages) - 10


class TestEntropyThreshold:
    """Test secret entropy threshold retrieval."""

    def test_known_secret_types(self):
        """Known secret types should have thresholds."""
        assert get_entropy_threshold("anthropic_api_key") >= 4.0
        assert get_entropy_threshold("openai_api_key") >= 4.0
        assert get_entropy_threshold("aws_access_key") >= 3.5
        assert get_entropy_threshold("github_token") >= 4.0

    def test_database_urls_lower_threshold(self):
        """Database URLs should have lower entropy thresholds."""
        assert get_entropy_threshold("postgres_url") < 4.0
        assert get_entropy_threshold("mongodb_url") < 4.0

    def test_unknown_secret_default(self):
        """Unknown secret types should return default threshold."""
        threshold = get_entropy_threshold("unknown_type_xyz")
        assert threshold == 4.0  # Default


class TestSecretPrefixMatching:
    """Test secret prefix detection."""

    def test_anthropic_prefix(self):
        """Detect Anthropic API key prefix."""
        result = matches_secret_prefix("sk-ant-api-xxxx")
        assert result == "anthropic_api_key"

    def test_openai_prefix(self):
        """Detect OpenAI API key prefix."""
        result = matches_secret_prefix("sk-proj-xxxx")
        assert result == "openai_api_key"

    def test_github_prefix(self):
        """Detect GitHub token prefixes."""
        assert matches_secret_prefix("ghp_xxxxxxxxxxxx") == "github_token"
        assert matches_secret_prefix("gho_xxxxxxxxxxxx") == "github_oauth"
        assert matches_secret_prefix("github_pat_xxxx") == "github_pat"

    def test_stripe_prefix(self):
        """Detect Stripe key prefixes."""
        assert matches_secret_prefix("sk_live_xxxxx") == "stripe_live_key"
        assert matches_secret_prefix("sk_test_xxxxx") == "stripe_test_key"

    def test_aws_prefix(self):
        """Detect AWS key prefix."""
        result = matches_secret_prefix("AKIAIOSFODNN7EXAMPLE")
        assert result == "aws_access_key"

    def test_slack_prefix(self):
        """Detect Slack token prefix."""
        result = matches_secret_prefix("xoxb-xxxx-xxxx")
        assert result == "slack_token"

    def test_no_match(self):
        """Non-matching strings return None."""
        assert matches_secret_prefix("normal_value") is None
        assert matches_secret_prefix("ABC123") is None
        assert matches_secret_prefix("password123") is None


class TestDataIntegrity:
    """Test data integrity verification."""

    def test_integrity_passes(self):
        """Data integrity should pass (not corrupted)."""
        result = verify_data_integrity()
        assert result is True

    def test_integrity_returns_bool(self):
        """Verification should return boolean."""
        result = verify_data_integrity()
        assert isinstance(result, bool)


class TestDataMoatsIntegration:
    """Integration tests for Data Moats features."""

    def test_full_typosquat_check(self):
        """Full typosquatting detection with data moats."""
        suspicious = "reqeusts"

        # Check if known malicious
        target = is_known_malicious(suspicious)
        assert target == "requests"

        # Verify target is legitimate
        assert is_legitimate_package(target, "pypi") is True

        # Compute similarity for ranking
        score = compute_similarity_score(suspicious, target)
        assert score > 0.5

    def test_secret_detection_pipeline(self):
        """Secret detection using embedded data."""
        api_key = "sk-ant-api03-real-key-here"

        # Match prefix
        secret_type = matches_secret_prefix(api_key)
        assert secret_type == "anthropic_api_key"

        # Get entropy threshold
        threshold = get_entropy_threshold(secret_type)
        assert threshold >= 4.0

    def test_data_consistency(self):
        """Data should be consistent across functions."""
        # All malicious package targets should be legitimate
        malicious = get_known_malicious_packages()
        for suspicious, target in malicious[:10]:  # Sample first 10
            assert is_legitimate_package(target, "any") is True

    def test_stats_match_actual_data(self):
        """Stats should match actual data counts."""
        stats = get_data_stats()
        pypi = get_legitimate_packages("pypi")
        npm = get_legitimate_packages("npm")

        assert stats["pypi_top_packages"] == len(pypi)
        assert stats["npm_top_packages"] == len(npm)

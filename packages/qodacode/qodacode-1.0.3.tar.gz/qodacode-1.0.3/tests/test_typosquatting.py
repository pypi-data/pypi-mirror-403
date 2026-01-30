"""
Tests for typosquatting detection.
"""

import tempfile
from pathlib import Path

import pytest

from qodacode.typosquatting import (
    TyposquattingDetector,
    levenshtein_distance,
    detect_homoglyphs,
    keyboard_proximity_score,
)
from qodacode.typosquatting.database import PackageDatabase, KNOWN_MALICIOUS
from qodacode.typosquatting.detector import RiskLevel, scan_directory


class TestLevenshteinDistance:
    """Test Levenshtein distance calculation."""

    def test_same_string(self):
        assert levenshtein_distance("requests", "requests") == 0

    def test_one_char_difference(self):
        assert levenshtein_distance("requests", "reqeusts") == 2  # swap eu
        assert levenshtein_distance("numpy", "numpyy") == 1  # extra char
        assert levenshtein_distance("flask", "flaск") == 2  # different chars

    def test_two_char_difference(self):
        assert levenshtein_distance("django", "djagno") == 2

    def test_empty_string(self):
        assert levenshtein_distance("", "test") == 4
        assert levenshtein_distance("test", "") == 4

    def test_completely_different(self):
        assert levenshtein_distance("abc", "xyz") == 3


class TestHomoglyphDetection:
    """Test homoglyph character detection."""

    def test_no_homoglyphs(self):
        result = detect_homoglyphs("requests")
        assert len(result) == 0

    def test_capital_i_for_l(self):
        # fIask with capital I instead of lowercase l
        result = detect_homoglyphs("fIask")
        assert len(result) >= 1
        # I maps to l or 1 depending on mapping direction
        suspicious_chars = [r[1] for r in result]
        assert "I" in suspicious_chars

    def test_zero_for_o(self):
        result = detect_homoglyphs("fl0sk")  # zero instead of o
        # 0 maps to o
        assert len(result) >= 1
        suspicious_chars = [r[1] for r in result]
        assert "0" in suspicious_chars

    def test_cyrillic_chars(self):
        # Cyrillic 'а' looks like Latin 'a'
        result = detect_homoglyphs("requеsts")  # Cyrillic е
        assert len(result) >= 1


class TestKeyboardProximity:
    """Test keyboard proximity scoring."""

    def test_same_string(self):
        score = keyboard_proximity_score("flask", "flask")
        assert score == 0.0

    def test_different_length(self):
        score = keyboard_proximity_score("flask", "flasky")
        assert score == 0.0

    def test_adjacent_keys(self):
        # s and a are adjacent on QWERTY
        score = keyboard_proximity_score("flask", "flsak")
        assert score > 0


class TestPackageDatabase:
    """Test package database."""

    def test_pypi_database(self):
        db = PackageDatabase("pypi")
        assert db.size() > 50
        assert db.contains("requests")
        assert db.contains("numpy")
        assert db.contains("django")

    def test_npm_database(self):
        db = PackageDatabase("npm")
        assert db.size() > 50
        assert db.contains("lodash")
        assert db.contains("react")
        assert db.contains("express")

    def test_known_malicious(self):
        db = PackageDatabase("pypi")
        assert db.is_known_malicious("reqeusts") == "requests"
        assert db.is_known_malicious("loadash") == "lodash"
        assert db.is_known_malicious("requests") is None  # Legit package

    def test_normalization(self):
        db = PackageDatabase("pypi")
        # Underscores and hyphens should be equivalent
        assert db.contains("python-dateutil") or db.contains("python_dateutil")


class TestTyposquattingDetector:
    """Test the main detector."""

    def test_detect_known_malicious(self):
        detector = TyposquattingDetector()
        matches = detector.detect_packages(["reqeusts", "requests"], "pypi")

        assert len(matches) == 1
        assert matches[0].suspicious_package == "reqeusts"
        assert matches[0].legitimate_package == "requests"
        assert matches[0].risk_level == RiskLevel.CRITICAL

    def test_detect_similar_package(self):
        detector = TyposquattingDetector()
        # "requesst" is similar to "requests" (distance 1) but not in KNOWN_MALICIOUS
        matches = detector.detect_packages(["requesst"], "pypi")

        assert len(matches) == 1
        assert matches[0].suspicious_package == "requesst"
        assert matches[0].risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]

    def test_legitimate_package_not_flagged(self):
        detector = TyposquattingDetector()
        matches = detector.detect_packages(["requests", "numpy", "flask"], "pypi")

        assert len(matches) == 0

    def test_detect_npm_packages(self):
        detector = TyposquattingDetector()
        matches = detector.detect_packages(["loadash", "lodash"], "npm")

        assert len(matches) == 1
        assert matches[0].suspicious_package == "loadash"
        assert matches[0].legitimate_package == "lodash"


class TestFileDetection:
    """Test detection from files."""

    def test_requirements_txt(self):
        detector = TyposquattingDetector()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("requests==2.28.0\n")
            f.write("reqeusts>=1.0\n")  # Typosquat
            f.write("numpy\n")
            f.write("# comment\n")
            f.flush()

            matches = detector.detect_file(f.name)

        assert len(matches) == 1
        assert matches[0].suspicious_package == "reqeusts"

    def test_package_json(self):
        detector = TyposquattingDetector()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            import json
            content = {
                "dependencies": {
                    "lodash": "^4.17.21",
                    "loadash": "^1.0.0",  # Typosquat
                },
                "devDependencies": {
                    "express": "^4.18.0",
                }
            }
            json.dump(content, f)
            f.flush()

            # Rename to package.json for detection
            path = Path(f.name)
            pkg_path = path.parent / "package.json"
            path.rename(pkg_path)

            matches = detector.detect_file(str(pkg_path))

        assert len(matches) == 1
        assert matches[0].suspicious_package == "loadash"

    def test_empty_file(self):
        detector = TyposquattingDetector()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            f.flush()

            matches = detector.detect_file(f.name)

        assert len(matches) == 0


class TestScanDirectory:
    """Test directory scanning."""

    def test_scan_with_requirements(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a requirements.txt with a typosquat
            req_path = Path(tmpdir) / "requirements.txt"
            req_path.write_text("requests\nreqeusts\n")

            results = scan_directory(tmpdir)

            assert str(req_path) in results
            assert len(results[str(req_path)]) == 1

    def test_scan_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = scan_directory(tmpdir)
            assert len(results) == 0


class TestMatchOutput:
    """Test match output formatting."""

    def test_to_dict(self):
        detector = TyposquattingDetector()
        matches = detector.detect_packages(["reqeusts"], "pypi")

        assert len(matches) == 1
        d = matches[0].to_dict()

        assert "suspicious_package" in d
        assert "legitimate_package" in d
        assert "risk_level" in d
        assert "reason" in d
        assert d["risk_level"] in ["critical", "high", "medium", "low"]

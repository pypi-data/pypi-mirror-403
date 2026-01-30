"""
Typosquatting Detector - Core detection logic.

Scans dependency files for potential typosquatting attacks.
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from qodacode.typosquatting.database import PackageDatabase, KNOWN_MALICIOUS
from qodacode.typosquatting.similarity import (
    levenshtein_distance,
    detect_homoglyphs,
    keyboard_proximity_score,
    normalize_package_name,
)


class RiskLevel(Enum):
    """Risk level for typosquatting detection."""
    CRITICAL = "critical"  # Known malicious package
    HIGH = "high"  # Very similar to popular package (distance 1)
    MEDIUM = "medium"  # Somewhat similar (distance 2)
    LOW = "low"  # Possibly suspicious


@dataclass
class TyposquatMatch:
    """A potential typosquatting match."""
    suspicious_package: str
    legitimate_package: str
    distance: int
    risk_level: RiskLevel
    reason: str
    has_homoglyphs: bool = False
    keyboard_typo_score: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "suspicious_package": self.suspicious_package,
            "legitimate_package": self.legitimate_package,
            "distance": self.distance,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "has_homoglyphs": self.has_homoglyphs,
            "keyboard_typo_score": self.keyboard_typo_score,
        }


class TyposquattingDetector:
    """
    Detector for typosquatting attacks in package dependencies.

    Supports:
    - requirements.txt (Python/pip)
    - package.json (Node.js/npm)
    - Pipfile (Python/pipenv)
    - pyproject.toml (Python/poetry)
    """

    def __init__(self, ecosystem: Optional[str] = None):
        """
        Initialize the detector.

        Args:
            ecosystem: "pypi", "npm", or None for auto-detection
        """
        self.ecosystem = ecosystem
        self._pypi_db = PackageDatabase("pypi")
        self._npm_db = PackageDatabase("npm")

    def detect_file(self, filepath: str) -> List[TyposquatMatch]:
        """
        Scan a dependency file for typosquatting.

        Args:
            filepath: Path to dependency file

        Returns:
            List of potential typosquatting matches
        """
        path = Path(filepath)
        if not path.exists():
            return []

        filename = path.name.lower()

        # Determine file type and parse
        if filename == "requirements.txt" or filename.endswith(".txt"):
            packages = self._parse_requirements_txt(path)
            db = self._pypi_db
        elif filename == "package.json":
            packages = self._parse_package_json(path)
            db = self._npm_db
        elif filename == "pipfile":
            packages = self._parse_pipfile(path)
            db = self._pypi_db
        elif filename == "pyproject.toml":
            packages = self._parse_pyproject_toml(path)
            db = self._pypi_db
        else:
            # Try to detect by content
            packages = self._parse_requirements_txt(path)
            db = self._pypi_db

        return self._check_packages(packages, db)

    def detect_packages(
        self,
        packages: List[str],
        ecosystem: str = "pypi"
    ) -> List[TyposquatMatch]:
        """
        Check a list of packages for typosquatting.

        Args:
            packages: List of package names
            ecosystem: "pypi" or "npm"

        Returns:
            List of potential typosquatting matches
        """
        db = self._pypi_db if ecosystem == "pypi" else self._npm_db
        return self._check_packages(packages, db)

    def _check_packages(
        self,
        packages: List[str],
        db: PackageDatabase
    ) -> List[TyposquatMatch]:
        """Check packages against the database."""
        matches = []

        for pkg in packages:
            # Skip empty names
            if not pkg or not pkg.strip():
                continue

            pkg_normalized = normalize_package_name(pkg)

            # Skip if it's a known legitimate package
            if db.contains(pkg):
                continue

            # Check if it's a known malicious package
            known_target = db.is_known_malicious(pkg)
            if known_target:
                matches.append(TyposquatMatch(
                    suspicious_package=pkg,
                    legitimate_package=known_target,
                    distance=levenshtein_distance(pkg_normalized, normalize_package_name(known_target)),
                    risk_level=RiskLevel.CRITICAL,
                    reason=f"Known malicious package impersonating '{known_target}'",
                ))
                continue

            # Check against all packages in database
            best_match = self._find_best_match(pkg, db)
            if best_match:
                matches.append(best_match)

        return matches

    def _find_best_match(
        self,
        package: str,
        db: PackageDatabase
    ) -> Optional[TyposquatMatch]:
        """Find the best matching legitimate package."""
        pkg_normalized = normalize_package_name(package)
        best_match = None
        best_distance = float("inf")

        for legit_pkg in db.get_all_packages():
            legit_normalized = normalize_package_name(legit_pkg)

            # Skip if same after normalization
            if pkg_normalized == legit_normalized:
                continue

            # Calculate Levenshtein distance
            distance = levenshtein_distance(pkg_normalized, legit_normalized)

            # Only consider close matches
            if distance > 2:
                continue

            # Check if this is the best match
            if distance < best_distance:
                best_distance = distance
                best_match = legit_pkg

        if best_match is None:
            return None

        # Determine risk level and reason
        homoglyphs = detect_homoglyphs(package)
        keyboard_score = keyboard_proximity_score(
            normalize_package_name(package),
            normalize_package_name(best_match)
        )

        if best_distance == 1:
            risk_level = RiskLevel.HIGH
            if homoglyphs:
                reason = f"Contains homoglyph characters, similar to '{best_match}'"
            elif keyboard_score > 0.5:
                reason = f"Keyboard typo of '{best_match}' (adjacent keys)"
            else:
                reason = f"One character different from popular package '{best_match}'"
        else:
            risk_level = RiskLevel.MEDIUM
            reason = f"Similar to popular package '{best_match}' (distance: {best_distance})"

        return TyposquatMatch(
            suspicious_package=package,
            legitimate_package=best_match,
            distance=best_distance,
            risk_level=risk_level,
            reason=reason,
            has_homoglyphs=bool(homoglyphs),
            keyboard_typo_score=keyboard_score,
        )

    def _parse_requirements_txt(self, path: Path) -> List[str]:
        """Parse requirements.txt file."""
        packages = []
        try:
            content = path.read_text()
            for line in content.splitlines():
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                # Extract package name (before any version specifier)
                match = re.match(r"^([a-zA-Z0-9_\-\.]+)", line)
                if match:
                    packages.append(match.group(1))
        except Exception:
            pass
        return packages

    def _parse_package_json(self, path: Path) -> List[str]:
        """Parse package.json file."""
        packages = []
        try:
            content = json.loads(path.read_text())
            # Get dependencies from all sections
            for key in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]:
                if key in content and isinstance(content[key], dict):
                    packages.extend(content[key].keys())
        except Exception:
            pass
        return packages

    def _parse_pipfile(self, path: Path) -> List[str]:
        """Parse Pipfile (simplified TOML parsing)."""
        packages = []
        try:
            content = path.read_text()
            in_packages_section = False
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("[packages]") or line.startswith("[dev-packages]"):
                    in_packages_section = True
                    continue
                if line.startswith("[") and in_packages_section:
                    in_packages_section = False
                    continue
                if in_packages_section and "=" in line:
                    pkg_name = line.split("=")[0].strip().strip('"').strip("'")
                    if pkg_name:
                        packages.append(pkg_name)
        except Exception:
            pass
        return packages

    def _parse_pyproject_toml(self, path: Path) -> List[str]:
        """Parse pyproject.toml (simplified TOML parsing)."""
        packages = []
        try:
            content = path.read_text()
            # Look for dependencies in various formats
            # poetry: [tool.poetry.dependencies]
            # pip: [project.dependencies]
            in_deps_section = False
            for line in content.splitlines():
                line = line.strip()
                if "dependencies" in line.lower() and line.startswith("["):
                    in_deps_section = True
                    continue
                if line.startswith("[") and in_deps_section:
                    in_deps_section = False
                    continue
                if in_deps_section:
                    # Extract package name using regex (handles all formats)
                    # Matches: "package>=1.0", 'package', package = "version", etc.
                    match = re.match(r'^["\']?([a-zA-Z0-9][a-zA-Z0-9_\-\.]*[a-zA-Z0-9]|[a-zA-Z0-9])', line)
                    if match:
                        pkg_name = match.group(1)
                        if pkg_name and pkg_name != "python":
                            packages.append(pkg_name)
        except Exception:
            pass
        return packages


def scan_directory(directory: str) -> Dict[str, List[TyposquatMatch]]:
    """
    Scan a directory for dependency files and check for typosquatting.

    Args:
        directory: Path to directory

    Returns:
        Dictionary mapping file paths to their matches
    """
    detector = TyposquattingDetector()
    results: Dict[str, List[TyposquatMatch]] = {}

    path = Path(directory)
    if not path.exists():
        return results

    # Files to scan
    dep_files = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "dev-requirements.txt",
        "test-requirements.txt",
        "package.json",
        "Pipfile",
        "pyproject.toml",
    ]

    for filename in dep_files:
        filepath = path / filename
        if filepath.exists():
            matches = detector.detect_file(str(filepath))
            if matches:
                results[str(filepath)] = matches

    return results

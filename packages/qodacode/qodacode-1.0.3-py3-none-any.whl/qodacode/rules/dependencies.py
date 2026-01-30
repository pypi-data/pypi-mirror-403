"""
Dependency rules for Qodacode.

DEP-001: vulnerable-package - Dependencies with known CVEs (OSV + offline fallback)
DEP-002: outdated-dependency - Dependencies significantly behind latest
DEP-004: license-risk - Dependencies with restrictive licenses
"""

import json
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import tree_sitter

from qodacode.rules.base import Rule, Issue, Severity, Category


class VulnerablePackageRule(Rule):
    """
    DEP-001: Detect dependencies with known vulnerabilities.

    Uses Google's OSV database for real-time CVE lookup.
    Falls back to offline patterns if network unavailable.
    """
    id = "DEP-001"
    name = "vulnerable-package"
    description = "Detects dependencies with known security vulnerabilities (OSV + offline)"
    severity = Severity.CRITICAL
    category = Category.DEPENDENCIES
    languages = ["python", "javascript", "typescript"]

    # Offline fallback patterns (used when OSV unavailable)
    OFFLINE_VULNERABILITIES = {
        "django": [
            ("< 3.2.14", "CVE-2022-34265", "SQL injection in Trunc/Extract"),
            ("< 4.0.6", "CVE-2022-34265", "SQL injection in Trunc/Extract"),
        ],
        "flask": [
            ("< 2.2.5", "CVE-2023-30861", "Cookie session vulnerability"),
        ],
        "requests": [
            ("< 2.31.0", "CVE-2023-32681", "Proxy-Authorization header leak"),
        ],
        "urllib3": [
            ("< 1.26.18", "CVE-2023-45803", "Request body not stripped on redirect"),
        ],
        "pillow": [
            ("< 9.3.0", "CVE-2022-45199", "DoS via crafted image"),
        ],
        "cryptography": [
            ("< 41.0.0", "CVE-2023-38325", "NULL dereference in PKCS7"),
        ],
        "lodash": [
            ("< 4.17.21", "CVE-2021-23337", "Command injection"),
        ],
        "axios": [
            ("< 1.6.0", "CVE-2023-45857", "CSRF vulnerability"),
        ],
        "express": [
            ("< 4.18.2", "CVE-2022-24999", "Open redirect"),
        ],
        "jsonwebtoken": [
            ("< 9.0.0", "CVE-2022-23529", "Algorithm confusion"),
        ],
    }

    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        """Check dependencies for vulnerabilities using OSV API."""
        issues = []
        source_str = source.decode("utf-8", errors="replace")

        # Try OSV first (real-time CVE database)
        osv_issues = self._check_with_osv(filepath, source_str)
        if osv_issues:
            return osv_issues

        # Fallback to offline detection
        return self._check_offline(filepath, source_str)

    def _check_with_osv(self, filepath: str, source_str: str) -> List[Issue]:
        """Query OSV database for real vulnerabilities."""
        try:
            from qodacode.osv import scan_dependencies

            findings = scan_dependencies(filepath, source_str)
            issues = []

            severity_map = {
                "CRITICAL": Severity.CRITICAL,
                "HIGH": Severity.HIGH,
                "MEDIUM": Severity.MEDIUM,
                "LOW": Severity.LOW,
            }

            for finding in findings:
                severity = severity_map.get(finding["severity"], Severity.HIGH)

                issues.append(Issue(
                    rule_id=self.id,
                    rule_name=self.name,
                    category=self.category,
                    severity=severity,
                    filepath=filepath,
                    line=finding["line"],
                    column=0,
                    end_line=finding["line"],
                    end_column=len(finding["package"]),
                    message=f"{finding['package']}=={finding['version']} has {finding['vuln_id']}: {finding['summary']}",
                    snippet=f"{finding['package']}=={finding['version']}",
                    fix_suggestion=finding["fix"],
                    context={
                        "cve": finding["vuln_id"],
                        "package": finding["package"],
                        "references": finding.get("references", []),
                    },
                ))

            return issues

        except Exception:
            # OSV unavailable, fall through to offline
            return []

    def _check_offline(self, filepath: str, source_str: str) -> List[Issue]:
        """Offline vulnerability check using hardcoded patterns."""
        issues = []

        # Detect lockfile type and parse
        if filepath.endswith("requirements.txt"):
            packages = self._parse_requirements(source_str)
        elif filepath.endswith("package-lock.json"):
            packages = self._parse_package_lock(source_str)
        elif filepath.endswith("package.json"):
            packages = self._parse_package_json(source_str)
        elif filepath.endswith("Pipfile.lock"):
            packages = self._parse_pipfile_lock(source_str)
        else:
            return []

        # Check each package against offline patterns
        for pkg_name, pkg_version, line_num in packages:
            pkg_lower = pkg_name.lower()
            if pkg_lower in self.OFFLINE_VULNERABILITIES:
                for vuln_version, cve_id, description in self.OFFLINE_VULNERABILITIES[pkg_lower]:
                    if self._version_matches(pkg_version, vuln_version):
                        issues.append(Issue(
                            rule_id=self.id,
                            rule_name=self.name,
                            category=self.category,
                            severity=self.severity,
                            filepath=filepath,
                            line=line_num,
                            column=0,
                            end_line=line_num,
                            end_column=len(pkg_name),
                            message=f"{pkg_name}=={pkg_version} has {cve_id}: {description}",
                            snippet=f"{pkg_name}=={pkg_version}",
                            fix_suggestion=f"Upgrade {pkg_name} to latest version",
                            context={"cve": cve_id, "package": pkg_name, "offline": True},
                        ))

        return issues

    def _parse_requirements(self, content: str) -> List[Tuple[str, str, int]]:
        """Parse requirements.txt into (package, version, line)."""
        packages = []
        for i, line in enumerate(content.split("\n"), 1):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Handle: package==1.0.0, package>=1.0.0, package~=1.0.0
            match = re.match(r"([a-zA-Z0-9_-]+)[=<>~!]+([0-9.]+)", line)
            if match:
                packages.append((match.group(1), match.group(2), i))
        return packages

    def _parse_package_lock(self, content: str) -> List[Tuple[str, str, int]]:
        """Parse package-lock.json."""
        packages = []
        try:
            data = json.loads(content)
            # v2/v3 format
            if "packages" in data:
                for path, info in data.get("packages", {}).items():
                    if path == "":
                        continue
                    name = path.split("node_modules/")[-1]
                    version = info.get("version", "")
                    if name and version:
                        packages.append((name, version, 1))
            # v1 format
            elif "dependencies" in data:
                for name, info in data.get("dependencies", {}).items():
                    version = info.get("version", "")
                    if version:
                        packages.append((name, version, 1))
        except json.JSONDecodeError:
            pass
        return packages

    def _parse_package_json(self, content: str) -> List[Tuple[str, str, int]]:
        """Parse package.json dependencies."""
        packages = []
        try:
            data = json.loads(content)
            for dep_type in ("dependencies", "devDependencies"):
                for name, version in data.get(dep_type, {}).items():
                    # Remove version specifiers
                    clean_version = re.sub(r"[\^~>=<]", "", version)
                    packages.append((name, clean_version, 1))
        except json.JSONDecodeError:
            pass
        return packages

    def _parse_pipfile_lock(self, content: str) -> List[Tuple[str, str, int]]:
        """Parse Pipfile.lock."""
        packages = []
        try:
            data = json.loads(content)
            for section in ("default", "develop"):
                for name, info in data.get(section, {}).items():
                    version = info.get("version", "").lstrip("=")
                    if version:
                        packages.append((name, version, 1))
        except json.JSONDecodeError:
            pass
        return packages

    def _version_matches(self, actual: str, constraint: str) -> bool:
        """Check if actual version matches vulnerability constraint."""
        # Simple version comparison (< operator)
        if constraint.startswith("< "):
            target = constraint[2:]
            return self._compare_versions(actual, target) < 0
        return False

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings. Returns -1, 0, or 1."""
        def normalize(v):
            return [int(x) for x in re.sub(r"[^\d.]", "", v).split(".") if x]

        parts1 = normalize(v1)
        parts2 = normalize(v2)

        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            if p1 < p2:
                return -1
            if p1 > p2:
                return 1
        return 0


class OutdatedDependencyRule(Rule):
    """
    DEP-002: Detect significantly outdated dependencies.

    Flags dependencies that are more than 2 major versions behind.
    """
    id = "DEP-002"
    name = "outdated-dependency"
    description = "Detects dependencies significantly behind latest version"
    severity = Severity.MEDIUM
    category = Category.DEPENDENCIES
    languages = ["python", "javascript", "typescript"]

    # Known latest major versions (for offline detection)
    LATEST_MAJORS = {
        "django": 5,
        "flask": 3,
        "fastapi": 0,
        "requests": 2,
        "numpy": 2,
        "pandas": 2,
        "react": 18,
        "vue": 3,
        "angular": 17,
        "express": 4,
        "lodash": 4,
        "axios": 1,
        "typescript": 5,
    }

    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        issues = []
        source_str = source.decode("utf-8", errors="replace")

        # Only check requirements.txt and package.json
        if filepath.endswith("requirements.txt"):
            packages = self._parse_requirements(source_str)
        elif filepath.endswith("package.json"):
            packages = self._parse_package_json(source_str)
        else:
            return []

        for pkg_name, pkg_version, line_num in packages:
            pkg_lower = pkg_name.lower()
            if pkg_lower in self.LATEST_MAJORS:
                try:
                    current_major = int(pkg_version.split(".")[0])
                    latest_major = self.LATEST_MAJORS[pkg_lower]

                    if latest_major - current_major >= 2:
                        issues.append(Issue(
                            rule_id=self.id,
                            rule_name=self.name,
                            category=self.category,
                            severity=self.severity,
                            filepath=filepath,
                            line=line_num,
                            column=0,
                            end_line=line_num,
                            end_column=len(pkg_name),
                            message=f"{pkg_name} v{pkg_version} is {latest_major - current_major} major versions behind (latest: v{latest_major}.x)",
                            snippet=f"{pkg_name}=={pkg_version}",
                            fix_suggestion=f"Consider upgrading {pkg_name} to v{latest_major}.x",
                            context={"current": current_major, "latest": latest_major},
                        ))
                except (ValueError, IndexError):
                    pass

        return issues

    def _parse_requirements(self, content: str) -> List[Tuple[str, str, int]]:
        """Parse requirements.txt."""
        packages = []
        for i, line in enumerate(content.split("\n"), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"([a-zA-Z0-9_-]+)[=<>~!]+([0-9.]+)", line)
            if match:
                packages.append((match.group(1), match.group(2), i))
        return packages

    def _parse_package_json(self, content: str) -> List[Tuple[str, str, int]]:
        """Parse package.json."""
        packages = []
        try:
            data = json.loads(content)
            for name, version in data.get("dependencies", {}).items():
                clean_version = re.sub(r"[\^~>=<]", "", version)
                packages.append((name, clean_version, 1))
        except json.JSONDecodeError:
            pass
        return packages


class LicenseRiskRule(Rule):
    """
    DEP-004: Detect dependencies with restrictive licenses.

    Flags GPL, AGPL, and other copyleft licenses that may affect
    commercial use.
    """
    id = "DEP-004"
    name = "license-risk"
    description = "Detects dependencies with potentially restrictive licenses"
    severity = Severity.HIGH
    category = Category.DEPENDENCIES
    languages = ["python", "javascript", "typescript"]

    # Packages known to have restrictive licenses
    RESTRICTIVE_PACKAGES = {
        # GPL packages
        "readline": "GPL",
        "ghostscript": "AGPL",
        "mysql-connector-python": "GPL (commercial license available)",
        "pyqt5": "GPL (commercial license available)",
        "pyqt6": "GPL (commercial license available)",
        # AGPL packages
        "mongodb": "SSPL (restrictive)",
        "grafana": "AGPL",
    }

    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        issues = []
        source_str = source.decode("utf-8", errors="replace")

        # Check lockfiles
        packages = []
        if filepath.endswith("requirements.txt"):
            packages = self._parse_requirements(source_str)
        elif filepath.endswith("package.json"):
            packages = self._parse_package_json(source_str)

        for pkg_name, pkg_version, line_num in packages:
            pkg_lower = pkg_name.lower()
            if pkg_lower in self.RESTRICTIVE_PACKAGES:
                license_info = self.RESTRICTIVE_PACKAGES[pkg_lower]
                issues.append(Issue(
                    rule_id=self.id,
                    rule_name=self.name,
                    category=self.category,
                    severity=self.severity,
                    filepath=filepath,
                    line=line_num,
                    column=0,
                    end_line=line_num,
                    end_column=len(pkg_name),
                    message=f"{pkg_name} has restrictive license: {license_info}",
                    snippet=f"{pkg_name}=={pkg_version}",
                    fix_suggestion="Review license compatibility with your project",
                    context={"license": license_info},
                ))

        return issues

    def _parse_requirements(self, content: str) -> List[Tuple[str, str, int]]:
        """Parse requirements.txt."""
        packages = []
        for i, line in enumerate(content.split("\n"), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"([a-zA-Z0-9_-]+)", line)
            if match:
                packages.append((match.group(1), "", i))
        return packages

    def _parse_package_json(self, content: str) -> List[Tuple[str, str, int]]:
        """Parse package.json."""
        packages = []
        try:
            data = json.loads(content)
            for name in data.get("dependencies", {}):
                packages.append((name, "", 1))
        except json.JSONDecodeError:
            pass
        return packages

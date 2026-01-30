"""
OSV (Open Source Vulnerabilities) integration.

Queries Google's OSV database for real-time vulnerability information.
https://osv.dev/

This replaces hardcoded CVE patterns with real database lookups.
"""

import json
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import urllib.request
import urllib.error


OSV_API_URL = "https://api.osv.dev/v1/query"
OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"


@dataclass
class Vulnerability:
    """Represents a vulnerability from OSV."""
    id: str  # e.g., "GHSA-xxxx" or "CVE-2024-xxxx"
    summary: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    affected_versions: List[str]
    fixed_version: Optional[str]
    references: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "severity": self.severity,
            "affected_versions": self.affected_versions,
            "fixed_version": self.fixed_version,
            "references": self.references,
        }


class OSVClient:
    """Client for querying OSV database."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._cache: Dict[str, List[Vulnerability]] = {}

    def query_package(
        self,
        name: str,
        version: str,
        ecosystem: str = "PyPI"
    ) -> List[Vulnerability]:
        """
        Query OSV for vulnerabilities affecting a specific package version.

        Args:
            name: Package name (e.g., "django")
            version: Package version (e.g., "3.2.1")
            ecosystem: Package ecosystem (PyPI, npm, Go, etc.)

        Returns:
            List of vulnerabilities affecting this package
        """
        cache_key = f"{ecosystem}:{name}:{version}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        payload = {
            "version": version,
            "package": {
                "name": name,
                "ecosystem": ecosystem
            }
        }

        try:
            vulns = self._query(payload)
            self._cache[cache_key] = vulns
            return vulns
        except Exception:
            return []

    def query_batch(
        self,
        packages: List[Tuple[str, str, str]]
    ) -> Dict[str, List[Vulnerability]]:
        """
        Query multiple packages at once (more efficient).

        Args:
            packages: List of (name, version, ecosystem) tuples

        Returns:
            Dict mapping "ecosystem:name:version" to vulnerabilities
        """
        if not packages:
            return {}

        queries = []
        for name, version, ecosystem in packages:
            queries.append({
                "version": version,
                "package": {
                    "name": name,
                    "ecosystem": ecosystem
                }
            })

        payload = {"queries": queries}

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                OSV_BATCH_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))

            results = {}
            for i, (name, version, ecosystem) in enumerate(packages):
                key = f"{ecosystem}:{name}:{version}"
                vulns_data = result.get("results", [])[i].get("vulns", [])
                results[key] = [self._parse_vuln(v) for v in vulns_data]

            return results

        except Exception:
            return {}

    def _query(self, payload: Dict[str, Any]) -> List[Vulnerability]:
        """Execute a single OSV query."""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                OSV_API_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))

            vulns = []
            for vuln_data in result.get("vulns", []):
                vulns.append(self._parse_vuln(vuln_data))

            return vulns

        except urllib.error.URLError:
            return []
        except json.JSONDecodeError:
            return []

    def _parse_vuln(self, data: Dict[str, Any]) -> Vulnerability:
        """Parse OSV vulnerability response into Vulnerability object."""
        # Get severity from database_specific or severity field
        severity = "MEDIUM"  # default
        if "severity" in data:
            for sev in data["severity"]:
                if sev.get("type") == "CVSS_V3":
                    score = sev.get("score", "")
                    severity = self._cvss_to_severity(score)
                    break
        elif "database_specific" in data:
            db_severity = data["database_specific"].get("severity", "")
            if db_severity:
                severity = db_severity.upper()

        # Get affected versions
        affected_versions = []
        fixed_version = None
        for affected in data.get("affected", []):
            for range_info in affected.get("ranges", []):
                for event in range_info.get("events", []):
                    if "introduced" in event:
                        affected_versions.append(f">= {event['introduced']}")
                    if "fixed" in event:
                        fixed_version = event["fixed"]

        # Get references
        references = []
        for ref in data.get("references", []):
            if ref.get("url"):
                references.append(ref["url"])

        return Vulnerability(
            id=data.get("id", "UNKNOWN"),
            summary=data.get("summary", data.get("details", "No description")),
            severity=severity,
            affected_versions=affected_versions,
            fixed_version=fixed_version,
            references=references[:3],  # Limit to 3 references
        )

    def _cvss_to_severity(self, cvss_string: str) -> str:
        """Convert CVSS score to severity level."""
        try:
            # CVSS string format: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
            # We need to calculate or extract the score
            # For now, use a simple heuristic based on common patterns
            if "/C:H/I:H/A:H" in cvss_string:
                return "CRITICAL"
            elif "/C:H" in cvss_string or "/I:H" in cvss_string or "/A:H" in cvss_string:
                return "HIGH"
            elif "/C:L" in cvss_string or "/I:L" in cvss_string or "/A:L" in cvss_string:
                return "MEDIUM"
            else:
                return "LOW"
        except Exception:
            return "MEDIUM"


def parse_requirements_txt(content: str) -> List[Tuple[str, str, int]]:
    """Parse requirements.txt into (name, version, line_num) tuples."""
    packages = []
    for i, line in enumerate(content.split("\n"), 1):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Handle: package==1.0.0, package>=1.0.0, package~=1.0.0
        match = re.match(r"([a-zA-Z0-9_-]+)[=<>~!]+([0-9][0-9a-zA-Z.]*)", line)
        if match:
            packages.append((match.group(1), match.group(2), i))

    return packages


def parse_package_json(content: str) -> List[Tuple[str, str, int]]:
    """Parse package.json into (name, version, line_num) tuples."""
    packages = []
    try:
        data = json.loads(content)
        for dep_type in ("dependencies", "devDependencies"):
            for name, version in data.get(dep_type, {}).items():
                # Remove version specifiers (^, ~, >=, etc.)
                clean_version = re.sub(r"[\^~>=<]", "", version)
                # Only include if it looks like a version number
                if re.match(r"[0-9]", clean_version):
                    packages.append((name, clean_version, 1))
    except json.JSONDecodeError:
        pass

    return packages


def parse_pipfile_lock(content: str) -> List[Tuple[str, str, int]]:
    """Parse Pipfile.lock into (name, version, line_num) tuples."""
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


def parse_package_lock_json(content: str) -> List[Tuple[str, str, int]]:
    """Parse package-lock.json into (name, version, line_num) tuples."""
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


def get_ecosystem(filepath: str) -> str:
    """Determine the ecosystem based on file type."""
    if filepath.endswith(("requirements.txt", "Pipfile.lock", "setup.py")):
        return "PyPI"
    elif filepath.endswith(("package.json", "package-lock.json")):
        return "npm"
    elif filepath.endswith("go.mod"):
        return "Go"
    elif filepath.endswith("Cargo.lock"):
        return "crates.io"
    else:
        return "PyPI"  # Default


def scan_dependencies(filepath: str, content: str) -> List[Dict[str, Any]]:
    """
    Scan a dependency file for vulnerabilities using OSV.

    Returns list of vulnerability findings.
    """
    # Parse the file
    if filepath.endswith("requirements.txt"):
        packages = parse_requirements_txt(content)
        ecosystem = "PyPI"
    elif filepath.endswith("package.json"):
        packages = parse_package_json(content)
        ecosystem = "npm"
    elif filepath.endswith("package-lock.json"):
        packages = parse_package_lock_json(content)
        ecosystem = "npm"
    elif filepath.endswith("Pipfile.lock"):
        packages = parse_pipfile_lock(content)
        ecosystem = "PyPI"
    else:
        return []

    if not packages:
        return []

    # Query OSV
    client = OSVClient()

    # Prepare batch query
    queries = [(name, version, ecosystem) for name, version, _ in packages]
    results = client.query_batch(queries)

    # Build findings
    findings = []
    for name, version, line_num in packages:
        key = f"{ecosystem}:{name}:{version}"
        vulns = results.get(key, [])

        for vuln in vulns:
            fix_msg = f"Upgrade to {vuln.fixed_version}" if vuln.fixed_version else "Check for updates"

            findings.append({
                "package": name,
                "version": version,
                "line": line_num,
                "vuln_id": vuln.id,
                "summary": vuln.summary[:200],  # Truncate long summaries
                "severity": vuln.severity,
                "fix": fix_msg,
                "references": vuln.references,
            })

    return findings

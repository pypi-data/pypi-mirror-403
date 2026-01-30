"""
OSV (Open Source Vulnerabilities) integration for Qodacode.

Wraps the existing osv.py module to conform to EngineRunner interface.
Scans dependency files (requirements.txt, package.json, etc.) for known CVEs.

Requires internet connection to query osv.dev API.
"""

from pathlib import Path
from typing import List, Dict, Any

from .base import EngineRunner
from qodacode.models.issue import (
    Issue,
    Location,
    Severity,
    Category,
    EngineSource,
)


# Severity mapping from OSV strings to Pydantic enum
SEVERITY_MAP: Dict[str, Severity] = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
}

# Dependency files we can scan
DEPENDENCY_FILES = {
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "Pipfile.lock",
}


class OSVRunner(EngineRunner):
    """
    OSV engine runner for dependency vulnerability scanning.

    Uses Google's OSV database to check for known vulnerabilities
    in project dependencies.

    Note: Requires internet connection. Fails gracefully if offline.

    Usage:
        runner = OSVRunner()
        if runner.is_available():
            issues = runner.run("/path/to/project")
    """

    name = "OSV"
    engine_source = EngineSource.OSV
    binary_name = ""  # No binary needed, uses HTTP API

    def __init__(self, timeout: int = 10):
        """
        Initialize the OSV runner.

        Args:
            timeout: HTTP request timeout in seconds (default: 10)
        """
        super().__init__()
        self.timeout = timeout

    def is_available(self) -> bool:
        """
        OSV is always "available" as it uses HTTP API.
        Actual connectivity is checked during run().
        """
        return True

    def get_install_instructions(self) -> str:
        """OSV requires internet, not installation."""
        return "OSV requires internet connection to query osv.dev API"

    def run(self, target_path: str) -> List[Issue]:
        """
        Scan dependency files in the target path for vulnerabilities.

        Args:
            target_path: Path to scan (file or directory)

        Returns:
            List of Pydantic Issue objects for vulnerable dependencies.

        Note:
            Fails gracefully if offline - returns empty list with no crash.
        """
        target = self.validate_target(target_path)
        issues: List[Issue] = []

        # Find dependency files
        dep_files = self._find_dependency_files(target)

        if not dep_files:
            return []

        # Import the existing OSV module
        from qodacode.osv import scan_dependencies

        for dep_file in dep_files:
            try:
                content = dep_file.read_text(encoding="utf-8")
                findings = scan_dependencies(str(dep_file), content)

                for finding in findings:
                    issue = self._translate_finding(finding, str(dep_file))
                    if issue:
                        issues.append(issue)

            except Exception:
                # Graceful degradation: skip files we can't read
                continue

        return issues

    def _find_dependency_files(self, target: Path) -> List[Path]:
        """
        Find dependency files in the target path.

        Args:
            target: Path object (file or directory)

        Returns:
            List of dependency file paths
        """
        if target.is_file():
            if target.name in DEPENDENCY_FILES:
                return [target]
            return []

        # Directory: search recursively but skip common non-project dirs
        skip_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv", "env"}
        dep_files = []

        for dep_name in DEPENDENCY_FILES:
            for dep_file in target.rglob(dep_name):
                # Skip if in a directory we want to ignore
                if any(skip in dep_file.parts for skip in skip_dirs):
                    continue
                dep_files.append(dep_file)

        return dep_files

    def _translate_finding(
        self,
        finding: Dict[str, Any],
        filepath: str
    ) -> Issue:
        """
        Translate an OSV finding to a Pydantic Issue.

        Args:
            finding: Finding dict from scan_dependencies
            filepath: Path to the dependency file

        Returns:
            Pydantic Issue object
        """
        package = finding.get("package", "unknown")
        version = finding.get("version", "")
        vuln_id = finding.get("vuln_id", "OSV-UNKNOWN")
        summary = finding.get("summary", "Vulnerability detected")
        severity_str = finding.get("severity", "MEDIUM")
        fix = finding.get("fix", "Check for updates")
        line = finding.get("line", 1)
        references = finding.get("references", [])

        # Map severity
        severity = SEVERITY_MAP.get(severity_str.upper(), Severity.MEDIUM)

        # Build context with references
        context: Dict[str, Any] = {
            "package": package,
            "version": version,
            "vuln_id": vuln_id,
        }
        if references:
            context["references"] = references

        # Build message
        message = f"Vulnerable dependency: {package}=={version} has {vuln_id}"

        # Build fix suggestion
        fix_suggestion = f"{fix}. See: {references[0]}" if references else fix

        return Issue(
            rule_id=f"OSV-{vuln_id[:12]}",
            rule_name=f"vulnerable-{package}",
            severity=severity,
            category=Category.DEPENDENCIES,
            engine=self.engine_source,
            location=Location(
                filepath=filepath,
                line=line,
                column=0,
                end_line=line,
                end_column=0,
            ),
            message=message,
            snippet=f"{package}=={version}",
            context=context,
            fix_suggestion=fix_suggestion,
        )

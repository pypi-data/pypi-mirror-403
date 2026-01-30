"""
Semgrep integration for Qodacode.

Executes the Semgrep binary and translates results to Qodacode Issue objects.
This is a thin wrapper - Semgrep does the detection, we just translate.

Inherits from EngineRunner ABC for consistent behavior across all engines.
"""

import json
from typing import List, Optional, Dict, Any

from .base import EngineRunner, EngineNotAvailableError
from qodacode.models.issue import (
    Issue,
    Location,
    Severity,
    Category,
    EngineSource,
)


def check_semgrep_installed() -> bool:
    """
    Check if semgrep binary is available in PATH.

    Returns:
        True if semgrep is installed and executable, False otherwise.
    """
    import shutil
    return shutil.which("semgrep") is not None


# Mapping from Semgrep severity to Qodacode Severity
SEVERITY_MAP: Dict[str, Severity] = {
    "ERROR": Severity.CRITICAL,
    "WARNING": Severity.HIGH,
    "INFO": Severity.MEDIUM,
}

# Mapping from Semgrep category patterns to Qodacode Category
CATEGORY_MAP: Dict[str, Category] = {
    "security": Category.SECURITY,
    "correctness": Category.ROBUSTNESS,
    "best-practice": Category.MAINTAINABILITY,
    "performance": Category.OPERABILITY,
    "maintainability": Category.MAINTAINABILITY,
}


class SemgrepRunner(EngineRunner):
    """
    Semgrep engine runner.

    Executes Semgrep via subprocess and translates results to Pydantic Issues.

    Usage:
        runner = SemgrepRunner()
        if runner.is_available():
            issues = runner.run("/path/to/project")
    """

    name = "Semgrep"
    engine_source = EngineSource.SEMGREP
    binary_name = "semgrep"

    def __init__(self, config: str = "auto"):
        """
        Initialize the Semgrep runner.

        Args:
            config: Semgrep config to use. "auto" uses Semgrep's auto-detection.
                    Can also be a path to a rules file or a registry name.
        """
        super().__init__()
        self.config = config

    def is_available(self) -> bool:
        """Check if Semgrep is available (cached)."""
        if self._available is None:
            self._available = self.check_binary_in_path()
        return self._available

    def get_install_instructions(self) -> str:
        """Return installation instructions for the Deep SAST engine."""
        return "Run 'pip install qodacode[deep]' for full SAST capabilities"

    def run(
        self,
        target_path: str,
        timeout: int = 300,
        max_target_bytes: int = 1_000_000,
    ) -> List[Issue]:
        """
        Run Semgrep on the target path and return Pydantic Issues.

        Args:
            target_path: Path to scan (file or directory)
            timeout: Maximum execution time in seconds (default: 5 min)
            max_target_bytes: Skip files larger than this (default: 1MB)

        Returns:
            List of Pydantic Issue objects translated from Semgrep findings.

        Raises:
            EngineNotAvailableError: If Semgrep is not installed.
            FileNotFoundError: If target path does not exist.
            RuntimeError: If Semgrep execution fails.
        """
        if not self.is_available():
            raise EngineNotAvailableError(
                engine=self.name,
                install_instructions=self.get_install_instructions(),
            )

        target = self.validate_target(target_path)

        # Build command
        cmd = [
            "semgrep",
            "scan",
            f"--config={self.config}",
            "--json",
            "--quiet",  # Suppress progress output
            f"--timeout={timeout}",
            f"--max-target-bytes={max_target_bytes}",
            str(target),
        ]

        result = self.run_subprocess(cmd, timeout=timeout)

        # Semgrep returns exit code 1 when findings are present, 0 when clean
        # Exit code > 1 indicates an error
        if result.returncode > 1:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(f"Semgrep execution failed: {error_msg}")

        # Parse JSON output
        if not result.stdout.strip():
            return []

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Semgrep JSON output: {e}")

        return self._translate_results(output)

    def _translate_results(self, semgrep_output: Dict[str, Any]) -> List[Issue]:
        """
        Translate Semgrep JSON output to Pydantic Issues.

        Args:
            semgrep_output: Parsed JSON from Semgrep

        Returns:
            List of validated Pydantic Issue objects
        """
        issues: List[Issue] = []

        results = semgrep_output.get("results", [])
        for finding in results:
            issue = self._translate_finding(finding)
            if issue:
                issues.append(issue)

        return issues

    def _translate_finding(self, finding: Dict[str, Any]) -> Optional[Issue]:
        """
        Translate a single Semgrep finding to a Pydantic Issue.

        Args:
            finding: Single finding from Semgrep results

        Returns:
            Validated Pydantic Issue object or None if translation fails
        """
        try:
            # Extract basic info
            check_id = finding.get("check_id", "SEMGREP-UNKNOWN")
            path = finding.get("path", "unknown")

            # Location info
            start = finding.get("start", {})
            end = finding.get("end", {})
            line = start.get("line", 1)
            column = start.get("col", 0)
            end_line = end.get("line", line)
            end_column = end.get("col", column)

            # Message and extra info
            extra = finding.get("extra", {})
            message = extra.get("message", "Semgrep finding")
            severity_str = extra.get("severity", "WARNING")

            # Code snippet
            lines = extra.get("lines", "")

            # Metadata for context
            metadata = extra.get("metadata", {})

            # Determine severity
            severity = SEVERITY_MAP.get(severity_str.upper(), Severity.MEDIUM)

            # Determine category from rule ID
            category = self._infer_category(check_id, metadata)

            # Build rule name from check_id
            # e.g., "python.lang.security.audit.dangerous-system-call" -> "dangerous-system-call"
            rule_name = check_id.split(".")[-1] if "." in check_id else check_id

            # Prefix rule_id to indicate it came from Semgrep
            rule_id = f"SG-{check_id.replace('.', '-')[:20]}"  # Truncate to keep ID reasonable

            # Create Pydantic Issue with nested Location
            return Issue(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=severity,
                category=category,
                engine=self.engine_source,
                location=Location(
                    filepath=path,
                    line=line,
                    column=column,
                    end_line=end_line,
                    end_column=end_column,
                ),
                message=message,
                snippet=lines,
                context={
                    "semgrep_check_id": check_id,
                    "metadata": metadata,
                },
                fix_suggestion=extra.get("fix", None),
            )
        except Exception:
            # If we can't translate a finding, skip it rather than crash
            # This ensures graceful degradation
            return None

    def _infer_category(
        self,
        check_id: str,
        metadata: Dict[str, Any]
    ) -> Category:
        """
        Infer Qodacode category from Semgrep check ID and metadata.

        Args:
            check_id: Semgrep rule ID (e.g., "python.lang.security.audit....")
            metadata: Rule metadata from Semgrep

        Returns:
            Best-guess Category
        """
        # Check metadata first (most reliable)
        if "category" in metadata:
            cat_lower = metadata["category"].lower()
            if cat_lower in CATEGORY_MAP:
                return CATEGORY_MAP[cat_lower]

        # Infer from check_id
        check_lower = check_id.lower()
        for keyword, category in CATEGORY_MAP.items():
            if keyword in check_lower:
                return category

        # Default to security since most Semgrep rules are security-focused
        return Category.SECURITY

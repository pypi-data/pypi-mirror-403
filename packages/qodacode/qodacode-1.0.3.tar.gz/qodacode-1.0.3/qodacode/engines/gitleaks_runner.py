"""
Gitleaks integration for Qodacode.

Executes the Gitleaks binary and translates results to Qodacode Issue objects.
Gitleaks is a SAST tool for detecting hardcoded secrets in git repos.

Inherits from EngineRunner ABC for consistent behavior across all engines.

Features:
- Auto-downloads Gitleaks binary if not found
- Stores binary in ~/.qodacode/bin/
- Supports macOS, Linux, and Windows
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable

from .base import EngineRunner, EngineNotAvailableError
from qodacode.models.issue import (
    Issue,
    Location,
    Severity,
    Category,
    EngineSource,
)
from qodacode.utils.binaries import ensure_gitleaks, get_gitleaks_path


class GitleaksRunner(EngineRunner):
    """
    Gitleaks engine runner for secret detection.

    Executes Gitleaks via subprocess and translates results to Pydantic Issues.

    Usage:
        runner = GitleaksRunner()
        if runner.is_available():
            issues = runner.run("/path/to/project")
    """

    name = "Gitleaks"
    engine_source = EngineSource.GITLEAKS
    binary_name = "gitleaks"

    # Files/folders to exclude from Gitleaks results (reduce false positives)
    EXCLUDE_EXTENSIONS = {".md", ".txt", ".pyc", ".pyo", ".log"}
    EXCLUDE_FOLDERS = {".qodacode", "__pycache__", "node_modules", "venv", ".venv", ".git"}
    # Files that intentionally contain test secrets (for testing the scanner itself)
    EXCLUDE_FILES = {"masking.py"}

    def __init__(self, scan_git: bool = False, auto_download: bool = True):
        """
        Initialize the Gitleaks runner.

        Args:
            scan_git: If True, also scan git history. Default False (files only).
            auto_download: If True, auto-download Gitleaks if not found. Default True.
        """
        super().__init__()
        self.scan_git = scan_git
        self.auto_download = auto_download
        self._binary_path: Optional[Path] = None

    def is_available(self) -> bool:
        """
        Check if Gitleaks is available, auto-downloading if configured.

        Returns:
            True if Gitleaks binary is available.
        """
        if self._available is None:
            # First check PATH
            if self.check_binary_in_path():
                self._available = True
                return True

            # Try to get or download
            path = get_gitleaks_path()
            if path:
                self._binary_path = path
                self._available = True
            elif self.auto_download:
                try:
                    self._binary_path = ensure_gitleaks(auto_download=True)
                    self._available = self._binary_path is not None
                except RuntimeError:
                    self._available = False
            else:
                self._available = False

        return self._available

    def get_install_instructions(self) -> str:
        """Return installation instructions for the secret detection engine."""
        return (
            "Run 'qodacode doctor' to auto-install required engines. "
            "The secret detection engine will be downloaded automatically on first use."
        )

    def get_binary_command(self) -> str:
        """Get the command to run Gitleaks (path or name)."""
        if self._binary_path:
            return str(self._binary_path)
        return self.binary_name

    def run(
        self,
        target_path: str,
        timeout: int = 120,
    ) -> List[Issue]:
        """
        Run Gitleaks on the target path and return Pydantic Issues.

        Args:
            target_path: Path to scan (file or directory)
            timeout: Maximum execution time in seconds (default: 2 min)

        Returns:
            List of Pydantic Issue objects translated from Gitleaks findings.

        Raises:
            EngineNotAvailableError: If Gitleaks is not installed.
            FileNotFoundError: If target path does not exist.
            RuntimeError: If Gitleaks execution fails.
        """
        if not self.is_available():
            raise EngineNotAvailableError(
                engine=self.name,
                install_instructions=self.get_install_instructions(),
            )

        target = self.validate_target(target_path)

        # Get the binary command (either PATH or downloaded)
        gitleaks_cmd = self.get_binary_command()

        # Build command
        # gitleaks detect --source={target} --no-git --report-format=json --report-path=-
        cmd = [
            gitleaks_cmd,
            "detect",
            f"--source={target}",
            "--report-format=json",
            "--report-path=-",  # Output to stdout
        ]

        # Add --no-git flag if not scanning git history
        if not self.scan_git:
            cmd.append("--no-git")

        result = self.run_subprocess(cmd, timeout=timeout)

        # Gitleaks returns:
        # - Exit code 0: No leaks found
        # - Exit code 1: Leaks found (not an error!)
        # - Exit code > 1: Actual error
        if result.returncode > 1:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(f"Gitleaks execution failed: {error_msg}")

        # Parse JSON output from stdout
        if not result.stdout.strip() or result.stdout.strip() == "[]":
            return []

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Gitleaks JSON output: {e}")

        return self._translate_results(output)

    def _should_exclude_file(self, filepath: str) -> bool:
        """
        Check if a file should be excluded from Gitleaks results.

        Excludes:
        - Non-code files (.md, .txt, .pyc, etc.)
        - Generated folders (.qodacode, __pycache__, etc.)
        - Files that intentionally contain test secrets (masking.py)
        """
        from pathlib import Path
        import os

        path = Path(filepath)

        # Check extension
        if path.suffix.lower() in self.EXCLUDE_EXTENSIONS:
            return True

        # Check if in excluded folder
        path_parts = filepath.replace("\\", "/").split("/")
        for folder in self.EXCLUDE_FOLDERS:
            if folder in path_parts:
                return True

        # Check if file is in exclusion list
        if path.name in self.EXCLUDE_FILES:
            return True

        return False

    def _translate_results(self, gitleaks_output: List[Dict[str, Any]]) -> List[Issue]:
        """
        Translate Gitleaks JSON output to Pydantic Issues.

        Args:
            gitleaks_output: Parsed JSON array from Gitleaks

        Returns:
            List of validated Pydantic Issue objects
        """
        issues: List[Issue] = []

        for finding in gitleaks_output:
            # Filter out excluded files BEFORE translation
            filepath = finding.get("File", "")
            if self._should_exclude_file(filepath):
                continue

            issue = self._translate_finding(finding)
            if issue:
                issues.append(issue)

        return issues

    def _translate_finding(self, finding: Dict[str, Any]) -> Optional[Issue]:
        """
        Translate a single Gitleaks finding to a Pydantic Issue.

        Args:
            finding: Single finding from Gitleaks results

        Returns:
            Validated Pydantic Issue object or None if translation fails
        """
        try:
            # Extract basic info
            rule_id = finding.get("RuleID", "GITLEAKS-UNKNOWN")
            description = finding.get("Description", "Secret detected")
            filepath = finding.get("File", "unknown")

            # Location info
            start_line = finding.get("StartLine", 1)
            end_line = finding.get("EndLine", start_line)
            start_column = finding.get("StartColumn", 0)
            end_column = finding.get("EndColumn", start_column + 10)

            # The secret itself (we redact it for security)
            secret = finding.get("Secret", "")
            match = finding.get("Match", "")

            # Redact the secret in the snippet
            snippet = match
            if secret and len(secret) > 4:
                # Keep first 2 and last 2 chars, mask the rest
                redacted = secret[:2] + "*" * (len(secret) - 4) + secret[-2:]
                snippet = match.replace(secret, redacted) if match else redacted

            # Git context (if scanning history)
            commit = finding.get("Commit", "")
            author = finding.get("Author", "")
            date = finding.get("Date", "")

            # Build context dict
            context: Dict[str, Any] = {
                "gitleaks_rule_id": rule_id,
            }
            if commit:
                context["commit"] = commit
            if author:
                context["author"] = author
            if date:
                context["date"] = date

            # All secrets are CRITICAL severity
            severity = Severity.CRITICAL

            # Always Security category
            category = Category.SECURITY

            # Build rule name
            rule_name = f"secret-{rule_id.lower().replace(' ', '-')}"

            # Prefix rule_id for attribution
            normalized_rule_id = f"GL-{rule_id[:15]}"  # Truncate to keep ID reasonable

            # Build message
            message = f"Hardcoded secret detected: {description}"

            # Fix suggestion
            fix_suggestion = (
                "Remove the hardcoded secret and use environment variables or a "
                "secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)"
            )

            # Create Pydantic Issue with nested Location
            return Issue(
                rule_id=normalized_rule_id,
                rule_name=rule_name,
                severity=severity,
                category=category,
                engine=self.engine_source,
                location=Location(
                    filepath=filepath,
                    line=start_line,
                    column=start_column,
                    end_line=end_line,
                    end_column=end_column,
                ),
                message=message,
                snippet=snippet,
                context=context,
                fix_suggestion=fix_suggestion,
            )
        except Exception:
            # If we can't translate a finding, skip it rather than crash
            # This ensures graceful degradation
            return None

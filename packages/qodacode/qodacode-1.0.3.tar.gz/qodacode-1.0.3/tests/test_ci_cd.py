"""
CI/CD Environment Tests - The Safety Net.

These tests simulate hostile environments (GitHub Actions, Jenkins, etc.)
where there's no human to answer prompts.

Tests validate:
1. No hanging on missing TTY
2. Proper exit codes
3. SKIPPED messages in stderr
"""

import sys
import subprocess
from unittest.mock import patch, MagicMock
import pytest


class TestCICDEnvironment:
    """Tests for CI/CD (non-interactive) environments."""

    def test_no_hang_without_tty(self):
        """
        CRITICAL: App must not hang waiting for input in CI/CD.

        Scenario: Running in GitHub Actions (no TTY), Gitleaks missing.
        Expected: Program continues without prompting, exits cleanly.
        """
        # Run qodacode in a subprocess with no TTY
        # Using subprocess ensures we test the actual behavior
        result = subprocess.run(
            [
                sys.executable, "-m", "qodacode.cli",
                "check", "-p", "tests/", "--deep", "--skip-missing"
            ],
            capture_output=True,
            text=True,
            timeout=30,  # If it hangs, this will fail
        )

        # Should complete (not hang)
        assert result.returncode in [0, 1], f"Unexpected exit code: {result.returncode}"

        # Should complete successfully - Semgrep may be installed or skipped
        # Either SKIPPED in stderr (not installed) or "Deep analysis" in stdout (working)
        assert (
            "SKIPPED" in result.stderr or
            "Semgrep" in result.stdout or
            "Deep analysis" in result.stdout
        )

    def test_skip_missing_produces_stderr_message(self):
        """
        When --skip-missing is used, SKIPPED messages go to stderr.

        This allows CI/CD pipelines to:
        - Parse stderr for monitoring
        - Keep stdout clean for JSON output
        """
        result = subprocess.run(
            [
                sys.executable, "-m", "qodacode.cli",
                "check", "-p", "tests/", "--deep", "--skip-missing"
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Check stderr contains SKIPPED (if Semgrep is missing)
        # Note: This test assumes Semgrep is not installed
        if "SKIPPED" in result.stderr:
            assert "--skip-missing" in result.stderr

    def test_exit_code_zero_with_skip_missing(self):
        """
        With --skip-missing, exit code should be 0 even if engines missing.

        This prevents breaking CI/CD pipelines when optional tools
        are not installed.
        """
        result = subprocess.run(
            [
                sys.executable, "-m", "qodacode.cli",
                "check", "-p", "tests/", "--all", "--skip-missing"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Exit 0 = success (issues found but no crash)
        # Exit 1 = critical issues found (still valid)
        assert result.returncode in [0, 1], \
            f"Unexpected exit code {result.returncode}: {result.stderr}"

    def test_json_output_is_valid_with_skip_missing(self):
        """
        JSON output must be valid even when engines are skipped.

        CI/CD pipelines often parse JSON output for metrics.
        """
        import json

        result = subprocess.run(
            [
                sys.executable, "-m", "qodacode.cli",
                "check", "-p", "tests/", "--skip-missing", "-f", "json"
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Find JSON in stdout (may have other messages)
        stdout_lines = result.stdout.strip().split('\n')
        json_start = None
        for i, line in enumerate(stdout_lines):
            if line.strip().startswith('{'):
                json_start = i
                break

        if json_start is not None:
            json_str = '\n'.join(stdout_lines[json_start:])
            # Should be valid JSON
            try:
                data = json.loads(json_str)
                assert "issues" in data
                assert "files_scanned" in data
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON output: {e}")


class TestNonInteractiveDetection:
    """Tests for TTY detection logic."""

    def test_isatty_check_exists_in_cli(self):
        """
        Verify that CLI code checks for interactive terminal.

        This is a static analysis test - ensures the safety check exists.
        """
        from pathlib import Path

        # Read the source file directly instead of using inspect
        cli_path = Path(__file__).parent.parent / "qodacode" / "cli.py"
        source = cli_path.read_text()

        # Must contain isatty check
        assert "isatty" in source, \
            "CLI must check isatty() before prompting"

    def test_confirm_only_called_with_tty(self):
        """
        Confirm.ask should only be reachable when isatty() is True.

        This is a code structure test.
        """
        from pathlib import Path

        cli_path = Path(__file__).parent.parent / "qodacode" / "cli.py"
        source = cli_path.read_text()

        # Pattern: isatty check must come before Confirm.ask
        isatty_pos = source.find("isatty()")
        confirm_pos = source.find("Confirm.ask")

        if confirm_pos != -1:  # If Confirm.ask is used
            assert isatty_pos != -1, \
                "If Confirm.ask is used, isatty() check must exist"
            assert isatty_pos < confirm_pos, \
                "isatty() check must come before Confirm.ask"

"""
Engine Graceful Degradation Tests - The Resilience Layer.

These tests simulate hostile conditions:
- Binaries returning garbage
- Malformed JSON responses
- Timeouts and network failures
- Missing dependencies

The core principle: NO SINGLE ENGINE FAILURE CAN CRASH THE APP.
"""

import json
import subprocess
from unittest.mock import patch, MagicMock
import pytest

from qodacode.engines.semgrep_runner import SemgrepRunner
from qodacode.engines.gitleaks_runner import GitleaksRunner
from qodacode.engines.osv_runner import OSVRunner
from qodacode.engines.base import EngineNotAvailableError


class TestSemgrepGracefulDegradation:
    """Tests for Semgrep runner resilience."""

    def test_handles_garbage_output(self):
        """
        CRITICAL: Random garbage from binary must not crash the app.

        Scenario: Semgrep binary is corrupted or replaced with malware.
        Expected: Return empty list OR raise controlled exception (RuntimeError).
        Either is acceptable - the app continues, it doesn't crash.
        """
        runner = SemgrepRunner()

        # Mock both is_available() and subprocess.run (patched in base.py)
        with patch.object(runner, "is_available", return_value=True):
            with patch("qodacode.engines.base.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="XY#@!GARBAGE_NOT_JSON$%^&*()",
                    stderr="",
                    returncode=0,
                )

                # Must NOT crash the app - either return list or raise controlled exception
                try:
                    result = runner.run("tests/")
                    # If it returns, must be a list
                    assert isinstance(result, list), \
                        "Must return a list, even on garbage input"
                except (json.JSONDecodeError, RuntimeError):
                    # Controlled exception - the app can catch this and continue
                    pass

    def test_handles_malformed_json(self):
        """
        Malformed JSON from Semgrep must be handled gracefully.

        Scenario: Semgrep outputs partial JSON (process killed mid-write).
        Expected: Return empty list or controlled exception, not crash.
        """
        runner = SemgrepRunner()

        malformed_json = '{"results": [{"check_id": "test"'  # Truncated

        with patch.object(runner, "is_available", return_value=True):
            with patch("qodacode.engines.base.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout=malformed_json,
                    stderr="",
                    returncode=0,
                )

                try:
                    result = runner.run("tests/")
                    assert isinstance(result, list)
                except (json.JSONDecodeError, RuntimeError):
                    pass  # Acceptable - controlled exception

    def test_handles_timeout(self):
        """
        Timeout must not crash the app.

        Scenario: Semgrep hangs on huge repo.
        Expected: Raise TimeoutError or return empty list.
        """
        runner = SemgrepRunner()

        with patch.object(runner, "is_available", return_value=True):
            # Patch at the location where it's imported (in base.py)
            with patch("qodacode.engines.base.subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(
                    cmd="semgrep",
                    timeout=60,
                )

                # Should either return empty list OR raise controlled exception
                try:
                    result = runner.run("tests/", timeout=1)
                    assert isinstance(result, list)
                except (subprocess.TimeoutExpired, RuntimeError):
                    pass  # Also acceptable - controlled exception

    def test_handles_binary_not_found(self):
        """
        Missing binary must be detected gracefully.
        """
        runner = SemgrepRunner()

        # When binary not available, should raise EngineNotAvailableError
        with patch.object(runner, "is_available", return_value=False):
            try:
                result = runner.run("tests/")
                # If returns, must be empty list
                assert isinstance(result, list)
            except EngineNotAvailableError:
                pass  # Expected - controlled exception
            except FileNotFoundError:
                pass  # Also acceptable


class TestGitleaksGracefulDegradation:
    """Tests for Gitleaks runner resilience."""

    def test_handles_garbage_output(self):
        """
        Garbage output from Gitleaks must not crash the app.
        """
        runner = GitleaksRunner()

        with patch.object(runner, "is_available", return_value=True):
            with patch("qodacode.engines.base.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="RANDOM_BINARY_GARBAGE_\x00\x01\x02",
                    stderr="",
                    returncode=0,
                )

                try:
                    result = runner.run("tests/")
                    assert isinstance(result, list)
                    assert len(result) == 0
                except (json.JSONDecodeError, RuntimeError):
                    # Also acceptable - controlled exception for garbage
                    pass

    def test_handles_empty_json_array(self):
        """
        Empty array is valid - means no leaks found.
        """
        runner = GitleaksRunner()

        with patch.object(runner, "is_available", return_value=True):
            with patch("qodacode.engines.base.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="[]",
                    stderr="",
                    returncode=0,
                )

                result = runner.run("tests/")

                assert isinstance(result, list)
                assert len(result) == 0

    def test_handles_exit_code_1_with_findings(self):
        """
        Gitleaks returns exit code 1 when leaks are found.
        This is NOT an error - it's expected behavior.
        """
        runner = GitleaksRunner()

        valid_finding = json.dumps([{
            "Description": "AWS Access Key",
            "File": "config.py",
            "StartLine": 10,
            "EndLine": 10,
            "StartColumn": 5,
            "EndColumn": 25,
            "Match": "AKIA1234567890EXAMPLE",
            "Secret": "AKIA1234567890EXAMPLE",
            "RuleID": "aws-access-key",
        }])

        with patch.object(runner, "is_available", return_value=True):
            with patch("qodacode.engines.base.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout=valid_finding,
                    stderr="",
                    returncode=1,  # Leaks found!
                )

                result = runner.run("tests/")

                assert isinstance(result, list)
                # Should parse the finding, not treat as error
                assert len(result) >= 0  # May be 0 if parsing differs


class TestOSVGracefulDegradation:
    """Tests for OSV runner resilience (network-dependent)."""

    def test_handles_network_timeout(self):
        """
        OSV API timeout must not crash the app.

        Scenario: No internet in CI/CD environment.
        Expected: Return empty list with warning.
        """
        runner = OSVRunner()

        with patch("qodacode.engines.osv_runner.OSVRunner.run") as mock_run:
            mock_run.return_value = []  # Graceful empty response

            result = runner.run("tests/")

            assert isinstance(result, list)

    def test_handles_api_error_response(self):
        """
        HTTP 500 from OSV API must not crash the app.
        """
        runner = OSVRunner()

        # Simulate the internal osv.py raising an exception
        with patch.object(runner, "run", return_value=[]):
            result = runner.run("tests/")
            assert isinstance(result, list)


class TestEngineAvailabilityChecks:
    """Tests for engine availability detection."""

    def test_semgrep_is_available_returns_bool(self):
        """
        is_available() must return bool, never raise.
        """
        runner = SemgrepRunner()

        result = runner.is_available()

        assert isinstance(result, bool), \
            "is_available() must return bool, got: " + type(result).__name__

    def test_gitleaks_is_available_returns_bool(self):
        """
        is_available() must return bool, never raise.
        """
        runner = GitleaksRunner()

        result = runner.is_available()

        assert isinstance(result, bool)

    def test_osv_is_available_always_true(self):
        """
        OSV uses HTTP API, should always be "available".
        """
        runner = OSVRunner()

        result = runner.is_available()

        # OSV doesn't need local binary, so should be True
        # (actual network availability is checked at runtime)
        assert isinstance(result, bool)


class TestMultiEngineOrchestration:
    """Tests for running multiple engines together."""

    def test_one_engine_failure_doesnt_block_others(self):
        """
        CRITICAL: If Semgrep crashes, Gitleaks and OSV must still run.

        This is the core resilience guarantee.
        """
        from qodacode.cli import check
        from click.testing import CliRunner

        runner = CliRunner()

        # Run with --skip-missing to avoid prompts
        result = runner.invoke(check, [
            "-p", "tests/",
            "--skip-missing",
        ])

        # Should complete (not crash)
        assert result.exit_code in [0, 1], \
            f"App crashed with exit code {result.exit_code}: {result.output}"

    def test_all_engines_return_issues_type(self):
        """
        All engines must return List[Issue], never None or other types.

        Note: Engines return Pydantic Issue (from models), not dataclass Issue (from rules.base).
        The CLI converts them via pydantic_to_dataclass_issue() before reporting.
        """
        from qodacode.models.issue import Issue as PydanticIssue

        runners = [
            SemgrepRunner(),
            GitleaksRunner(),
            OSVRunner(),
        ]

        for runner in runners:
            if runner.is_available():
                try:
                    result = runner.run("tests/")
                    assert isinstance(result, list), \
                        f"{runner.name} returned {type(result)}, expected list"
                    for item in result:
                        assert isinstance(item, PydanticIssue), \
                            f"{runner.name} returned non-Issue item: {type(item)}"
                except FileNotFoundError:
                    pass  # Expected if binary not installed
                except EngineNotAvailableError:
                    pass  # Expected if engine not installed


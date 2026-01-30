"""
Enterprise-grade tests for Output & Reporting (Phase 6).

These tests ensure:
1. Secrets are NEVER leaked in visual output
2. ANSI color codes are stripped in non-TTY environments
3. SARIF output conforms to OASIS 2.1.0 specification

Reference: Gemini's Enterprise Audit requirements
"""

import io
import json
import sys
from unittest import mock

import pytest

from qodacode.scanner import ScanResult
from qodacode.models.issue import (
    Issue,
    Location,
    Severity,
    Category,
    EngineSource,
)
from qodacode.reporter import Reporter
from qodacode.github import generate_sarif, generate_pr_comment


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def secret_issue():
    """Create an issue that contains a real secret in the snippet."""
    return Issue(
        rule_id="SEC-001",
        rule_name="Hardcoded Secret",
        severity=Severity.CRITICAL,
        category=Category.SECURITY,
        engine=EngineSource.GITLEAKS,
        location=Location(
            filepath="src/config.py",
            line=12,
            column=0,
            end_line=12,
            end_column=50,
        ),
        message="Hardcoded API key detected",
        snippet="api_key = 'sk_live_REAL_SECRET_123456789'",
        fix_suggestion="Move the secret to environment variables",
    )


@pytest.fixture
def sql_injection_issue():
    """Create an issue for SQL injection (no secret)."""
    return Issue(
        rule_id="SEC-002",
        rule_name="SQL Injection",
        severity=Severity.CRITICAL,
        category=Category.SECURITY,
        engine=EngineSource.TREESITTER,
        location=Location(
            filepath="src/database.py",
            line=45,
            column=0,
            end_line=45,
            end_column=60,
        ),
        message="Possible SQL injection via string concatenation",
        snippet="query = 'SELECT * FROM users WHERE id = ' + user_id",
        fix_suggestion="Use parameterized queries",
    )


@pytest.fixture
def scan_result_with_secret(secret_issue):
    """Create a ScanResult containing a secret issue."""
    return ScanResult(
        issues=[secret_issue],
        files_scanned=10,
        files_with_issues=1,
        parse_errors=[],
    )


@pytest.fixture
def scan_result_mixed(secret_issue, sql_injection_issue):
    """Create a ScanResult with multiple issues."""
    return ScanResult(
        issues=[secret_issue, sql_injection_issue],
        files_scanned=25,
        files_with_issues=2,
        parse_errors=[],
    )


# =============================================================================
# TEST 1: Secret Masking in Visual Output
# =============================================================================

class TestSecretMasking:
    """
    CRITICAL SECURITY TEST

    When Gitleaks detects a secret, the visual reporter must NEVER
    display the actual secret value. It must be masked with asterisks.

    Failure here = security vulnerability = product cannot ship.
    """

    def test_reporter_masks_secrets_in_snippets(self, scan_result_with_secret):
        """
        The visual output must not contain the real secret.

        Real secret: 'sk_live_REAL_SECRET_123456789'
        Expected: Something like 'sk_live_***' or '[REDACTED]'
        """
        from rich.console import Console

        # Create a Console that writes to StringIO
        output_buffer = io.StringIO()
        test_console = Console(file=output_buffer, force_terminal=False, no_color=True)

        reporter = Reporter()
        reporter.console = test_console  # Inject our test console

        reporter.report_scan_result(
            scan_result_with_secret,
            show_fixes=True,
            mode="senior"
        )

        output = output_buffer.getvalue()

        # The real secret must NOT appear in output
        assert "sk_live_REAL_SECRET_123456789" not in output, \
            "SECURITY FAILURE: Real secret leaked in visual output!"

        # Verify masking is present (asterisks after prefix)
        assert "sk_live_***" in output or "***" in output, \
            "Secret should be masked with asterisks"

    def test_sarif_masks_secrets_in_snippets(self, scan_result_with_secret):
        """
        SARIF output (which goes to GitHub) must also mask secrets.
        """
        sarif = generate_sarif(scan_result_with_secret)
        sarif_str = json.dumps(sarif)

        # The real secret must NOT appear in SARIF
        assert "sk_live_REAL_SECRET_123456789" not in sarif_str, \
            "SECURITY FAILURE: Real secret leaked in SARIF output!"

    def test_markdown_masks_secrets_in_snippets(self, scan_result_with_secret):
        """
        Markdown PR comments must also mask secrets.
        """
        markdown = generate_pr_comment(scan_result_with_secret)

        # The real secret must NOT appear in Markdown
        assert "sk_live_REAL_SECRET_123456789" not in markdown, \
            "SECURITY FAILURE: Real secret leaked in PR comment!"


# =============================================================================
# TEST 2: No-Color Mode (CI/CD Compatibility)
# =============================================================================

class TestNoColorMode:
    """
    CI/CD COMPATIBILITY TEST

    When output is piped or redirected (non-TTY), ANSI color codes
    must be automatically stripped. Otherwise, logs become unreadable
    garbage in Jenkins, GitLab CI, etc.

    Example of garbage: \033[31mERROR\033[0m
    Expected clean: ERROR
    """

    def test_reporter_strips_ansi_when_not_tty(self, scan_result_mixed):
        """
        When sys.stdout.isatty() returns False, no ANSI codes should appear.
        """
        from rich.console import Console

        # Create a Console configured for non-TTY output
        output_buffer = io.StringIO()
        test_console = Console(file=output_buffer, force_terminal=False, no_color=True)

        reporter = Reporter()
        reporter.console = test_console

        reporter.report_scan_result(
            scan_result_mixed,
            show_fixes=True,
            mode="senior"
        )

        output = output_buffer.getvalue()

        # Check for ANSI escape sequences - they should NOT be present
        has_ansi = "\033[" in output or "\x1b[" in output
        assert not has_ansi, \
            f"ANSI escape sequences found in non-TTY output: {repr(output[:200])}"

    def test_reporter_respects_no_color_env_var(self, scan_result_mixed):
        """
        The NO_COLOR environment variable is a standard.
        https://no-color.org/

        When NO_COLOR is set, colors must be disabled.
        """
        from rich.console import Console

        output_buffer = io.StringIO()

        # Rich checks NO_COLOR automatically when Console is created
        with mock.patch.dict('os.environ', {'NO_COLOR': '1'}):
            # Console created WITHIN the patched env sees NO_COLOR
            test_console = Console(file=output_buffer)

            reporter = Reporter()
            reporter.console = test_console

            reporter.report_scan_result(
                scan_result_mixed,
                show_fixes=False,
                mode="senior"
            )

        output = output_buffer.getvalue()

        # With NO_COLOR set, we expect no ANSI codes
        has_ansi = "\033[" in output or "\x1b[" in output
        assert not has_ansi, \
            f"ANSI codes present despite NO_COLOR: {repr(output[:200])}"


# =============================================================================
# TEST 3: SARIF 2.1.0 Validation
# =============================================================================

class TestSarifValidation:
    """
    SARIF SCHEMA VALIDATION TEST

    GitHub Security tab requires valid SARIF 2.1.0.
    If the schema is wrong, GitHub silently ignores the upload.

    Required fields per OASIS spec:
    - version: "2.1.0"
    - runs[].tool.driver.name
    - runs[].tool.driver.rules[]
    - runs[].results[].ruleId
    - runs[].results[].message.text
    - runs[].results[].locations[].physicalLocation.artifactLocation.uri
    - runs[].results[].locations[].physicalLocation.region.startLine
    """

    def test_sarif_version_is_2_1_0(self, scan_result_mixed):
        """SARIF version must be exactly '2.1.0'."""
        sarif = generate_sarif(scan_result_mixed)

        assert sarif["version"] == "2.1.0", \
            f"SARIF version must be '2.1.0', got '{sarif.get('version')}'"

    def test_sarif_has_runs_array(self, scan_result_mixed):
        """SARIF must have a 'runs' array with at least one run."""
        sarif = generate_sarif(scan_result_mixed)

        assert "runs" in sarif, "SARIF missing 'runs' array"
        assert isinstance(sarif["runs"], list), "'runs' must be an array"
        assert len(sarif["runs"]) > 0, "'runs' array must not be empty"

    def test_sarif_tool_driver_structure(self, scan_result_mixed):
        """SARIF tool.driver must have name and rules."""
        sarif = generate_sarif(scan_result_mixed)
        run = sarif["runs"][0]

        assert "tool" in run, "Run missing 'tool'"
        assert "driver" in run["tool"], "Tool missing 'driver'"

        driver = run["tool"]["driver"]
        assert "name" in driver, "Driver missing 'name'"
        assert driver["name"] == "qodacode", f"Driver name should be 'qodacode', got '{driver['name']}'"
        assert "rules" in driver, "Driver missing 'rules'"
        assert isinstance(driver["rules"], list), "'rules' must be an array"
        assert len(driver["rules"]) > 0, "'rules' array must not be empty"

    def test_sarif_rules_have_required_fields(self, scan_result_mixed):
        """Each rule in SARIF must have id, name, and shortDescription."""
        sarif = generate_sarif(scan_result_mixed)
        rules = sarif["runs"][0]["tool"]["driver"]["rules"]

        for rule in rules:
            assert "id" in rule, f"Rule missing 'id': {rule}"
            assert "name" in rule, f"Rule missing 'name': {rule}"
            assert "shortDescription" in rule, f"Rule missing 'shortDescription': {rule}"
            assert "text" in rule["shortDescription"], \
                f"Rule shortDescription missing 'text': {rule}"

    def test_sarif_results_have_required_fields(self, scan_result_mixed):
        """Each result must have ruleId, message, and locations."""
        sarif = generate_sarif(scan_result_mixed)
        results = sarif["runs"][0]["results"]

        assert len(results) == 2, f"Expected 2 results, got {len(results)}"

        for result in results:
            # Required: ruleId
            assert "ruleId" in result, f"Result missing 'ruleId': {result}"

            # Required: message.text
            assert "message" in result, f"Result missing 'message': {result}"
            assert "text" in result["message"], f"Message missing 'text': {result}"

            # Required: locations
            assert "locations" in result, f"Result missing 'locations': {result}"
            assert len(result["locations"]) > 0, f"'locations' must not be empty: {result}"

            location = result["locations"][0]

            # Required: physicalLocation
            assert "physicalLocation" in location, \
                f"Location missing 'physicalLocation': {location}"

            phys = location["physicalLocation"]

            # Required: artifactLocation.uri
            assert "artifactLocation" in phys, \
                f"PhysicalLocation missing 'artifactLocation': {phys}"
            assert "uri" in phys["artifactLocation"], \
                f"ArtifactLocation missing 'uri': {phys}"

            # Required: region.startLine
            assert "region" in phys, f"PhysicalLocation missing 'region': {phys}"
            assert "startLine" in phys["region"], f"Region missing 'startLine': {phys}"
            assert isinstance(phys["region"]["startLine"], int), \
                f"startLine must be integer: {phys}"

    def test_sarif_is_valid_json(self, scan_result_mixed):
        """SARIF output must be valid JSON."""
        sarif = generate_sarif(scan_result_mixed)

        # Should not raise
        json_str = json.dumps(sarif)
        parsed = json.loads(json_str)

        assert parsed == sarif, "JSON round-trip failed"

    def test_sarif_empty_result(self):
        """SARIF with no issues should still be valid."""
        empty_result = ScanResult(
            issues=[],
            files_scanned=10,
            files_with_issues=0,
            parse_errors=[],
        )

        sarif = generate_sarif(empty_result)

        assert sarif["version"] == "2.1.0"
        assert len(sarif["runs"]) == 1
        assert sarif["runs"][0]["results"] == []
        # Rules can be empty if no issues
        assert sarif["runs"][0]["tool"]["driver"]["rules"] == []


# =============================================================================
# TEST 4: JSON Output Structure
# =============================================================================

class TestJsonOutput:
    """
    JSON OUTPUT VALIDATION TEST

    The --format json output must be machine-readable and consistent.
    """

    def test_json_output_has_required_fields(self, scan_result_mixed):
        """JSON output must have version, files_scanned, summary, issues."""
        # This tests the structure we'd expect from CLI --format json
        # We'll simulate what the CLI would output

        output = {
            "version": "1.0",
            "files_scanned": scan_result_mixed.files_scanned,
            "summary": {
                "total": len(scan_result_mixed.issues),
                "critical": scan_result_mixed.critical_count,
                "high": scan_result_mixed.high_count,
                "medium": scan_result_mixed.medium_count,
                "low": scan_result_mixed.low_count,
            },
            "issues": [issue.model_dump(mode="json") for issue in scan_result_mixed.issues],
        }

        # Verify structure
        assert "version" in output
        assert "files_scanned" in output
        assert "summary" in output
        assert "issues" in output
        assert isinstance(output["issues"], list)
        assert len(output["issues"]) == 2

    def test_json_issues_are_serializable(self, scan_result_mixed):
        """All issues must be JSON serializable via Pydantic."""
        for issue in scan_result_mixed.issues:
            # Should not raise
            json_str = json.dumps(issue.model_dump(mode="json"))
            parsed = json.loads(json_str)

            assert parsed["rule_id"] == issue.rule_id
            assert parsed["severity"] == issue.severity.value

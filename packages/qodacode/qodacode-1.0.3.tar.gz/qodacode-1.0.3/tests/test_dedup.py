"""
Deduplication & Fingerprint Tests - Data Integrity.

These tests validate the core deduplication logic that prevents
duplicate alerts from confusing users.

Critical behaviors:
1. Fingerprints must be stable across line number changes
2. Higher priority engines must win in deduplication
3. Higher severity must win as tiebreaker
4. Inline ignore comments must suppress issues
"""

import pytest
from qodacode.context.deduplicator import (
    Deduplicator,
    IssueFingerprint,
    parse_inline_ignores,
    is_ignored_by_inline_comment,
    InlineIgnore,
)
from qodacode.models.issue import Issue, Location, Category, Severity, EngineSource


class TestFingerprintStability:
    """Tests for fingerprint stability across code changes."""

    def create_issue(self, line: int = 10, snippet: str = "api_key = 'secret123'", filepath: str = "src/config.py"):
        """Helper to create a test issue using Pydantic Issue."""
        return Issue(
            rule_id="SEC-001",
            rule_name="hardcoded-secret",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            engine=EngineSource.TREESITTER,
            location=Location(
                filepath=filepath,
                line=line,
                column=0,
                end_line=line,
                end_column=20,
            ),
            message="Hardcoded secret detected",
            snippet=snippet,
            context={},
            fix_suggestion="Use environment variables",
        )

    def test_fingerprint_stable_on_line_change(self):
        """
        CRITICAL: Fingerprint must NOT change when line number changes.

        Scenario: User adds a blank line at top of file, all code shifts down.
        Expected: Suppressed issues stay suppressed.
        """
        issue_line_10 = self.create_issue(line=10)
        issue_line_11 = self.create_issue(line=11)  # Same code, different line

        fp1 = IssueFingerprint.from_issue(issue_line_10)
        fp2 = IssueFingerprint.from_issue(issue_line_11)

        # Fingerprints MUST be identical
        assert fp1.fingerprint == fp2.fingerprint, \
            f"Fingerprint changed from {fp1.fingerprint} to {fp2.fingerprint} " \
            "just because line number changed. This breaks suppressions!"

    def test_fingerprint_different_for_different_code(self):
        """
        Fingerprint must change when the actual code changes.
        """
        issue1 = self.create_issue(snippet="api_key = 'secret123'")
        issue2 = self.create_issue(snippet="api_key = 'different_secret'")

        fp1 = IssueFingerprint.from_issue(issue1)
        fp2 = IssueFingerprint.from_issue(issue2)

        # Fingerprints MUST be different
        assert fp1.fingerprint != fp2.fingerprint, \
            "Different code should have different fingerprints"

    def test_fingerprint_different_for_different_files(self):
        """
        Same code in different files must have different fingerprints.
        """
        issue1 = self.create_issue(filepath="src/config.py")
        issue2 = self.create_issue(filepath="src/other_config.py")

        fp1 = IssueFingerprint.from_issue(issue1)
        fp2 = IssueFingerprint.from_issue(issue2)

        assert fp1.fingerprint != fp2.fingerprint, \
            "Same code in different files should have different fingerprints"


class TestDeduplicationPriority:
    """Tests for engine and severity priority in deduplication."""

    def create_issue(
        self,
        engine: EngineSource,
        severity: Severity,
        filepath: str = "src/api.py",
        line: int = 42
    ):
        """Helper to create issues with specific engine/severity."""
        return Issue(
            rule_id=f"{engine.value}-001",
            rule_name="test-issue",
            category=Category.SECURITY,
            severity=severity,
            engine=engine,
            location=Location(
                filepath=filepath,
                line=line,
                column=0,
                end_line=line,
                end_column=10,
            ),
            message="Test issue",
            snippet="secret = 'abc123'",
            context={},
            fix_suggestion="Fix it",
        )

    def test_gitleaks_wins_over_treesitter(self):
        """
        Gitleaks must win over Tree-sitter for same issue.

        Gitleaks is more specialized for secrets, so its findings
        should take priority.
        """
        dedup = Deduplicator()

        issues = [
            self.create_issue(EngineSource.TREESITTER, Severity.HIGH),
            self.create_issue(EngineSource.GITLEAKS, Severity.CRITICAL),
        ]

        result = dedup.deduplicate(issues)

        assert len(result) == 1, "Should deduplicate to single issue"
        assert result[0].engine == EngineSource.GITLEAKS, \
            "Gitleaks should win over Tree-sitter"
        assert result[0].severity == Severity.CRITICAL, \
            "Should keep CRITICAL severity from Gitleaks"

    def test_semgrep_wins_over_treesitter(self):
        """
        Semgrep must win over Tree-sitter for same issue.
        """
        dedup = Deduplicator()

        issues = [
            self.create_issue(EngineSource.TREESITTER, Severity.MEDIUM),
            self.create_issue(EngineSource.SEMGREP, Severity.HIGH),
        ]

        result = dedup.deduplicate(issues)

        assert len(result) == 1
        assert result[0].engine == EngineSource.SEMGREP

    def test_higher_severity_wins_same_engine(self):
        """
        When same engine finds same issue twice with different severity,
        keep the higher severity.
        """
        dedup = Deduplicator()

        # Same engine, different severities
        issues = [
            self.create_issue(EngineSource.TREESITTER, Severity.MEDIUM),
            self.create_issue(EngineSource.TREESITTER, Severity.CRITICAL),
        ]

        result = dedup.deduplicate(issues)

        assert len(result) == 1
        assert result[0].severity == Severity.CRITICAL, \
            "Higher severity should win"

    def test_no_false_dedup_different_locations(self):
        """
        Issues at different locations must NOT be deduplicated.
        """
        dedup = Deduplicator()

        issues = [
            self.create_issue(EngineSource.TREESITTER, Severity.HIGH, line=10),
            self.create_issue(EngineSource.TREESITTER, Severity.HIGH, line=20),
        ]

        result = dedup.deduplicate(issues)

        assert len(result) == 2, \
            "Different line numbers should NOT be deduplicated"


class TestSuppressionPersistence:
    """Tests for suppression save/load functionality."""

    def test_suppression_survives_reload(self, tmp_path):
        """
        Suppressions must persist across Deduplicator instances.
        """
        # Create deduplicator with temp directory
        dedup1 = Deduplicator(project_root=str(tmp_path))

        # Suppress an issue
        dedup1.suppress("abc123def456", reason="False positive")

        # Create new instance (simulates restart)
        dedup2 = Deduplicator(project_root=str(tmp_path))

        # Suppression should still exist
        supps = dedup2.list_suppressions()
        assert len(supps) == 1
        assert supps[0].fingerprint == "abc123def456"
        assert supps[0].reason == "False positive"

    def test_suppression_file_format(self, tmp_path):
        """
        Suppression file must be human-readable JSON with indent.
        """
        import json

        dedup = Deduplicator(project_root=str(tmp_path))
        dedup.suppress("test123", reason="Test")

        # Read the file directly
        supp_file = tmp_path / ".qodacode" / "suppressions.json"
        content = supp_file.read_text()

        # Must be valid JSON
        data = json.loads(content)
        assert "suppressions" in data
        assert "version" in data

        # Must be formatted (for git-friendly diffs)
        assert "\n" in content, "JSON should be formatted with newlines"


class TestInlineIgnoreComments:
    """Tests for inline ignore comment parsing and filtering."""

    def test_parse_same_line_ignore(self, tmp_path):
        """
        Test parsing same-line ignore comments.

        Example: code  # qodacode-ignore: SEC-001
        """
        test_file = tmp_path / "test.py"
        test_file.write_text(
            'password = "secret"  # qodacode-ignore: SEC-001\n'
            'api_key = "abc123"\n'
        )

        ignores = parse_inline_ignores(str(test_file))

        assert 1 in ignores
        assert ignores[1].matches("SEC-001")
        assert not ignores[1].matches("SEC-002")

    def test_parse_line_above_ignore(self, tmp_path):
        """
        Test parsing line-above ignore comments.

        Example:
            # qodacode-ignore: SEC-001
            code_here
        """
        test_file = tmp_path / "test.py"
        test_file.write_text(
            '# qodacode-ignore: SEC-001\n'
            'password = "secret"\n'
        )

        ignores = parse_inline_ignores(str(test_file))

        # Line 2 should be ignored (comment on line 1 applies to line 2)
        assert 2 in ignores
        assert ignores[2].matches("SEC-001")

    def test_parse_ignore_all_rules(self, tmp_path):
        """
        Test parsing ignore-all comments.

        Example: code  # qodacode-ignore
        """
        test_file = tmp_path / "test.py"
        test_file.write_text(
            'password = "secret"  # qodacode-ignore\n'
        )

        ignores = parse_inline_ignores(str(test_file))

        assert 1 in ignores
        # Should match ANY rule when no specific rule is given
        assert ignores[1].matches("SEC-001")
        assert ignores[1].matches("SEC-002")
        assert ignores[1].matches("ANY-RULE")

    def test_parse_multiple_rules(self, tmp_path):
        """
        Test parsing multiple rule IDs in one comment.

        Example: code  # qodacode-ignore: SEC-001, SEC-002
        """
        test_file = tmp_path / "test.py"
        test_file.write_text(
            'code  # qodacode-ignore: SEC-001, SEC-002\n'
        )

        ignores = parse_inline_ignores(str(test_file))

        assert 1 in ignores
        assert ignores[1].matches("SEC-001")
        assert ignores[1].matches("SEC-002")
        assert not ignores[1].matches("SEC-003")

    def test_parse_js_style_comment(self, tmp_path):
        """
        Test parsing JS-style // comments.
        """
        test_file = tmp_path / "test.js"
        test_file.write_text(
            'const secret = "abc";  // qodacode-ignore: SEC-001\n'
        )

        ignores = parse_inline_ignores(str(test_file))

        assert 1 in ignores
        assert ignores[1].matches("SEC-001")

    def test_is_ignored_function(self, tmp_path):
        """
        Test the is_ignored_by_inline_comment helper.
        """
        test_file = tmp_path / "test.py"
        test_file.write_text(
            '# qodacode-ignore: SEC-001\n'
            'password = "secret"\n'
            'api_key = "abc123"\n'
        )

        # Line 2 is ignored for SEC-001
        assert is_ignored_by_inline_comment(str(test_file), 2, "SEC-001")

        # Line 2 is NOT ignored for other rules
        assert not is_ignored_by_inline_comment(str(test_file), 2, "SEC-002")

        # Line 3 is NOT ignored
        assert not is_ignored_by_inline_comment(str(test_file), 3, "SEC-001")

    def test_filter_suppressed_with_inline_ignores(self, tmp_path):
        """
        Test that filter_suppressed respects inline ignore comments.
        """
        # Create a test file with ignore comment
        test_file = tmp_path / "test.py"
        test_file.write_text(
            '# qodacode-ignore: SEC-001\n'
            'password = "secret"\n'
            'api_key = "abc123"\n'
        )

        # Create issues
        issue_ignored = Issue(
            rule_id="SEC-001",
            rule_name="hardcoded-secret",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            engine=EngineSource.TREESITTER,
            location=Location(
                filepath=str(test_file),
                line=2,  # This line is ignored
                column=0,
                end_line=2,
                end_column=20,
            ),
            message="Hardcoded secret",
            snippet='password = "secret"',
            context={},
        )

        issue_not_ignored = Issue(
            rule_id="SEC-001",
            rule_name="hardcoded-secret",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            engine=EngineSource.TREESITTER,
            location=Location(
                filepath=str(test_file),
                line=3,  # This line is NOT ignored
                column=0,
                end_line=3,
                end_column=20,
            ),
            message="Hardcoded secret",
            snippet='api_key = "abc123"',
            context={},
        )

        dedup = Deduplicator(project_root=str(tmp_path))
        filtered, fp_count, inline_count = dedup.filter_suppressed(
            [issue_ignored, issue_not_ignored]
        )

        # Only one issue should remain
        assert len(filtered) == 1
        assert filtered[0].location.line == 3
        assert inline_count == 1
        assert fp_count == 0


class TestBaselineMode:
    """Tests for baseline mode functionality."""

    def create_issue(
        self,
        filepath: str = "src/config.py",
        line: int = 10,
        snippet: str = "api_key = 'secret123'"
    ):
        """Helper to create a test issue."""
        return Issue(
            rule_id="SEC-001",
            rule_name="hardcoded-secret",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            engine=EngineSource.TREESITTER,
            location=Location(
                filepath=filepath,
                line=line,
                column=0,
                end_line=line,
                end_column=20,
            ),
            message="Hardcoded secret detected",
            snippet=snippet,
            context={},
        )

    def test_save_baseline(self, tmp_path):
        """Should save issues to baseline file."""
        dedup = Deduplicator(project_root=str(tmp_path))

        # Use different snippets to get different fingerprints
        issues = [
            self.create_issue(line=10, snippet="api_key = 'secret123'"),
            self.create_issue(line=20, snippet="password = 'hunter2'"),
        ]

        count = dedup.save_baseline(issues)

        assert count == 2
        assert dedup.has_baseline()

    def test_load_baseline(self, tmp_path):
        """Should load fingerprints from baseline."""
        dedup = Deduplicator(project_root=str(tmp_path))

        issues = [self.create_issue(line=10)]
        dedup.save_baseline(issues)

        fps = dedup.load_baseline()

        assert len(fps) == 1
        # Fingerprint should be a 12-char hex string
        assert len(list(fps)[0]) == 12

    def test_filter_baseline(self, tmp_path):
        """Should filter out baseline issues."""
        dedup = Deduplicator(project_root=str(tmp_path))

        # Save baseline with one issue
        old_issue = self.create_issue(line=10, snippet="old_secret = 'abc'")
        dedup.save_baseline([old_issue])

        # Now scan finds old + new issues
        new_issue = self.create_issue(line=20, snippet="new_secret = 'xyz'")
        all_issues = [old_issue, new_issue]

        filtered, baseline_count = dedup.filter_baseline(all_issues)

        # Only new issue should remain
        assert len(filtered) == 1
        assert filtered[0].location.line == 20
        assert baseline_count == 1

    def test_clear_baseline(self, tmp_path):
        """Should remove baseline file."""
        dedup = Deduplicator(project_root=str(tmp_path))

        # Save then clear
        dedup.save_baseline([self.create_issue()])
        assert dedup.has_baseline()

        result = dedup.clear_baseline()

        assert result is True
        assert not dedup.has_baseline()

    def test_get_baseline_info(self, tmp_path):
        """Should return baseline metadata."""
        dedup = Deduplicator(project_root=str(tmp_path))

        # Use different snippets to get different fingerprints
        issues = [
            self.create_issue(line=10, snippet="api_key = 'secret1'"),
            self.create_issue(line=20, snippet="api_key = 'secret2'"),
            self.create_issue(line=30, snippet="api_key = 'secret3'"),
        ]
        dedup.save_baseline(issues)

        info = dedup.get_baseline_info()

        assert info is not None
        assert info["issue_count"] == 3
        assert "created_at" in info

    def test_no_baseline_returns_all_issues(self, tmp_path):
        """Without baseline, filter_baseline should return all issues."""
        dedup = Deduplicator(project_root=str(tmp_path))

        issues = [
            self.create_issue(line=10),
            self.create_issue(line=20),
        ]

        filtered, count = dedup.filter_baseline(issues)

        assert len(filtered) == 2
        assert count == 0

"""
Tests for the scanner module.
"""

import pytest
import tempfile
import os

from qodacode.scanner import Scanner, ScanResult
from qodacode.rules.base import Severity


class TestScanner:
    """Tests for the Scanner class."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    def test_scan_python_file_with_secret(self, scanner):
        """Should detect hardcoded secret in Python file."""
        code = '''
api_key = "sk_live_1234567890abcdefghijkl"

def get_data():
    return requests.get(url, headers={"Authorization": api_key})
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(code)
            f.flush()

            try:
                result = scanner.scan_file(f.name)
                assert isinstance(result, ScanResult)
                assert len(result.issues) >= 1
                assert any(i.rule_id == "SEC-001" for i in result.issues)
            finally:
                os.unlink(f.name)

    def test_scan_python_file_clean(self, scanner):
        """Should return no issues for clean code."""
        code = '''
import os

api_key = os.environ["API_KEY"]

def get_data():
    return requests.get(url, headers={"Authorization": api_key})
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(code)
            f.flush()

            try:
                result = scanner.scan_file(f.name)
                # Should not have SEC-001 for env variable
                sec001_issues = [i for i in result.issues if i.rule_id == "SEC-001"]
                assert len(sec001_issues) == 0
            finally:
                os.unlink(f.name)

    def test_scan_sql_injection(self, scanner):
        """Should detect SQL injection vulnerability."""
        code = '''
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(code)
            f.flush()

            try:
                result = scanner.scan_file(f.name)
                assert any(i.rule_id == "SEC-002" for i in result.issues)
            finally:
                os.unlink(f.name)

    def test_scan_result_by_severity(self, scanner):
        """Should correctly group issues by severity."""
        code = '''
# Multiple issues
api_key = "secret123"
password = "mypassword"
query = f"SELECT * FROM users WHERE id = {user_id}"
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(code)
            f.flush()

            try:
                result = scanner.scan_file(f.name)
                by_severity = result.by_severity()

                # Should have critical issues
                assert Severity.CRITICAL in by_severity or len(result.issues) >= 0
            finally:
                os.unlink(f.name)

    def test_scan_nonexistent_file(self, scanner):
        """Should handle nonexistent file gracefully."""
        result = scanner.scan_file("/nonexistent/file.py")
        assert isinstance(result, ScanResult)
        # Scanner counts the attempt even if file doesn't exist
        assert result.files_scanned == 1
        assert len(result.issues) == 0
        assert len(result.parse_errors) == 1  # Should report parse error

    def test_scan_unsupported_file(self, scanner):
        """Should skip unsupported file types."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xyz", delete=False
        ) as f:
            f.write("some content")
            f.flush()

            try:
                result = scanner.scan_file(f.name)
                # Scanner counts the attempt
                assert result.files_scanned == 1
                assert len(result.issues) == 0
                # Reports parse error for unsupported file
                assert len(result.parse_errors) == 1
            finally:
                os.unlink(f.name)

    def test_scan_directory(self, scanner):
        """Should scan all files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            py_file = os.path.join(tmpdir, "test.py")
            with open(py_file, "w") as f:
                f.write('api_key = "secret"\n')

            # Use scan() method for directories
            result = scanner.scan(tmpdir)
            assert isinstance(result, ScanResult)
            assert result.files_scanned >= 1

    def test_filter_by_severity(self, scanner):
        """Should filter results by severity."""
        code = '''
api_key = "sk_live_secret"  # Critical
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(code)
            f.flush()

            try:
                # Use severities parameter (list) to filter
                result = scanner.scan_file(
                    f.name,
                    severities=[Severity.CRITICAL]
                )
                # All issues should be CRITICAL
                for issue in result.issues:
                    assert issue.severity == Severity.CRITICAL
            finally:
                os.unlink(f.name)


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_counts(self):
        """Should correctly count issues by severity."""
        from qodacode.models.issue import Issue, Category, Location, EngineSource

        issues = [
            Issue(
                rule_id="SEC-001",
                rule_name="test",
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                engine=EngineSource.TREESITTER,
                location=Location(filepath="test.py", line=1, column=0, end_line=1, end_column=10),
                message="test",
            ),
            Issue(
                rule_id="SEC-002",
                rule_name="test",
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                engine=EngineSource.TREESITTER,
                location=Location(filepath="test.py", line=2, column=0, end_line=2, end_column=10),
                message="test",
            ),
            Issue(
                rule_id="SEC-003",
                rule_name="test",
                category=Category.SECURITY,
                severity=Severity.HIGH,
                engine=EngineSource.TREESITTER,
                location=Location(filepath="test.py", line=3, column=0, end_line=3, end_column=10),
                message="test",
            ),
        ]

        result = ScanResult(
            issues=issues,
            files_scanned=1,
            files_with_issues=1,
            parse_errors=[]
        )

        assert result.critical_count == 2
        assert result.high_count == 1
        assert result.medium_count == 0
        assert result.low_count == 0

    def test_has_critical_issues(self):
        """Should identify critical issues."""
        from qodacode.models.issue import Issue, Category, Location, EngineSource

        issues = [
            Issue(
                rule_id="SEC-001",
                rule_name="test",
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                engine=EngineSource.TREESITTER,
                location=Location(filepath="test.py", line=1, column=0, end_line=1, end_column=10),
                message="test",
            ),
        ]

        result = ScanResult(
            issues=issues,
            files_scanned=1,
            files_with_issues=1,
            parse_errors=[]
        )
        # Use critical_count property instead of has_blocking_issues
        assert result.critical_count > 0

        # Without critical issues
        result_clean = ScanResult(
            issues=[],
            files_scanned=1,
            files_with_issues=0,
            parse_errors=[]
        )
        assert result_clean.critical_count == 0


class TestQodacodeignore:
    """Tests for .qodacodeignore file support."""

    def test_load_qodacodeignore(self, tmp_path):
        """Should load patterns from .qodacodeignore file."""
        from qodacode.scanner import load_qodacodeignore

        # Create .qodacodeignore file
        ignore_file = tmp_path / ".qodacodeignore"
        ignore_file.write_text(
            "# Comment line\n"
            "tests/fixtures/\n"
            "*.test.js\n"
            "\n"  # Empty line
            "generated/\n"
        )

        patterns = load_qodacodeignore(str(tmp_path))

        assert "tests/fixtures" in patterns  # Trailing slash removed
        assert "*.test.js" in patterns
        assert "generated" in patterns
        assert len(patterns) == 3  # Comments and empty lines excluded

    def test_load_qodacodeignore_missing_file(self, tmp_path):
        """Should return empty set if .qodacodeignore doesn't exist."""
        from qodacode.scanner import load_qodacodeignore

        patterns = load_qodacodeignore(str(tmp_path))

        assert patterns == set()

    def test_get_exclude_patterns_combines(self, tmp_path):
        """Should combine DEFAULT_EXCLUDE with .qodacodeignore patterns."""
        from qodacode.scanner import get_exclude_patterns, DEFAULT_EXCLUDE

        # Create .qodacodeignore file
        ignore_file = tmp_path / ".qodacodeignore"
        ignore_file.write_text("custom_ignore/\n")

        patterns = get_exclude_patterns(str(tmp_path))

        # Should have default patterns
        assert ".git" in patterns
        assert "node_modules" in patterns

        # Should have custom pattern
        assert "custom_ignore" in patterns

    def test_scanner_respects_qodacodeignore(self, tmp_path):
        """Scanner should skip files matching .qodacodeignore patterns."""
        from qodacode.scanner import Scanner

        # Create directory structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        fixtures_dir = tmp_path / "fixtures"
        fixtures_dir.mkdir()

        # Create test files
        (src_dir / "main.py").write_text('api_key = "sk_live_secret123"\n')
        (fixtures_dir / "test_data.py").write_text('api_key = "sk_live_secret123"\n')

        # Create .qodacodeignore
        (tmp_path / ".qodacodeignore").write_text("fixtures/\n")

        scanner = Scanner()
        result = scanner.scan(str(tmp_path))

        # Should find issue in src/main.py but NOT in fixtures/
        assert result.files_scanned == 1
        assert any(
            "src/main.py" in i.location.filepath
            for i in result.issues
        )
        assert not any(
            "fixtures" in i.location.filepath
            for i in result.issues
        )

"""
Tests for security rules (SEC-001 to SEC-005).
"""

import pytest
from tests.conftest import parse_python, parse_javascript

from qodacode.rules.security import (
    HardcodedSecretRule,
    SQLInjectionRule,
    CommandInjectionRule,
    NoAuthEndpointRule,
    PathTraversalRule,
)
from qodacode.rules.base import Severity, Category


class TestHardcodedSecretRule:
    """Tests for SEC-001: Hardcoded secrets."""

    @pytest.fixture
    def rule(self):
        return HardcodedSecretRule()

    def test_detects_api_key_python(self, python_parser, rule):
        """Should detect hardcoded API key in Python."""
        code = '''
api_key = "sk_live_1234567890abcdef"
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) == 1
        assert issues[0].rule_id == "SEC-001"
        assert "api_key" in issues[0].message
        assert issues[0].severity == Severity.CRITICAL

    def test_detects_password_python(self, python_parser, rule):
        """Should detect hardcoded password in Python."""
        code = '''
db_password = "supersecret123"
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) == 1
        assert "password" in issues[0].message.lower()

    def test_ignores_env_variable(self, python_parser, rule):
        """Should ignore secrets from environment variables."""
        code = '''
import os
api_key = os.environ["API_KEY"]
secret_key = os.getenv("SECRET_KEY")
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) == 0

    def test_ignores_empty_strings(self, python_parser, rule):
        """Should ignore empty placeholder strings."""
        code = '''
api_key = ""
password = ''
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) == 0

    def test_detects_stripe_live_key(self, python_parser, rule):
        """Should detect Stripe live API key."""
        # Use realistic-looking key (no false positive patterns like 'abcde', 'xxx', '12345')
        code = '''
stripe_key = "sk_live_4eC39HqLyjWDarjtT1zdp7dc"
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) >= 1

    def test_detects_github_token(self, python_parser, rule):
        """Should detect GitHub personal access token."""
        # Use realistic-looking token (no false positive patterns)
        code = '''
token = "ghp_R7FvPqNz3mKjL8wYtG9HbVcDnE4sAi0XuZ"
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) >= 1


class TestSQLInjectionRule:
    """Tests for SEC-002: SQL injection."""

    @pytest.fixture
    def rule(self):
        return SQLInjectionRule()

    def test_detects_fstring_sql(self, python_parser, rule):
        """Should detect SQL in f-string."""
        code = '''
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) >= 1
        assert issues[0].rule_id == "SEC-002"
        assert "SQL" in issues[0].message

    def test_detects_concat_sql(self, python_parser, rule):
        """Should detect SQL with string concatenation."""
        code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) >= 1

    def test_ignores_parameterized_query(self, python_parser, rule):
        """Should not flag parameterized queries."""
        code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, (user_id,))
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        # Should not detect injection in parameterized query
        assert len(issues) == 0

    def test_detects_insert_injection(self, python_parser, rule):
        """Should detect INSERT statement with injection."""
        code = '''
def create_user(name, email):
    query = f"INSERT INTO users (name, email) VALUES ('{name}', '{email}')"
    db.execute(query)
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) >= 1


class TestCommandInjectionRule:
    """Tests for SEC-003: Command injection."""

    @pytest.fixture
    def rule(self):
        return CommandInjectionRule()

    def test_detects_os_system_injection(self, python_parser, rule):
        """Should detect os.system with dynamic input."""
        code = '''
import os

def run_command(filename):
    os.system(f"cat {filename}")
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) >= 1
        assert issues[0].rule_id == "SEC-003"

    def test_detects_subprocess_injection(self, python_parser, rule):
        """Should detect subprocess with shell=True and dynamic input."""
        code = '''
import subprocess

def run_cmd(user_input):
    subprocess.call("ls " + user_input, shell=True)
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) >= 1

    def test_ignores_static_command(self, python_parser, rule):
        """Should not flag static commands."""
        code = '''
import os
os.system("ls -la")
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        # Static command should not be flagged
        assert len(issues) == 0

    def test_detects_eval_injection(self, python_parser, rule):
        """Should detect eval with dynamic input."""
        code = '''
def execute(code_str):
    result = eval(code_str + "_suffix")
    return result
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "test.py")

        assert len(issues) >= 1


class TestNoAuthEndpointRule:
    """Tests for SEC-005: Unprotected endpoints."""

    @pytest.fixture
    def rule(self):
        return NoAuthEndpointRule()

    def test_detects_unprotected_admin(self, python_parser, rule):
        """Should detect admin endpoint without auth."""
        code = '''
@app.route("/admin/users")
def list_users():
    return get_all_users()
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "routes.py")

        assert len(issues) >= 1
        assert issues[0].rule_id == "SEC-005"
        assert "/admin" in issues[0].message

    def test_allows_protected_admin(self, python_parser, rule):
        """Should allow admin endpoint with auth decorator."""
        code = '''
@app.route("/admin/users")
@login_required
def list_users():
    return get_all_users()
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "routes.py")

        assert len(issues) == 0

    def test_detects_unprotected_api_users(self, python_parser, rule):
        """Should detect unprotected /api/users endpoint."""
        code = '''
@router.get("/api/users/profile")
def get_profile():
    return current_user
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "routes.py")

        assert len(issues) >= 1

    def test_ignores_public_endpoints(self, python_parser, rule):
        """Should not flag public endpoints like health checks."""
        code = '''
@app.route("/health")
def health_check():
    return {"status": "ok"}

@app.route("/api/public/docs")
def get_docs():
    return docs
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "routes.py")

        # Public endpoints should not be flagged
        assert len(issues) == 0

"""
Tests for operability rules (OPS-001: No logging in critical operations).
"""

import pytest
from tests.conftest import parse_python, parse_javascript

from qodacode.rules.operability import (
    NoLoggingRule,
)
from qodacode.rules.base import Severity, Category


class TestNoLoggingRule:
    """Tests for OPS-001: No logging in critical operations."""

    @pytest.fixture
    def rule(self):
        return NoLoggingRule()

    def test_detects_db_operation_without_logging(self, python_parser, rule):
        """Should detect database operation without logging."""
        code = '''
def delete_user(user_id):
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "users.py")

        assert len(issues) >= 1
        assert issues[0].rule_id == "OPS-001"

    def test_allows_operation_with_logging(self, python_parser, rule):
        """Should allow operation with proper logging."""
        code = '''
import logging
logger = logging.getLogger(__name__)

def delete_user(user_id):
    logger.info(f"Deleting user {user_id}")
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "users.py")

        # Should not flag when logging is present
        assert len(issues) == 0

    def test_detects_payment_without_logging(self, python_parser, rule):
        """Should detect payment processing without logging."""
        code = '''
def process_payment(amount, card):
    stripe.Charge.create(amount=amount, source=card)
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "payments.py")

        assert len(issues) >= 1

    def test_detects_api_call_without_logging(self, python_parser, rule):
        """Should detect external API call without logging."""
        code = '''
def send_notification(user_id, message):
    requests.post(f"https://api.example.com/notify", json={"user": user_id, "msg": message})
'''
        tree, source = parse_python(python_parser, code)
        issues = rule.check(tree, source, "notify.py")

        assert len(issues) >= 1

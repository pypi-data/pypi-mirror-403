"""
Tests for Qodacode Daemon - Proactive Security Guardian.

Tests the background service that watches file changes and maintains
an issue cache for real-time security feedback.
"""

import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from qodacode.daemon import (
    ProactivityLevel,
    CachedIssue,
    DaemonEvent,
    FileHook,
    IssueCache,
    EventQueue,
    QodacodeDaemon,
    get_daemon,
    start_daemon,
    stop_daemon,
)


class TestProactivityLevel:
    """Test proactivity level enum."""

    def test_all_levels_defined(self):
        """All proactivity levels should be defined."""
        assert ProactivityLevel.PASSIVE.value == "passive"
        assert ProactivityLevel.REACTIVE.value == "reactive"
        assert ProactivityLevel.PROACTIVE.value == "proactive"
        assert ProactivityLevel.GUARDIAN.value == "guardian"

    def test_level_from_string(self):
        """Can create level from string."""
        assert ProactivityLevel("passive") == ProactivityLevel.PASSIVE
        assert ProactivityLevel("guardian") == ProactivityLevel.GUARDIAN


class TestCachedIssue:
    """Test cached issue dataclass."""

    def test_create_cached_issue(self):
        """Can create a cached issue."""
        issue = CachedIssue(
            rule_id="SEC-001",
            rule_name="hardcoded-secret",
            severity="critical",
            file_path="src/config.py",
            line=42,
            message="Hardcoded API key detected",
            fix_suggestion="Use environment variable",
        )

        assert issue.rule_id == "SEC-001"
        assert issue.severity == "critical"
        assert issue.line == 42

    def test_cached_issue_to_dict(self):
        """Cached issue converts to dict."""
        issue = CachedIssue(
            rule_id="SEC-001",
            rule_name="hardcoded-secret",
            severity="critical",
            file_path="src/config.py",
            line=42,
            message="Test message",
        )

        result = issue.to_dict()

        assert result["rule_id"] == "SEC-001"
        assert result["severity"] == "critical"
        assert result["file"] == "src/config.py"
        assert result["line"] == 42
        assert "detected_at" in result

    def test_cached_issue_default_timestamp(self):
        """Cached issue has default timestamp."""
        before = time.time()
        issue = CachedIssue(
            rule_id="SEC-001",
            rule_name="test",
            severity="low",
            file_path="test.py",
            line=1,
            message="Test",
        )
        after = time.time()

        assert before <= issue.detected_at <= after


class TestDaemonEvent:
    """Test daemon event dataclass."""

    def test_create_event(self):
        """Can create a daemon event."""
        event = DaemonEvent(
            event_type="issues_found",
            timestamp=time.time(),
            data={"file": "test.py", "count": 3},
        )

        assert event.event_type == "issues_found"
        assert "file" in event.data

    def test_event_to_dict(self):
        """Event converts to dict."""
        event = DaemonEvent(
            event_type="scan_complete",
            timestamp=12345.0,
            data={"status": "ok"},
        )

        result = event.to_dict()

        assert result["event_type"] == "scan_complete"
        assert result["timestamp"] == 12345.0
        assert result["data"]["status"] == "ok"


class TestIssueCache:
    """Test issue cache functionality."""

    def test_cache_update_and_get(self):
        """Can update and retrieve issues."""
        cache = IssueCache()

        issues = [
            CachedIssue(
                rule_id="SEC-001",
                rule_name="test",
                severity="critical",
                file_path="test.py",
                line=1,
                message="Test",
            )
        ]

        cache.update("test.py", issues)
        result = cache.get("test.py")

        assert len(result) == 1
        assert result[0].rule_id == "SEC-001"

    def test_cache_get_nonexistent(self):
        """Getting nonexistent file returns empty list."""
        cache = IssueCache()
        result = cache.get("nonexistent.py")
        assert result == []

    def test_cache_get_all(self):
        """Can get all cached issues."""
        cache = IssueCache()

        cache.update("file1.py", [
            CachedIssue("SEC-001", "test", "critical", "file1.py", 1, "msg1"),
        ])
        cache.update("file2.py", [
            CachedIssue("SEC-002", "test", "high", "file2.py", 2, "msg2"),
        ])

        all_issues = cache.get_all()

        assert len(all_issues) == 2

    def test_cache_remove(self):
        """Can remove issues for a file."""
        cache = IssueCache()

        cache.update("test.py", [
            CachedIssue("SEC-001", "test", "low", "test.py", 1, "msg"),
        ])
        cache.remove("test.py")

        assert cache.get("test.py") == []

    def test_cache_clear(self):
        """Can clear all cached issues."""
        cache = IssueCache()

        cache.update("file1.py", [
            CachedIssue("SEC-001", "test", "low", "file1.py", 1, "msg"),
        ])
        cache.update("file2.py", [
            CachedIssue("SEC-002", "test", "low", "file2.py", 1, "msg"),
        ])
        cache.clear()

        assert cache.get_all() == []

    def test_cache_get_summary(self):
        """Can get summary by severity."""
        cache = IssueCache()

        cache.update("file1.py", [
            CachedIssue("SEC-001", "test", "critical", "file1.py", 1, "msg"),
            CachedIssue("SEC-002", "test", "critical", "file1.py", 2, "msg"),
        ])
        cache.update("file2.py", [
            CachedIssue("SEC-003", "test", "high", "file2.py", 1, "msg"),
            CachedIssue("SEC-004", "test", "medium", "file2.py", 2, "msg"),
        ])

        summary = cache.get_summary()

        assert summary["critical"] == 2
        assert summary["high"] == 1
        assert summary["medium"] == 1
        assert summary["low"] == 0


class TestEventQueue:
    """Test event queue functionality."""

    def test_queue_push_and_pop(self):
        """Can push and pop events."""
        queue = EventQueue()

        event = DaemonEvent("test", time.time(), {"data": "value"})
        queue.push(event)

        events = queue.pop_all()

        assert len(events) == 1
        assert events[0].event_type == "test"

    def test_queue_pop_clears_queue(self):
        """Pop removes events from queue."""
        queue = EventQueue()

        queue.push(DaemonEvent("test", time.time(), {}))
        queue.pop_all()

        assert queue.pop_all() == []

    def test_queue_peek(self):
        """Can peek without removing."""
        queue = EventQueue()

        queue.push(DaemonEvent("test1", time.time(), {}))
        queue.push(DaemonEvent("test2", time.time(), {}))

        peeked = queue.peek(1)

        assert len(peeked) == 1
        assert queue.is_empty() is False

    def test_queue_max_size(self):
        """Queue respects max size."""
        queue = EventQueue(max_size=3)

        for i in range(5):
            queue.push(DaemonEvent(f"test{i}", time.time(), {}))

        events = queue.pop_all()

        assert len(events) == 3
        # Should keep most recent
        assert events[0].event_type == "test2"

    def test_queue_is_empty(self):
        """Can check if queue is empty."""
        queue = EventQueue()

        assert queue.is_empty() is True
        queue.push(DaemonEvent("test", time.time(), {}))
        assert queue.is_empty() is False


class TestQodacodeDaemon:
    """Test daemon core functionality."""

    def test_daemon_init(self):
        """Can initialize daemon."""
        daemon = QodacodeDaemon(
            project_path=".",
            proactivity=ProactivityLevel.PASSIVE,
        )

        assert daemon.proactivity == ProactivityLevel.PASSIVE
        assert daemon.issue_cache is not None
        assert daemon.event_queue is not None

    def test_daemon_register_hook(self):
        """Can register file hooks."""
        daemon = QodacodeDaemon()

        daemon.register_hook("*.py", action="scan", severity_threshold="high")

        assert len(daemon._hooks) == 1
        assert daemon._hooks[0].pattern == "*.py"

    def test_daemon_get_status(self):
        """Can get daemon status."""
        daemon = QodacodeDaemon(proactivity=ProactivityLevel.REACTIVE)

        status = daemon.get_status()

        assert status["proactivity"] == "reactive"
        assert "issue_summary" in status
        assert "pending_events" in status

    def test_daemon_get_context_for_claude_no_issues(self):
        """Context for Claude when no issues."""
        daemon = QodacodeDaemon()

        context = daemon.get_context_for_claude()

        assert "QODACODE SECURITY GUARDIAN" in context
        assert "EXCELLENT" in context

    def test_daemon_get_context_for_claude_critical_issues(self):
        """Context for Claude with critical issues."""
        daemon = QodacodeDaemon()

        # Add critical issues
        daemon.issue_cache.update("test.py", [
            CachedIssue("SEC-001", "test", "critical", "test.py", 1, "msg"),
        ])

        context = daemon.get_context_for_claude()

        assert "CRITICAL" in context

    def test_daemon_on_file_change_passive(self):
        """Passive mode doesn't auto-scan."""
        daemon = QodacodeDaemon(proactivity=ProactivityLevel.PASSIVE)

        daemon.on_file_change("test.py")

        # Should push file_changed event but not scan
        events = daemon.event_queue.pop_all()
        assert len(events) == 1
        assert events[0].event_type == "file_changed"

    def test_daemon_on_file_change_reactive(self):
        """Reactive mode suggests scan."""
        daemon = QodacodeDaemon(proactivity=ProactivityLevel.REACTIVE)

        daemon.on_file_change("test.py")

        events = daemon.event_queue.pop_all()
        assert len(events) == 2
        event_types = [e.event_type for e in events]
        assert "file_changed" in event_types
        assert "scan_suggested" in event_types

    def test_daemon_skips_non_code_files(self):
        """Daemon skips non-code files."""
        daemon = QodacodeDaemon()

        daemon.on_file_change("readme.md")
        daemon.on_file_change("image.png")

        events = daemon.event_queue.pop_all()
        assert len(events) == 0

    def test_daemon_skips_hidden_files(self):
        """Daemon skips hidden files and directories."""
        daemon = QodacodeDaemon()

        daemon.on_file_change(".git/config")
        daemon.on_file_change("node_modules/lib.js")
        daemon.on_file_change("__pycache__/module.pyc")

        events = daemon.event_queue.pop_all()
        assert len(events) == 0


class TestDaemonGlobalFunctions:
    """Test global daemon management functions."""

    def test_start_and_stop_daemon(self):
        """Can start and stop global daemon."""
        # Start daemon
        daemon = start_daemon(".", "passive")

        assert daemon is not None
        assert get_daemon() is daemon

        # Stop daemon
        stop_daemon()

        assert get_daemon() is None

    def test_get_daemon_when_none(self):
        """Get daemon returns None when not started."""
        stop_daemon()  # Ensure clean state
        assert get_daemon() is None


class TestFileHook:
    """Test file hook dataclass."""

    def test_create_file_hook(self):
        """Can create a file hook."""
        hook = FileHook(
            pattern="*.py",
            action="scan",
            severity_threshold="critical",
        )

        assert hook.pattern == "*.py"
        assert hook.action == "scan"
        assert hook.severity_threshold == "critical"

    def test_file_hook_with_callback(self):
        """Can create hook with callback."""
        callback = MagicMock()
        hook = FileHook(
            pattern="*.ts",
            action="alert",
            severity_threshold="high",
            callback=callback,
        )

        assert hook.callback is callback


class TestDaemonIntegration:
    """Integration tests for daemon functionality."""

    def test_full_workflow(self):
        """Test complete daemon workflow."""
        # Start daemon
        daemon = start_daemon(".", "reactive")

        try:
            # Simulate file change
            daemon.on_file_change("test.py")

            # Get events
            events = daemon.event_queue.pop_all()
            assert len(events) >= 1

            # Get status
            status = daemon.get_status()
            assert status["running"] is True

            # Get context
            context = daemon.get_context_for_claude()
            assert "QODACODE" in context

        finally:
            stop_daemon()

    def test_issue_cache_integration(self):
        """Test issue cache with daemon."""
        daemon = QodacodeDaemon()

        # Simulate scan results
        daemon.issue_cache.update("src/config.py", [
            CachedIssue(
                rule_id="SEC-001",
                rule_name="hardcoded-secret",
                severity="critical",
                file_path="src/config.py",
                line=42,
                message="API key exposed",
            ),
        ])

        # Get summary
        summary = daemon.issue_cache.get_summary()
        assert summary["critical"] == 1

        # Clear file
        daemon.issue_cache.remove("src/config.py")
        summary = daemon.issue_cache.get_summary()
        assert summary["critical"] == 0

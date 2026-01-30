"""
Qodacode Daemon - Proactive Security Guardian.

Background service that watches file changes and maintains an issue cache
for real-time security feedback to AI coding assistants.

Features:
- File watching with debouncing
- Issue cache with TTL
- Event queue for push notifications
- Integration with MCP server

Premium Features (by tier):
- REACTIVE (Pro): Suggest scans after changes
- PROACTIVE (Team): Auto-scan on save
- GUARDIAN (Business): Block commits with issues
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Callable, Dict, List, Optional, Set

try:
    import watchdog.events
    import watchdog.observers
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

logger = logging.getLogger("qodacode.daemon")


class ProactivityLevel(Enum):
    """Proactivity levels for the daemon."""
    PASSIVE = "passive"      # Free: Claude calls when it wants
    REACTIVE = "reactive"    # Pro: Suggest scans after changes
    PROACTIVE = "proactive"  # Team: Auto-scan on save
    GUARDIAN = "guardian"    # Business: Block dangerous actions


@dataclass
class CachedIssue:
    """An issue in the cache with metadata."""
    rule_id: str
    rule_name: str
    severity: str
    file_path: str
    line: int
    message: str
    fix_suggestion: Optional[str] = None
    snippet: Optional[str] = None
    detected_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "file": self.file_path,
            "line": self.line,
            "message": self.message,
            "fix_suggestion": self.fix_suggestion,
            "snippet": self.snippet,
            "detected_at": self.detected_at,
        }


@dataclass
class DaemonEvent:
    """Event pushed to the MCP server."""
    event_type: str  # "issues_found", "scan_complete", "file_changed"
    timestamp: float
    data: Dict[str, Any]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "data": self.data,
        }


@dataclass
class FileHook:
    """Registered hook for file changes."""
    pattern: str  # glob pattern like "*.py" or "src/**/*.ts"
    action: str   # "scan", "alert", "block"
    severity_threshold: str  # minimum severity to trigger
    callback: Optional[Callable] = None


class IssueCache:
    """Thread-safe cache for detected issues."""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, List[CachedIssue]] = {}  # file_path -> issues
        self._lock = Lock()
        self._ttl = ttl_seconds

    def update(self, file_path: str, issues: List[CachedIssue]) -> None:
        """Update issues for a file."""
        with self._lock:
            self._cache[file_path] = issues

    def get(self, file_path: str) -> List[CachedIssue]:
        """Get issues for a file."""
        with self._lock:
            return self._cache.get(file_path, [])

    def get_all(self) -> List[CachedIssue]:
        """Get all cached issues."""
        with self._lock:
            all_issues = []
            for issues in self._cache.values():
                all_issues.extend(issues)
            return all_issues

    def remove(self, file_path: str) -> None:
        """Remove issues for a file."""
        with self._lock:
            self._cache.pop(file_path, None)

    def clear(self) -> None:
        """Clear all cached issues."""
        with self._lock:
            self._cache.clear()

    def get_summary(self) -> Dict[str, int]:
        """Get summary counts by severity."""
        with self._lock:
            summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for issues in self._cache.values():
                for issue in issues:
                    if issue.severity in summary:
                        summary[issue.severity] += 1
            return summary


class EventQueue:
    """Thread-safe event queue for push notifications."""

    def __init__(self, max_size: int = 100):
        self._queue: List[DaemonEvent] = []
        self._lock = Lock()
        self._max_size = max_size

    def push(self, event: DaemonEvent) -> None:
        """Push an event to the queue."""
        with self._lock:
            self._queue.append(event)
            # Keep queue bounded
            if len(self._queue) > self._max_size:
                self._queue = self._queue[-self._max_size:]

    def pop_all(self) -> List[DaemonEvent]:
        """Pop all events from the queue."""
        with self._lock:
            events = self._queue.copy()
            self._queue.clear()
            return events

    def peek(self, count: int = 10) -> List[DaemonEvent]:
        """Peek at the most recent events without removing them."""
        with self._lock:
            return self._queue[-count:]

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        with self._lock:
            return len(self._queue) == 0


class QodacodeDaemon:
    """
    Background daemon for proactive security scanning.

    Watches files, maintains issue cache, and pushes events.
    """

    def __init__(
        self,
        project_path: str = ".",
        proactivity: ProactivityLevel = ProactivityLevel.PASSIVE,
        scan_debounce_ms: int = 500,
    ):
        self.project_path = Path(project_path).resolve()
        self.proactivity = proactivity
        self.scan_debounce_ms = scan_debounce_ms

        self.issue_cache = IssueCache()
        self.event_queue = EventQueue()

        self._hooks: List[FileHook] = []
        self._watched_patterns: Set[str] = {".py", ".js", ".ts", ".tsx", ".go", ".java"}
        self._observer = None
        self._running = False
        self._pending_scans: Dict[str, float] = {}  # file_path -> scheduled_time
        self._scan_lock = Lock()

    def register_hook(
        self,
        pattern: str,
        action: str = "scan",
        severity_threshold: str = "critical",
        callback: Optional[Callable] = None,
    ) -> None:
        """Register a file hook for proactive actions."""
        hook = FileHook(
            pattern=pattern,
            action=action,
            severity_threshold=severity_threshold,
            callback=callback,
        )
        self._hooks.append(hook)
        logger.info(f"Registered hook: {pattern} -> {action}")

    def start(self) -> None:
        """Start the daemon (file watcher + background tasks)."""
        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog not available, daemon running in passive mode")
            return

        if self._running:
            return

        self._running = True

        # Start file watcher
        event_handler = _FileChangeHandler(self)
        self._observer = watchdog.observers.Observer()
        self._observer.schedule(
            event_handler,
            str(self.project_path),
            recursive=True,
        )
        self._observer.start()

        # Start background scan processor
        self._scan_thread = Thread(target=self._process_pending_scans, daemon=True)
        self._scan_thread.start()

        logger.info(f"Daemon started watching: {self.project_path}")

    def stop(self) -> None:
        """Stop the daemon."""
        self._running = False

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None

        logger.info("Daemon stopped")

    def on_file_change(self, file_path: str) -> None:
        """Handle a file change event."""
        path = Path(file_path)

        # Skip non-code files
        if path.suffix not in self._watched_patterns:
            return

        # Skip hidden/ignored paths
        if any(part.startswith('.') for part in path.parts):
            return
        if 'node_modules' in path.parts or '__pycache__' in path.parts:
            return

        logger.debug(f"File changed: {file_path}")

        # Push file_changed event
        self.event_queue.push(DaemonEvent(
            event_type="file_changed",
            timestamp=time.time(),
            data={"file": file_path},
        ))

        # Handle based on proactivity level
        if self.proactivity == ProactivityLevel.PASSIVE:
            return

        elif self.proactivity == ProactivityLevel.REACTIVE:
            # Push suggestion event
            self.event_queue.push(DaemonEvent(
                event_type="scan_suggested",
                timestamp=time.time(),
                data={
                    "file": file_path,
                    "message": f"File changed: {path.name}. Consider scanning for issues.",
                },
            ))

        elif self.proactivity in (ProactivityLevel.PROACTIVE, ProactivityLevel.GUARDIAN):
            # Schedule automatic scan with debouncing
            self._schedule_scan(file_path)

    def _schedule_scan(self, file_path: str) -> None:
        """Schedule a scan with debouncing."""
        with self._scan_lock:
            scheduled_time = time.time() + (self.scan_debounce_ms / 1000)
            self._pending_scans[file_path] = scheduled_time

    def _process_pending_scans(self) -> None:
        """Background thread to process pending scans."""
        while self._running:
            try:
                files_to_scan = []
                current_time = time.time()

                with self._scan_lock:
                    for file_path, scheduled_time in list(self._pending_scans.items()):
                        if current_time >= scheduled_time:
                            files_to_scan.append(file_path)
                            del self._pending_scans[file_path]

                for file_path in files_to_scan:
                    self._scan_file(file_path)

                time.sleep(0.1)  # 100ms poll interval

            except Exception as e:
                logger.error(f"Error in scan processor: {e}")

    def _scan_file(self, file_path: str) -> None:
        """Scan a single file and update cache."""
        try:
            from qodacode.scanner import Scanner
            import qodacode.rules.security  # noqa: F401
            import qodacode.rules.robustness  # noqa: F401

            scanner = Scanner()
            result = scanner.scan_file(file_path)

            # Convert to cached issues
            cached_issues = [
                CachedIssue(
                    rule_id=issue.rule_id,
                    rule_name=issue.rule_name,
                    severity=issue.severity.value,
                    file_path=issue.location.filepath,
                    line=issue.location.line,
                    message=issue.message,
                    fix_suggestion=issue.fix_suggestion,
                    snippet=getattr(issue, 'snippet', None),
                )
                for issue in result.issues
            ]

            # Update cache
            self.issue_cache.update(file_path, cached_issues)

            # Push event if issues found
            if cached_issues:
                # Filter by severity for GUARDIAN mode
                critical_high = [i for i in cached_issues
                               if i.severity in ("critical", "high")]

                event_data = {
                    "file": file_path,
                    "total_issues": len(cached_issues),
                    "critical": len([i for i in cached_issues if i.severity == "critical"]),
                    "high": len([i for i in cached_issues if i.severity == "high"]),
                    "issues": [i.to_dict() for i in cached_issues[:5]],  # Top 5
                }

                self.event_queue.push(DaemonEvent(
                    event_type="issues_found",
                    timestamp=time.time(),
                    data=event_data,
                ))

                logger.info(f"Scan complete: {file_path} - {len(cached_issues)} issues")
            else:
                # Clear issues for this file
                self.issue_cache.remove(file_path)

        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")

    def scan_staged(self) -> Dict[str, Any]:
        """Scan git staged files (for pre-commit)."""
        try:
            import subprocess

            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )

            staged_files = [
                f for f in result.stdout.strip().split('\n')
                if f and Path(f).suffix in self._watched_patterns
            ]

            if not staged_files:
                return {
                    "status": "ok",
                    "message": "No staged code files to scan",
                    "issues": [],
                }

            # Scan each staged file
            all_issues = []
            for file_path in staged_files:
                full_path = self.project_path / file_path
                if full_path.exists():
                    self._scan_file(str(full_path))
                    all_issues.extend(self.issue_cache.get(str(full_path)))

            critical_issues = [i for i in all_issues if i.severity == "critical"]

            return {
                "status": "blocked" if critical_issues else "ok",
                "message": (
                    f"BLOCKED: {len(critical_issues)} critical issues found"
                    if critical_issues
                    else f"OK: {len(all_issues)} issues found (no critical)"
                ),
                "staged_files": staged_files,
                "total_issues": len(all_issues),
                "critical": len(critical_issues),
                "issues": [i.to_dict() for i in all_issues],
            }

        except Exception as e:
            logger.error(f"Error scanning staged files: {e}")
            return {"status": "error", "message": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get daemon status and summary."""
        summary = self.issue_cache.get_summary()
        pending_events = len(self.event_queue.peek(100))

        return {
            "running": self._running,
            "proactivity": self.proactivity.value,
            "project": str(self.project_path),
            "issue_summary": summary,
            "pending_events": pending_events,
            "total_cached_issues": sum(summary.values()),
        }

    def get_context_for_claude(self) -> str:
        """
        Generate context string for Claude Code system prompt injection.

        This is the "magic" that makes Claude proactive about security.
        """
        summary = self.issue_cache.get_summary()
        total = sum(summary.values())

        if summary["critical"] > 0:
            security_status = "CRITICAL - Fix security issues before proceeding"
        elif summary["high"] > 0:
            security_status = "WARNING - Security issues detected"
        elif total > 0:
            security_status = f"OK - {total} minor issues"
        else:
            security_status = "EXCELLENT - No issues detected"

        context = f"""
QODACODE SECURITY GUARDIAN ACTIVE

Current Security Status: {security_status}
Issues: {summary['critical']} critical, {summary['high']} high, {summary['medium']} medium

MANDATORY BEHAVIORS:
1. Before any git commit, call qodacode.scan_staged()
2. If critical issues exist, DO NOT proceed until fixed
3. Check qodacode.get_realtime_issues() after editing files

AUTOMATIC BEHAVIORS:
- File changes are monitored in real-time
- Issues are cached and available instantly
- Critical issues will block commits (Guardian mode)
"""
        return context


# File system event handler for watchdog
if WATCHDOG_AVAILABLE:
    class _FileChangeHandler(watchdog.events.FileSystemEventHandler):
        """Handler for file system events."""

        def __init__(self, daemon: QodacodeDaemon):
            self.daemon = daemon

        def on_modified(self, event):
            if not event.is_directory:
                self.daemon.on_file_change(event.src_path)

        def on_created(self, event):
            if not event.is_directory:
                self.daemon.on_file_change(event.src_path)


# Singleton daemon instance
_daemon: Optional[QodacodeDaemon] = None


def get_daemon() -> Optional[QodacodeDaemon]:
    """Get the global daemon instance."""
    return _daemon


def start_daemon(
    project_path: str = ".",
    proactivity: str = "passive",
) -> QodacodeDaemon:
    """Start the global daemon instance."""
    global _daemon

    level = ProactivityLevel(proactivity)
    _daemon = QodacodeDaemon(project_path, level)
    _daemon.start()

    return _daemon


def stop_daemon() -> None:
    """Stop the global daemon instance."""
    global _daemon

    if _daemon:
        _daemon.stop()
        _daemon = None

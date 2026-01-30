"""
Structured audit logging for Qodacode operations.

Provides enterprise-grade audit trails for security operations, compliance,
and debugging. All logs are structured JSON for easy parsing and analysis.

CRITICAL: All sensitive data (commands, secrets, credentials) are redacted
before writing to audit logs to prevent secret leakage.
"""

import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from qodacode.utils.masking import mask_secrets


@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: float
    action: str
    user: str
    details: Dict[str, Any]
    severity: Optional[str] = None
    result: Optional[str] = None

    def to_json(self) -> str:
        """Convert to JSON string."""
        data = asdict(self)
        data["timestamp_iso"] = datetime.fromtimestamp(self.timestamp).isoformat()
        return json.dumps(data)


class AuditLogger:
    """
    Structured audit logger for security operations.

    Logs all security-relevant operations to .qodacode/audit.jsonl
    in JSON Lines format for easy parsing and streaming.
    """

    def __init__(self, project_root: str = ".", enabled: bool = True):
        """
        Initialize audit logger.

        Args:
            project_root: Path to project root
            enabled: Whether audit logging is enabled
        """
        self.project_root = Path(project_root)
        self.enabled = enabled
        self.log_file = self.project_root / ".qodacode" / "audit.jsonl"

        # Create directory if needed
        if self.enabled:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize sensitive data from details before logging.

        CRITICAL: Prevents secret leakage in audit logs.
        """
        sanitized = {}
        for key, value in details.items():
            if isinstance(value, str):
                # Mask secrets in string values
                sanitized[key] = mask_secrets(value)
            elif isinstance(value, list):
                # Sanitize list items
                sanitized[key] = [
                    mask_secrets(item) if isinstance(item, str) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = self._sanitize_details(value)
            else:
                sanitized[key] = value
        return sanitized

    def _write_entry(self, entry: AuditEntry) -> None:
        """Write entry to audit log with sanitized details."""
        if not self.enabled:
            return

        # Sanitize sensitive data before logging
        entry.details = self._sanitize_details(entry.details)

        try:
            with open(self.log_file, "a") as f:
                f.write(entry.to_json() + "\n")
        except OSError:
            # Fail silently - audit logging shouldn't break operations
            pass

    def log_scan(
        self,
        path: str,
        scan_type: str,
        findings_count: int,
        critical_count: int,
        duration_ms: float,
    ) -> None:
        """
        Log a security scan operation.

        Args:
            path: Path that was scanned
            scan_type: Type of scan (full_audit, quick, deep, secrets, etc.)
            findings_count: Total number of findings
            critical_count: Number of critical findings
            duration_ms: Scan duration in milliseconds
        """
        entry = AuditEntry(
            timestamp=time.time(),
            action="scan",
            user=os.getenv("USER", "unknown"),
            severity="info",
            result="completed",
            details={
                "path": str(path),
                "scan_type": scan_type,
                "findings_count": findings_count,
                "critical_count": critical_count,
                "duration_ms": duration_ms,
            },
        )
        self._write_entry(entry)

    def log_block(
        self,
        tool_name: str,
        reason: str,
        details: Dict[str, Any],
    ) -> None:
        """
        Log a blocked operation (PreToolUse hook).

        Args:
            tool_name: Name of the tool that was blocked
            reason: Reason for blocking
            details: Additional context (command, path, etc.)
        """
        entry = AuditEntry(
            timestamp=time.time(),
            action="block_tool",
            user=os.getenv("USER", "unknown"),
            severity="warning",
            result="blocked",
            details={
                "tool_name": tool_name,
                "reason": reason,
                **details,
            },
        )
        self._write_entry(entry)

    def log_ai_call(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_estimate: Optional[float] = None,
    ) -> None:
        """
        Log an AI API call.

        Args:
            provider: AI provider (anthropic, openai, etc.)
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cost_estimate: Optional estimated cost in USD
        """
        entry = AuditEntry(
            timestamp=time.time(),
            action="ai_call",
            user=os.getenv("USER", "unknown"),
            severity="info",
            result="completed",
            details={
                "provider": provider,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost_estimate_usd": cost_estimate,
            },
        )
        self._write_entry(entry)

    def log_config_change(
        self,
        setting: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """
        Log a configuration change.

        Args:
            setting: Setting that was changed
            old_value: Previous value
            new_value: New value
        """
        entry = AuditEntry(
            timestamp=time.time(),
            action="config_change",
            user=os.getenv("USER", "unknown"),
            severity="info",
            result="updated",
            details={
                "setting": setting,
                "old_value": str(old_value),
                "new_value": str(new_value),
            },
        )
        self._write_entry(entry)

    def log_publish(
        self,
        document_ids: list,
        release_id: Optional[str] = None,
    ) -> None:
        """
        Log a document publish operation.

        Args:
            document_ids: List of document IDs that were published
            release_id: Optional release ID
        """
        entry = AuditEntry(
            timestamp=time.time(),
            action="publish",
            user=os.getenv("USER", "unknown"),
            severity="info",
            result="completed",
            details={
                "document_ids": document_ids,
                "document_count": len(document_ids),
                "release_id": release_id,
            },
        )
        self._write_entry(entry)

    def log_error(
        self,
        operation: str,
        error_type: str,
        error_message: str,
    ) -> None:
        """
        Log an error.

        Args:
            operation: Operation that failed
            error_type: Type of error
            error_message: Error message
        """
        entry = AuditEntry(
            timestamp=time.time(),
            action=operation,
            user=os.getenv("USER", "unknown"),
            severity="error",
            result="failed",
            details={
                "error_type": error_type,
                "error_message": error_message,
            },
        )
        self._write_entry(entry)

    def read_recent(self, limit: int = 100) -> list[Dict[str, Any]]:
        """
        Read recent audit entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of audit entries (most recent first)
        """
        if not self.log_file.exists():
            return []

        try:
            with open(self.log_file) as f:
                lines = f.readlines()

            # Get last N lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines

            # Parse JSON
            entries = []
            for line in reversed(recent_lines):
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

            return entries
        except OSError:
            return []

    def get_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get audit summary for the last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            Summary statistics
        """
        cutoff = time.time() - (hours * 3600)
        entries = self.read_recent(limit=10000)

        # Filter by time
        recent = [e for e in entries if e.get("timestamp", 0) >= cutoff]

        # Count by action
        action_counts = {}
        for entry in recent:
            action = entry.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        # Count blocks
        blocks = [e for e in recent if e.get("action") == "block_tool"]

        # Count errors
        errors = [e for e in recent if e.get("severity") == "error"]

        return {
            "period_hours": hours,
            "total_operations": len(recent),
            "action_counts": action_counts,
            "blocks": len(blocks),
            "errors": len(errors),
            "most_recent": recent[0] if recent else None,
        }

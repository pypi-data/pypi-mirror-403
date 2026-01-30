"""
Rate limiter for Qodacode operations.

Protects users from runaway AI agents causing excessive API costs or resource usage.
Configurable limits with sensible defaults.

IMPORTANT LIMITATIONS:
- Rate limits are PER-INSTANCE/PER-SESSION only (not distributed)
- Multiple terminals or CI jobs running in parallel will each have their own limits
- For distributed rate limiting (e.g., across CI jobs), use external solutions like Redis
- This is designed for individual developer protection, not cluster-wide enforcement
"""

import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    max_scans_per_minute: int = 60
    max_ai_calls_per_minute: int = 30
    enabled: bool = True


class RateLimiter:
    """
    Token bucket rate limiter with configurable limits.

    Protects users from runaway costs when AI agents execute too many operations.
    All limits are configurable in .qodacode/config.json
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter with config.

        Args:
            config: Optional rate limit configuration. If None, uses defaults.
        """
        self.config = config or RateLimitConfig()
        self._scan_timestamps: deque = deque()
        self._ai_timestamps: deque = deque()

    @classmethod
    def from_project(cls, project_root: str = ".") -> "RateLimiter":
        """
        Load rate limiter with project config.

        Args:
            project_root: Path to project root with .qodacode/config.json

        Returns:
            RateLimiter instance with project config or defaults
        """
        config_path = Path(project_root) / ".qodacode" / "config.json"

        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                    rate_config = data.get("rate_limit", {})

                    return cls(RateLimitConfig(
                        max_scans_per_minute=rate_config.get("max_scans_per_minute", 60),
                        max_ai_calls_per_minute=rate_config.get("max_ai_calls_per_minute", 30),
                        enabled=rate_config.get("enabled", True)
                    ))
            except (json.JSONDecodeError, OSError):
                pass

        return cls()

    def _clean_old_timestamps(self, timestamps: deque, window_seconds: int = 60) -> None:
        """Remove timestamps older than the window."""
        now = time.time()
        while timestamps and now - timestamps[0] > window_seconds:
            timestamps.popleft()

    def can_scan(self) -> tuple[bool, Optional[str]]:
        """
        Check if a scan operation is allowed.

        Returns:
            (allowed, reason) tuple. If not allowed, reason explains why.
        """
        if not self.config.enabled:
            return True, None

        self._clean_old_timestamps(self._scan_timestamps)

        if len(self._scan_timestamps) >= self.config.max_scans_per_minute:
            wait_time = 60 - (time.time() - self._scan_timestamps[0])
            return False, f"Rate limit: {self.config.max_scans_per_minute} scans/minute. Wait {wait_time:.0f}s"

        return True, None

    def can_call_ai(self) -> tuple[bool, Optional[str]]:
        """
        Check if an AI API call is allowed.

        Returns:
            (allowed, reason) tuple. If not allowed, reason explains why.
        """
        if not self.config.enabled:
            return True, None

        self._clean_old_timestamps(self._ai_timestamps)

        if len(self._ai_timestamps) >= self.config.max_ai_calls_per_minute:
            wait_time = 60 - (time.time() - self._ai_timestamps[0])
            return False, f"Rate limit: {self.config.max_ai_calls_per_minute} AI calls/minute. Wait {wait_time:.0f}s"

        return True, None

    def record_scan(self) -> None:
        """Record a scan operation."""
        if self.config.enabled:
            self._scan_timestamps.append(time.time())

    def record_ai_call(self) -> None:
        """Record an AI API call."""
        if self.config.enabled:
            self._ai_timestamps.append(time.time())

    def get_current_usage(self) -> dict:
        """
        Get current rate limit usage.

        Returns:
            Dict with current usage stats
        """
        self._clean_old_timestamps(self._scan_timestamps)
        self._clean_old_timestamps(self._ai_timestamps)

        return {
            "scans_last_minute": len(self._scan_timestamps),
            "scans_limit": self.config.max_scans_per_minute,
            "ai_calls_last_minute": len(self._ai_timestamps),
            "ai_calls_limit": self.config.max_ai_calls_per_minute,
            "enabled": self.config.enabled,
        }

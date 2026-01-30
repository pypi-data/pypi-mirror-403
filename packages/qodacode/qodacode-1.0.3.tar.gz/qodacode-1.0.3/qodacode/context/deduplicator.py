"""
Deduplication and suppression logic for Qodacode.

Handles:
- Deduplicating issues from multiple engines
- Engine priority (Gitleaks > Semgrep > OSV > Tree-sitter)
- Persisting and loading suppressions
- Fingerprinting issues for stable identification
- Inline ignore comments (# qodacode-ignore: RULE-ID)
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional, Any, Tuple

from qodacode.models.issue import Issue, EngineSource


# ─────────────────────────────────────────────────────────────────────────────
# INLINE IGNORE COMMENTS
# ─────────────────────────────────────────────────────────────────────────────

# Pattern to match inline ignore comments
# Supports:
#   # qodacode-ignore
#   # qodacode-ignore: SEC-001
#   # qodacode-ignore: SEC-001, SEC-002
#   // qodacode-ignore: SEC-001  (for JS/TS)
IGNORE_PATTERN = re.compile(
    r'(?:#|//)\s*qodacode-ignore(?::\s*([A-Z0-9_,\s-]+))?',
    re.IGNORECASE
)


@dataclass
class InlineIgnore:
    """An inline ignore directive from source code."""
    filepath: str
    line: int
    rule_ids: Set[str]  # Empty set means ignore ALL rules

    def matches(self, rule_id: str) -> bool:
        """Check if this ignore applies to a rule."""
        if not self.rule_ids:
            return True  # Empty = ignore all
        return rule_id.upper() in self.rule_ids


def parse_inline_ignores(filepath: str) -> Dict[int, InlineIgnore]:
    """
    Parse inline ignore comments from a source file.

    Supports two patterns:
    1. Same-line: `code  # qodacode-ignore: RULE-ID`
    2. Line-above: `# qodacode-ignore: RULE-ID` followed by code on next line

    Args:
        filepath: Path to the source file

    Returns:
        Dict mapping line numbers to InlineIgnore objects
    """
    ignores: Dict[int, InlineIgnore] = {}

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except (IOError, OSError):
        return ignores

    pending_ignore: Optional[Tuple[int, Set[str]]] = None

    for i, line in enumerate(lines, start=1):
        match = IGNORE_PATTERN.search(line)

        if match:
            # Parse rule IDs
            rule_ids_str = match.group(1)
            if rule_ids_str:
                rule_ids = {r.strip().upper() for r in rule_ids_str.split(',') if r.strip()}
            else:
                rule_ids = set()  # Ignore all rules

            # Check if this is a comment-only line (ignore applies to next line)
            code_before_comment = line[:match.start()].strip()
            if not code_before_comment:
                # Comment-only line: applies to NEXT line
                pending_ignore = (i + 1, rule_ids)
            else:
                # Same-line comment: applies to THIS line
                ignores[i] = InlineIgnore(filepath=filepath, line=i, rule_ids=rule_ids)

        # Apply pending ignore from line above
        if pending_ignore and pending_ignore[0] == i:
            line_num, rule_ids = pending_ignore
            # Merge if there's already an ignore for this line
            if i in ignores:
                ignores[i].rule_ids.update(rule_ids)
            else:
                ignores[i] = InlineIgnore(filepath=filepath, line=i, rule_ids=rule_ids)
            pending_ignore = None

    return ignores


def is_ignored_by_inline_comment(
    filepath: str,
    line: int,
    rule_id: str,
    ignores_cache: Optional[Dict[str, Dict[int, InlineIgnore]]] = None
) -> bool:
    """
    Check if an issue is ignored by an inline comment.

    Args:
        filepath: Path to the file
        line: Line number of the issue
        rule_id: Rule ID to check
        ignores_cache: Optional cache of parsed ignores per file

    Returns:
        True if the issue should be ignored
    """
    # Use cache if provided
    if ignores_cache is not None:
        if filepath not in ignores_cache:
            ignores_cache[filepath] = parse_inline_ignores(filepath)
        ignores = ignores_cache[filepath]
    else:
        ignores = parse_inline_ignores(filepath)

    if line in ignores:
        return ignores[line].matches(rule_id)

    return False


@dataclass
class IssueFingerprint:
    """
    Stable fingerprint for an issue.

    Used to identify the same issue across runs, even if line numbers shift.
    """
    fingerprint: str
    filepath: str
    rule_id: str
    category: str
    snippet_hash: str

    @classmethod
    def from_issue(cls, issue: Issue) -> "IssueFingerprint":
        """Generate a fingerprint from a Pydantic Issue."""
        # Hash the snippet for content-based matching
        snippet = issue.snippet or ""
        snippet_hash = hashlib.md5(snippet.encode()).hexdigest()[:8]

        # Create a stable fingerprint
        # Uses: filepath + rule_id + snippet_hash
        # This survives line number changes if the code is the same
        filepath = issue.location.filepath
        fp_string = f"{filepath}:{issue.rule_id}:{snippet_hash}"
        fingerprint = hashlib.sha256(fp_string.encode()).hexdigest()[:12]

        return cls(
            fingerprint=fingerprint,
            filepath=filepath,
            rule_id=issue.rule_id,
            category=issue.category.value if hasattr(issue.category, 'value') else str(issue.category),
            snippet_hash=snippet_hash,
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "fingerprint": self.fingerprint,
            "filepath": self.filepath,
            "rule_id": self.rule_id,
            "category": self.category,
            "snippet_hash": self.snippet_hash,
        }


@dataclass
class Suppression:
    """A suppressed issue."""
    fingerprint: str
    reason: str
    suppressed_at: str
    suppressed_by: str
    expires_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "reason": self.reason,
            "suppressed_at": self.suppressed_at,
            "suppressed_by": self.suppressed_by,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Suppression":
        return cls(
            fingerprint=data["fingerprint"],
            reason=data.get("reason", ""),
            suppressed_at=data.get("suppressed_at", ""),
            suppressed_by=data.get("suppressed_by", "user"),
            expires_at=data.get("expires_at"),
        )


class Deduplicator:
    """
    Handles deduplication and suppression of issues.

    Usage:
        dedup = Deduplicator(project_root="/path/to/project")
        unique_issues = dedup.deduplicate(all_issues)
        filtered_issues, fp_count, inline_count = dedup.filter_suppressed(unique_issues)

    Inline ignore comments:
        # qodacode-ignore              (ignore all rules on next line)
        # qodacode-ignore: SEC-001     (ignore specific rule)
        code  # qodacode-ignore        (ignore all rules on this line)
    """

    # Engine priority: lower = higher priority (wins in dedup)
    ENGINE_PRIORITY = {
        EngineSource.GITLEAKS: 0,   # Highest priority
        EngineSource.SEMGREP: 1,
        EngineSource.OSV: 2,
        EngineSource.TREESITTER: 3,  # Lowest priority
    }

    def __init__(self, project_root: str = "."):
        """
        Initialize the deduplicator.

        Args:
            project_root: Root directory of the project (for .qodacode/)
        """
        self.project_root = Path(project_root)
        self.qodacode_dir = self.project_root / ".qodacode"
        self.suppressions_file = self.qodacode_dir / "suppressions.json"
        self._suppressions: Dict[str, Suppression] = {}
        self._load_suppressions()

    def _ensure_qodacode_dir(self) -> None:
        """Ensure .qodacode directory exists."""
        self.qodacode_dir.mkdir(exist_ok=True)

    def _load_suppressions(self) -> None:
        """Load suppressions from disk."""
        if not self.suppressions_file.exists():
            return

        try:
            with open(self.suppressions_file, "r") as f:
                data = json.load(f)

            for item in data.get("suppressions", []):
                supp = Suppression.from_dict(item)
                # Check if expired
                if supp.expires_at:
                    try:
                        expires = datetime.fromisoformat(supp.expires_at)
                        if datetime.now() > expires:
                            continue  # Skip expired
                    except ValueError:
                        pass
                self._suppressions[supp.fingerprint] = supp
        except (json.JSONDecodeError, IOError):
            pass

    def _save_suppressions(self) -> None:
        """Save suppressions to disk."""
        self._ensure_qodacode_dir()

        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "suppressions": [s.to_dict() for s in self._suppressions.values()],
        }

        with open(self.suppressions_file, "w") as f:
            json.dump(data, f, indent=2)

    # Severity priority: higher severity wins in tiebreaker
    SEVERITY_PRIORITY = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
        "INFO": 4,
    }

    def deduplicate(self, issues: List[Issue]) -> List[Issue]:
        """
        Deduplicate issues from multiple engines.

        When the same issue is found by multiple engines, keeps the one
        from the highest-priority engine (Gitleaks > Semgrep > OSV > Tree-sitter).
        If same engine, keeps highest severity.

        Deduplication key: (filepath, line, category)

        Args:
            issues: List of issues from all engines

        Returns:
            Deduplicated list with highest-priority engine + severity preserved
        """
        if not issues:
            return []

        # Sort by: 1) engine priority, 2) severity (tiebreaker)
        # Lower values = higher priority (comes first, wins in dedup)
        def sort_key(issue: Issue):
            engine_priority = self.ENGINE_PRIORITY.get(issue.engine, 99)
            severity_name = issue.severity.name if hasattr(issue.severity, 'name') else str(issue.severity)
            severity_priority = self.SEVERITY_PRIORITY.get(severity_name.upper(), 99)
            return (engine_priority, severity_priority)

        sorted_issues = sorted(issues, key=sort_key)

        # Deduplicate: first occurrence (highest priority) wins
        seen: Set[tuple] = set()
        unique: List[Issue] = []

        for issue in sorted_issues:
            # Pydantic Issue uses location.filepath and location.line
            key = (issue.location.filepath, issue.location.line, issue.category)
            if key not in seen:
                seen.add(key)
                unique.append(issue)

        return unique

    def filter_suppressed(
        self,
        issues: List[Issue],
        check_inline: bool = True
    ) -> Tuple[List[Issue], int, int]:
        """
        Filter out suppressed issues.

        Checks both:
        1. Fingerprint-based suppressions (.qodacode/suppressions.json)
        2. Inline ignore comments (# qodacode-ignore: RULE-ID)

        Args:
            issues: List of issues
            check_inline: Whether to check inline ignore comments

        Returns:
            Tuple of (filtered_issues, fingerprint_suppressed_count, inline_ignored_count)
        """
        filtered: List[Issue] = []
        fingerprint_suppressed = 0
        inline_ignored = 0

        # Cache for inline ignores to avoid re-parsing files
        ignores_cache: Dict[str, Dict[int, InlineIgnore]] = {}

        for issue in issues:
            # Check fingerprint-based suppression first
            fp = IssueFingerprint.from_issue(issue)
            if fp.fingerprint in self._suppressions:
                fingerprint_suppressed += 1
                continue

            # Check inline ignore comments
            if check_inline and is_ignored_by_inline_comment(
                issue.location.filepath,
                issue.location.line,
                issue.rule_id,
                ignores_cache
            ):
                inline_ignored += 1
                continue

            filtered.append(issue)

        return filtered, fingerprint_suppressed, inline_ignored

    def suppress(
        self,
        fingerprint: str,
        reason: str = "",
        expires_in_days: Optional[int] = None,
    ) -> bool:
        """
        Suppress an issue by fingerprint.

        Args:
            fingerprint: Issue fingerprint (12-char hex)
            reason: Why it's being suppressed
            expires_in_days: Auto-expire after N days (None = permanent)

        Returns:
            True if suppressed, False if already suppressed
        """
        if fingerprint in self._suppressions:
            return False

        expires_at = None
        if expires_in_days:
            from datetime import timedelta
            expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()

        self._suppressions[fingerprint] = Suppression(
            fingerprint=fingerprint,
            reason=reason,
            suppressed_at=datetime.now().isoformat(),
            suppressed_by="user",
            expires_at=expires_at,
        )

        self._save_suppressions()
        return True

    def unsuppress(self, fingerprint: str) -> bool:
        """
        Remove a suppression.

        Args:
            fingerprint: Issue fingerprint to unsuppress

        Returns:
            True if removed, False if wasn't suppressed
        """
        if fingerprint not in self._suppressions:
            return False

        del self._suppressions[fingerprint]
        self._save_suppressions()
        return True

    def list_suppressions(self) -> List[Suppression]:
        """List all active suppressions."""
        return list(self._suppressions.values())

    def get_fingerprint(self, issue: Issue) -> str:
        """Get the fingerprint for an issue."""
        return IssueFingerprint.from_issue(issue).fingerprint

    def get_duplicates_removed_count(
        self,
        original_count: int,
        deduplicated_count: int
    ) -> int:
        """Calculate how many duplicates were removed."""
        return original_count - deduplicated_count

    # ─────────────────────────────────────────────────────────────────────────
    # BASELINE MODE
    # ─────────────────────────────────────────────────────────────────────────

    def _get_baseline_path(self) -> Path:
        """Get path to baseline file."""
        return self.qodacode_dir / "baseline.json"

    def save_baseline(self, issues: List[Issue]) -> int:
        """
        Save current issues as baseline.

        Future scans with --baseline will only show NEW issues
        (not in this baseline).

        Args:
            issues: List of issues to save as baseline

        Returns:
            Number of issues saved
        """
        fingerprints = {}
        for issue in issues:
            fp = IssueFingerprint.from_issue(issue)
            fingerprints[fp.fingerprint] = {
                "rule_id": issue.rule_id,
                "filepath": issue.location.filepath,
                "message": issue.message[:100],  # Truncate for readability
            }

        baseline_data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "issue_count": len(fingerprints),
            "fingerprints": fingerprints,
        }

        self.qodacode_dir.mkdir(parents=True, exist_ok=True)

        with open(self._get_baseline_path(), "w") as f:
            json.dump(baseline_data, f, indent=2)

        return len(fingerprints)

    def load_baseline(self) -> Set[str]:
        """
        Load baseline fingerprints.

        Returns:
            Set of fingerprints from baseline
        """
        baseline_path = self._get_baseline_path()

        if not baseline_path.exists():
            return set()

        try:
            with open(baseline_path) as f:
                data = json.load(f)
            return set(data.get("fingerprints", {}).keys())
        except (json.JSONDecodeError, KeyError):
            return set()

    def has_baseline(self) -> bool:
        """Check if a baseline exists."""
        return self._get_baseline_path().exists()

    def get_baseline_info(self) -> Optional[Dict[str, Any]]:
        """Get baseline metadata."""
        baseline_path = self._get_baseline_path()

        if not baseline_path.exists():
            return None

        try:
            with open(baseline_path) as f:
                data = json.load(f)
            return {
                "created_at": data.get("created_at"),
                "issue_count": data.get("issue_count", 0),
            }
        except (json.JSONDecodeError, KeyError):
            return None

    def clear_baseline(self) -> bool:
        """
        Remove baseline.

        Returns:
            True if baseline was removed, False if didn't exist
        """
        baseline_path = self._get_baseline_path()

        if baseline_path.exists():
            baseline_path.unlink()
            return True
        return False

    def filter_baseline(self, issues: List[Issue]) -> Tuple[List[Issue], int]:
        """
        Filter out issues that are in the baseline.

        Args:
            issues: List of issues to filter

        Returns:
            Tuple of (new_issues, baseline_filtered_count)
        """
        baseline_fps = self.load_baseline()

        if not baseline_fps:
            return issues, 0

        new_issues = []
        filtered_count = 0

        for issue in issues:
            fp = IssueFingerprint.from_issue(issue)
            if fp.fingerprint not in baseline_fps:
                new_issues.append(issue)
            else:
                filtered_count += 1

        return new_issues, filtered_count

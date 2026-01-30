"""
Unified Issue Schema (Pydantic).

All engine outputs MUST be normalized to this schema before entering
the processing pipeline. This is the single source of truth for issue
representation in Qodacode.

Reference: docs/PRD_V2_ORCHESTRATOR.md Section 5.1
"""

from datetime import datetime
from enum import Enum
from hashlib import sha256
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Severity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    def __lt__(self, other: "Severity") -> bool:
        """Enable severity comparison."""
        order = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        return order.index(self) < order.index(other)

    def __le__(self, other: "Severity") -> bool:
        return self == other or self < other

    def __gt__(self, other: "Severity") -> bool:
        return not self <= other

    def __ge__(self, other: "Severity") -> bool:
        return not self < other


class Category(str, Enum):
    """Issue categories matching PRD specification."""
    SECURITY = "security"
    ROBUSTNESS = "robustness"
    MAINTAINABILITY = "maintainability"
    OPERABILITY = "operability"
    DEPENDENCIES = "dependencies"


class EngineSource(str, Enum):
    """Source engine that detected the issue."""
    TREESITTER = "tree-sitter"
    SEMGREP = "semgrep"
    GITLEAKS = "gitleaks"
    OSV = "osv"


class Location(BaseModel):
    """
    Code location with line/column precision.

    All line numbers are 1-indexed.
    Column numbers are 0-indexed.
    """
    filepath: str = Field(description="Absolute or relative path to the file")
    line: int = Field(ge=1, description="Starting line number (1-indexed)")
    column: int = Field(ge=0, description="Starting column number (0-indexed)")
    end_line: int = Field(ge=1, description="Ending line number (1-indexed)")
    end_column: int = Field(ge=0, description="Ending column number (0-indexed)")

    @model_validator(mode="after")
    def validate_end_after_start(self) -> "Location":
        """Ensure end position is not before start position."""
        if self.end_line < self.line:
            raise ValueError("end_line cannot be before line")
        if self.end_line == self.line and self.end_column < self.column:
            raise ValueError("end_column cannot be before column on same line")
        return self

    model_config = {"frozen": True}


class Issue(BaseModel):
    """
    Unified issue representation.

    All engine outputs MUST be normalized to this schema
    before entering the processing pipeline.
    """
    # Identity
    id: str = Field(
        default="",
        description="Unique issue ID: {engine}-{rule}-{hash}. Auto-generated if empty."
    )
    rule_id: str = Field(description="Rule identifier (e.g., SEC-001, SG-python-sql)")
    rule_name: str = Field(description="Human-readable rule name")

    # Classification
    severity: Severity
    category: Category
    engine: EngineSource

    # Location
    location: Location

    # Content
    message: str = Field(description="What was found")
    snippet: str = Field(default="", description="Problematic code snippet")

    # Remediation
    fix_suggestion: Optional[str] = Field(default=None, description="How to fix")
    fix_diff: Optional[str] = Field(default=None, description="Suggested patch in diff format")

    # Context
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

    # Metadata
    fingerprint: str = Field(
        default="",
        description="Stable hash for deduplication. Auto-generated if empty."
    )
    first_seen: Optional[datetime] = Field(default=None, description="When first detected")
    suppressed: bool = Field(default=False, description="Whether user suppressed this issue")
    suppression_reason: Optional[str] = Field(default=None, description="Why suppressed")

    @model_validator(mode="after")
    def generate_fingerprint_and_id(self) -> "Issue":
        """Generate fingerprint and ID if not provided."""
        # Generate fingerprint from stable attributes
        if not self.fingerprint:
            fingerprint_input = (
                f"{self.rule_id}:{self.location.filepath}:{self.location.line}:"
                f"{self.location.column}:{self.snippet[:100]}"
            )
            object.__setattr__(
                self,
                "fingerprint",
                sha256(fingerprint_input.encode()).hexdigest()[:16]
            )

        # Generate ID from engine + rule + fingerprint
        if not self.id:
            object.__setattr__(
                self,
                "id",
                f"{self.engine.value}-{self.rule_id}-{self.fingerprint[:8]}"
            )

        return self

    @field_validator("rule_id")
    @classmethod
    def validate_rule_id(cls, v: str) -> str:
        """Ensure rule_id is not empty."""
        if not v or not v.strip():
            raise ValueError("rule_id cannot be empty")
        return v.strip()

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Ensure message is not empty."""
        if not v or not v.strip():
            raise ValueError("message cannot be empty")
        return v.strip()

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format compatible with legacy code.

        Use this for backwards compatibility during migration.
        """
        return {
            "id": self.id,
            "file": self.location.filepath,
            "line": self.location.line,
            "column": self.location.column,
            "end_line": self.location.end_line,
            "end_column": self.location.end_column,
            "rule": {
                "id": self.rule_id,
                "name": self.rule_name,
                "category": self.category.value,
                "severity": self.severity.value,
            },
            "message": self.message,
            "snippet": self.snippet,
            "context": self.context,
            "fix_suggestion": self.fix_suggestion,
        }

    @classmethod
    def from_legacy(
        cls,
        legacy_issue: Any,
        engine: EngineSource = EngineSource.TREESITTER
    ) -> "Issue":
        """
        Create Issue from legacy dataclass Issue.

        Args:
            legacy_issue: Legacy Issue object from qodacode.rules.base
            engine: Source engine (default: tree-sitter for legacy rules)

        Returns:
            Pydantic Issue object
        """
        # Import here to avoid circular dependency
        from qodacode.rules.base import Category as LegacyCategory
        from qodacode.rules.base import Severity as LegacySeverity

        # Map legacy enums to Pydantic enums
        severity_map = {
            LegacySeverity.CRITICAL: Severity.CRITICAL,
            LegacySeverity.HIGH: Severity.HIGH,
            LegacySeverity.MEDIUM: Severity.MEDIUM,
            LegacySeverity.LOW: Severity.LOW,
            LegacySeverity.INFO: Severity.INFO,
        }
        category_map = {
            LegacyCategory.SECURITY: Category.SECURITY,
            LegacyCategory.ROBUSTNESS: Category.ROBUSTNESS,
            LegacyCategory.MAINTAINABILITY: Category.MAINTAINABILITY,
            LegacyCategory.OPERABILITY: Category.OPERABILITY,
            LegacyCategory.DEPENDENCIES: Category.DEPENDENCIES,
        }

        return cls(
            rule_id=legacy_issue.rule_id,
            rule_name=legacy_issue.rule_name,
            severity=severity_map[legacy_issue.severity],
            category=category_map[legacy_issue.category],
            engine=engine,
            location=Location(
                filepath=legacy_issue.filepath,
                line=legacy_issue.line,
                column=legacy_issue.column,
                end_line=legacy_issue.end_line,
                end_column=legacy_issue.end_column,
            ),
            message=legacy_issue.message,
            snippet=legacy_issue.snippet,
            fix_suggestion=legacy_issue.fix_suggestion,
            context=legacy_issue.context,
        )

    model_config = {"use_enum_values": False}


class ScanSummary(BaseModel):
    """Aggregated statistics from a scan."""
    total: int = Field(ge=0, description="Total number of issues found")
    by_severity: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by severity level"
    )
    by_category: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by category"
    )
    by_engine: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by source engine"
    )
    suppressed: int = Field(default=0, ge=0, description="Number of suppressed issues")

    @classmethod
    def from_issues(cls, issues: List[Issue]) -> "ScanSummary":
        """Generate summary from a list of issues."""
        by_severity: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        by_engine: Dict[str, int] = {}
        suppressed = 0

        for issue in issues:
            # Count by severity
            sev = issue.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

            # Count by category
            cat = issue.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            # Count by engine
            eng = issue.engine.value
            by_engine[eng] = by_engine.get(eng, 0) + 1

            # Count suppressed
            if issue.suppressed:
                suppressed += 1

        return cls(
            total=len(issues),
            by_severity=by_severity,
            by_category=by_category,
            by_engine=by_engine,
            suppressed=suppressed,
        )


class ScanMetadata(BaseModel):
    """Scan execution metadata."""
    started_at: datetime = Field(description="When the scan started")
    completed_at: datetime = Field(description="When the scan completed")
    duration_ms: int = Field(ge=0, description="Duration in milliseconds")
    engines_used: List[str] = Field(description="Which engines ran")
    files_scanned: int = Field(ge=0, description="Number of files analyzed")
    lines_scanned: int = Field(ge=0, description="Total lines of code")
    target_path: str = Field(description="Path that was scanned")

    @model_validator(mode="after")
    def validate_times(self) -> "ScanMetadata":
        """Ensure completed_at is not before started_at."""
        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot be before started_at")
        return self


class ScanResult(BaseModel):
    """Complete scan result from orchestrator."""
    issues: List[Issue] = Field(description="All issues found")
    summary: ScanSummary = Field(description="Aggregated statistics")
    metadata: ScanMetadata = Field(description="Execution metadata")

    @classmethod
    def create(
        cls,
        issues: List[Issue],
        metadata: ScanMetadata,
    ) -> "ScanResult":
        """Create ScanResult with auto-generated summary."""
        return cls(
            issues=issues,
            summary=ScanSummary.from_issues(issues),
            metadata=metadata,
        )

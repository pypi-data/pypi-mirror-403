"""
Base classes for Qodacode rules.

Provides the Rule abstract base class, Issue model, severity/category enums,
and a global registry for rule discovery.

Supports Junior/Senior modes for adaptive learning.

NOTE: Issue and enums are now imported from qodacode.models.issue (Pydantic).
This module re-exports them for backwards compatibility.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional, Type
import tree_sitter

# Import unified Pydantic models - single source of truth
from qodacode.models.issue import (
    Issue,
    Location,
    Severity,
    Category,
    EngineSource,
)


class OutputMode(Enum):
    """Output verbosity modes."""
    JUNIOR = "junior"   # Full explanations, examples, learning resources
    SENIOR = "senior"   # Terse, just the facts


@dataclass
class EnterpriseKnowledge:
    """
    Educational content for Junior mode.

    Teaches WHY something matters and what enterprises actually do.
    """
    why_it_matters: str  # Why this issue is important in production
    real_world_impact: str  # Real breach/incident example
    enterprise_patterns: Dict[str, str]  # Company -> What they do
    learn_more: Optional[str] = None  # URL to learn more


class Rule(ABC):
    """
    Abstract base class for all Qodacode rules.

    Each rule must implement:
    - id: Unique identifier (e.g., "SEC-001")
    - name: Human-readable name (e.g., "hardcoded-secret")
    - description: What the rule detects
    - severity: Default severity level
    - category: Rule category
    - languages: List of supported languages
    - check(): The detection logic

    Optional (for Junior mode):
    - enterprise_knowledge: Educational content about why this matters
    """

    # Class attributes to be defined by subclasses
    id: str
    name: str
    description: str
    severity: Severity
    category: Category
    languages: List[str]

    # Optional: Educational content for Junior mode
    enterprise_knowledge: Optional[EnterpriseKnowledge] = None

    def __init_subclass__(cls, **kwargs):
        """Auto-register rules when they're defined."""
        super().__init_subclass__(**kwargs)
        # Only register concrete implementations (not abstract subclasses)
        if not getattr(cls, "__abstractmethods__", None):
            RuleRegistry.register(cls)

    @abstractmethod
    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        """
        Check the given AST for issues.

        Args:
            tree: Parsed Tree-sitter AST
            source: Original source code as bytes
            filepath: Path to the source file

        Returns:
            List of Issue objects for any problems found
        """
        pass

    def create_issue(
        self,
        filepath: str,
        node: tree_sitter.Node,
        source: bytes,
        message: str,
        fix_suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Issue:
        """
        Helper to create an Issue from a Tree-sitter node.

        Args:
            filepath: Path to the source file
            node: Tree-sitter node where the issue was found
            source: Original source code as bytes
            message: Human-readable issue description
            fix_suggestion: Optional fix suggestion
            context: Optional additional context

        Returns:
            Configured Pydantic Issue object
        """
        # Extract snippet (the problematic code)
        snippet = source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

        return Issue(
            rule_id=self.id,
            rule_name=self.name,
            category=self.category,
            severity=self.severity,
            engine=EngineSource.TREESITTER,
            location=Location(
                filepath=filepath,
                line=node.start_point[0] + 1,  # Convert to 1-indexed
                column=node.start_point[1],
                end_line=node.end_point[0] + 1,
                end_column=node.end_point[1],
            ),
            message=message,
            snippet=snippet,
            context=context or {},
            fix_suggestion=fix_suggestion,
        )

    def get_node_text(self, node: tree_sitter.Node, source: bytes) -> str:
        """Extract text content from a Tree-sitter node."""
        return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    def find_parent_function(self, node: tree_sitter.Node) -> Optional[str]:
        """Find the name of the enclosing function, if any."""
        current = node.parent
        while current:
            if current.type in ("function_definition", "method_definition"):
                name_node = current.child_by_field_name("name")
                if name_node:
                    return name_node.text.decode("utf-8", errors="replace")
            current = current.parent
        return None

    def find_parent_class(self, node: tree_sitter.Node) -> Optional[str]:
        """Find the name of the enclosing class, if any."""
        current = node.parent
        while current:
            if current.type == "class_definition":
                name_node = current.child_by_field_name("name")
                if name_node:
                    return name_node.text.decode("utf-8", errors="replace")
            current = current.parent
        return None


class RuleRegistry:
    """
    Global registry for all rules.

    Rules are auto-registered when their class is defined (via __init_subclass__).
    """
    _rules: Dict[str, Type[Rule]] = {}
    _instances: Dict[str, Rule] = {}

    @classmethod
    def register(cls, rule_class: Type[Rule]) -> None:
        """Register a rule class."""
        if hasattr(rule_class, "id"):
            cls._rules[rule_class.id] = rule_class

    @classmethod
    def get(cls, rule_id: str) -> Optional[Rule]:
        """Get a rule instance by ID."""
        if rule_id not in cls._instances:
            if rule_id in cls._rules:
                cls._instances[rule_id] = cls._rules[rule_id]()
        return cls._instances.get(rule_id)

    @classmethod
    def get_all(cls) -> List[Rule]:
        """Get instances of all registered rules."""
        for rule_id in cls._rules:
            if rule_id not in cls._instances:
                cls._instances[rule_id] = cls._rules[rule_id]()
        return list(cls._instances.values())

    @classmethod
    def get_by_category(cls, category: Category) -> List[Rule]:
        """Get all rules in a specific category."""
        return [r for r in cls.get_all() if r.category == category]

    @classmethod
    def get_by_language(cls, language: str) -> List[Rule]:
        """Get all rules that support a specific language."""
        return [r for r in cls.get_all() if language in r.languages]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered rules (mainly for testing)."""
        cls._rules.clear()
        cls._instances.clear()

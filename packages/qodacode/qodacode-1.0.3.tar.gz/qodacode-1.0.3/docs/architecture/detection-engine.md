# Detection Engine Architecture

**Document**: Phase 0 - Research
**Projects analyzed**: Semgrep, Bandit
**Goal**: Extract patterns for Qodacode's detection engine

---

## 1. Executive Summary

This document extracts architectural patterns from Semgrep and Bandit to design Qodacode's detection engine.

**Qodacode will adopt**:
- Declarative rule system (inspired by Semgrep YAML)
- Plugin architecture (inspired by Bandit)
- Pattern matching on AST (both)
- Key differentiator: **cross-file context via persistent memory**

---

## 2. Semgrep Analysis

### 2.1 General Architecture

- **Core language**: OCaml (78%) + Python (18%)
- **Performance**: "Code scanning at ludicrous speed" - local analysis without network overhead
- **Scope**: 30+ languages, 20,000+ rules in registry

### 2.2 Rule Structure (YAML)

```yaml
rules:
  - id: unique-rule-identifier
    languages: [python, javascript]
    severity: HIGH  # LOW, MEDIUM, HIGH, CRITICAL
    message: "Problem description and how to fix it"

    # Pattern matching (one required)
    pattern: dangerous_function($ARG)
    # Or multiple patterns
    patterns:
      - pattern: sql_query($USER_INPUT)
      - pattern-not: sql_query(sanitize($USER_INPUT))

    # Optional metadata
    metadata:
      category: security
      cwe: CWE-89
      confidence: HIGH

    # Optional autofix
    fix: safe_function($ARG)
```

### 2.3 Pattern Operators

| Operator | Function | Use in Qodacode |
|----------|----------|-----------------|
| `pattern` | Exact match | Yes - detection base |
| `patterns` | Logical AND | Yes - combine conditions |
| `pattern-either` | Logical OR | Yes - alternatives |
| `pattern-not` | Exclude matches | Yes - reduce false positives |
| `pattern-inside` | Match within context | Yes - function/class scope |
| `pattern-not-inside` | Exclude by context | Yes - ignore tests |
| `metavariable-regex` | Filter by regex | Evaluate - may be overkill |
| `metavariable-comparison` | Compare values | Not initially |
| `focus-metavariable` | Specific highlight | Not initially |

### 2.4 Metavariables

Semgrep uses `$VAR` to capture code parts:

```yaml
# Capture any argument
pattern: print($X)

# Capture multiple arguments
pattern: func($...ARGS)

# Capture with specific type
pattern: (string $S)
```

### 2.5 Lessons for Qodacode

| What Semgrep does well | How we adopt it |
|------------------------|-----------------|
| Rules that look like code | Our rules use similar AST patterns |
| Declarative YAML | We adopt similar but simplified format |
| Clear severity | Same 4 levels: LOW, MEDIUM, HIGH, CRITICAL |
| Extensible metadata | Same: category, cwe, confidence |

| What Semgrep DOESN'T do | Qodacode adds |
|-------------------------|---------------|
| Memory between runs | `.qodacode/` persists index |
| Deep cross-file context | Vector DB with relationships |
| AI explanation | MCP Server + Claude |

---

## 3. Bandit Analysis

### 3.1 General Architecture

- **Language**: Pure Python
- **Parsing**: Python's standard `ast` module
- **Architecture**: Plugin-based

### 3.2 Execution Flow

```
1. Parse Python file → AST
        ↓
2. Traverse AST node by node
        ↓
3. For each node, run relevant plugins
        ↓
4. Plugin returns: issue or nothing
        ↓
5. Add issues to report
```

### 3.3 Plugin Structure

```python
# Simplified Bandit plugin example
import bandit
from bandit.core import issue

def check_hardcoded_password(context):
    """Detect hardcoded passwords."""
    node = context.node

    if isinstance(node, ast.Assign):
        for target in node.targets:
            if hasattr(target, 'id'):
                name = target.id.lower()
                if 'password' in name or 'secret' in name:
                    if isinstance(node.value, ast.Str):
                        return bandit.Issue(
                            severity=bandit.HIGH,
                            confidence=bandit.MEDIUM,
                            text="Hardcoded password detected"
                        )
    return None
```

### 3.4 Check Categories

Bandit organizes checks by vulnerability type:
- **B1xx**: Dangerous imports (pickle, telnetlib)
- **B2xx**: Dangerous functions (exec, eval)
- **B3xx**: Call blacklists
- **B4xx**: SSL security
- **B5xx**: Weak cryptography
- **B6xx**: Injection (SQL, shell, YAML)
- **B7xx**: XSS

### 3.5 Lessons for Qodacode

| What Bandit does well | How we adopt it |
|----------------------|-----------------|
| Plugin architecture | Modular rule system |
| AST-based detection | Tree-sitter AST (multi-language) |
| Clear categories | SEC, ROB, MNT, OPS |
| Confidence levels | HIGH, MEDIUM, LOW |

| What Bandit DOESN'T do | Qodacode adds |
|------------------------|---------------|
| Only Python | Multi-language via Tree-sitter |
| No cross-file context | Persistent memory |
| No explanation | Contextual AI |

---

## 4. Proposed Architecture for Qodacode

### 4.1 Engine Structure

```
qodacode/rules/
├── __init__.py         # Rule registry
├── base.py             # Base Rule class
├── security.py         # SEC-001 to SEC-006
├── robustness.py       # ROB-001 to ROB-005
├── maintainability.py  # MNT-001 to MNT-005
└── operability.py      # OPS-001 to OPS-005
```

### 4.2 Base Rule Class

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import tree_sitter

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Category(Enum):
    SECURITY = "security"
    ROBUSTNESS = "robustness"
    MAINTAINABILITY = "maintainability"
    OPERABILITY = "operability"

@dataclass
class Issue:
    rule_id: str
    file: str
    line: int
    column: int
    end_line: int
    end_column: int
    message: str
    severity: Severity
    category: Category
    snippet: str
    fix_suggestion: Optional[str] = None

class Rule(ABC):
    """Base class for all detection rules."""

    id: str                    # e.g.: "SEC-001"
    name: str                  # e.g.: "hardcoded-secret"
    description: str           # Long description
    severity: Severity
    category: Category
    languages: List[str]       # e.g.: ["python", "javascript"]

    @abstractmethod
    def check(self, tree: tree_sitter.Tree, source: bytes, filepath: str) -> List[Issue]:
        """
        Run rule against an AST.

        Args:
            tree: Tree-sitter AST
            source: Source code as bytes
            filepath: File path

        Returns:
            List of issues found
        """
        pass

    def get_node_text(self, node: tree_sitter.Node, source: bytes) -> str:
        """Helper to extract text from a node."""
        return source[node.start_byte:node.end_byte].decode('utf-8')
```

### 4.3 Rule Example: SEC-001 (Hardcoded Secret)

```python
import re
from typing import List
from .base import Rule, Issue, Severity, Category

class HardcodedSecretRule(Rule):
    id = "SEC-001"
    name = "hardcoded-secret"
    description = "Detects hardcoded secrets in code"
    severity = Severity.CRITICAL
    category = Category.SECURITY
    languages = ["python", "javascript", "typescript"]

    # Suspicious name patterns
    SECRET_PATTERNS = [
        r'(?i)(password|passwd|pwd)',
        r'(?i)(secret|api_key|apikey)',
        r'(?i)(token|auth|credential)',
        r'(?i)(private_key|privatekey)',
    ]

    # Tree-sitter query for Python
    PYTHON_QUERY = """
    (assignment
      left: (identifier) @name
      right: (string) @value
    )
    """

    def check(self, tree, source: bytes, filepath: str) -> List[Issue]:
        issues = []

        # Use Tree-sitter query
        query = tree.language.query(self.PYTHON_QUERY)
        captures = query.captures(tree.root_node)

        # Group by assignment
        assignments = {}
        for node, name in captures:
            # Grouping logic...
            pass

        for name_node, value_node in assignments.items():
            var_name = self.get_node_text(name_node, source)

            # Check if name is suspicious
            for pattern in self.SECRET_PATTERNS:
                if re.match(pattern, var_name):
                    value = self.get_node_text(value_node, source)

                    # Ignore placeholder values
                    if self._is_placeholder(value):
                        continue

                    issues.append(Issue(
                        rule_id=self.id,
                        file=filepath,
                        line=name_node.start_point[0] + 1,
                        column=name_node.start_point[1],
                        end_line=value_node.end_point[0] + 1,
                        end_column=value_node.end_point[1],
                        message=f"Variable '{var_name}' contains a string literal that appears to be a secret",
                        severity=self.severity,
                        category=self.category,
                        snippet=f"{var_name} = {value}",
                        fix_suggestion=f"Use environment variable: {var_name} = os.environ['{var_name.upper()}']"
                    ))
                    break

        return issues

    def _is_placeholder(self, value: str) -> bool:
        """Ignore values that are clearly placeholders."""
        placeholders = ['""', "''", 'None', 'null', 'TODO', 'CHANGEME', 'xxx', '***']
        return value.strip('"\'').lower() in [p.lower() for p in placeholders]
```

### 4.4 Rule Registry

```python
# qodacode/rules/__init__.py
from typing import Dict, List, Type
from .base import Rule, Category

# Import all rules
from .security import (
    HardcodedSecretRule,
    SQLInjectionRule,
    CommandInjectionRule,
    XSSVulnerabilityRule,
    NoAuthEndpointRule,
    CVEDependencyRule,
)
from .robustness import (
    NoErrorHandlingRule,
    NoTimeoutRule,
    NoRetryLogicRule,
    RaceConditionRule,
    UnvalidatedInputRule,
)
from .maintainability import (
    CodeDuplicationRule,
    LongFunctionRule,
    CircularImportRule,
    DeadCodeRule,
    HighComplexityRule,
)
from .operability import (
    NoLoggingRule,
    HardcodedConfigRule,
    NoHealthCheckRule,
    BadDockerfileRule,
    NoGracefulShutdownRule,
)

# Global registry
RULES: Dict[str, Type[Rule]] = {}

def register_rule(rule_class: Type[Rule]):
    """Register a rule in the global registry."""
    RULES[rule_class.id] = rule_class
    return rule_class

def get_rules_by_category(category: Category) -> List[Type[Rule]]:
    """Get all rules of a category."""
    return [r for r in RULES.values() if r.category == category]

def get_rules_by_language(language: str) -> List[Type[Rule]]:
    """Get all rules that support a language."""
    return [r for r in RULES.values() if language in r.languages]

def get_all_rules() -> List[Type[Rule]]:
    """Get all registered rules."""
    return list(RULES.values())
```

### 4.5 Main Detection Engine

```python
# qodacode/scanner.py
from typing import List, Optional
from pathlib import Path
import tree_sitter
from .rules import get_rules_by_language
from .rules.base import Issue

class Scanner:
    """Main detection engine."""

    def __init__(self):
        self.parsers = {}  # Parser cache by language
        self._init_parsers()

    def _init_parsers(self):
        """Initialize Tree-sitter parsers."""
        import tree_sitter_python
        self.parsers['python'] = tree_sitter.Parser()
        self.parsers['python'].language = tree_sitter.Language(tree_sitter_python.language())
        # ... etc

    def detect_language(self, filepath: str) -> Optional[str]:
        """Detect language by extension."""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
        }
        ext = Path(filepath).suffix.lower()
        return ext_map.get(ext)

    def scan_file(self, filepath: str) -> List[Issue]:
        """Scan a file and return issues."""
        language = self.detect_language(filepath)
        if not language or language not in self.parsers:
            return []

        with open(filepath, 'rb') as f:
            source = f.read()

        parser = self.parsers[language]
        tree = parser.parse(source)

        issues = []
        rules = get_rules_by_language(language)

        for rule_class in rules:
            rule = rule_class()
            rule_issues = rule.check(tree, source, filepath)
            issues.extend(rule_issues)

        return issues
```

---

## 5. Design Decisions

### 5.1 Why we DON'T copy Semgrep's YAML

| Semgrep YAML | Qodacode Python |
|--------------|-----------------|
| More declarative | More flexible |
| Requires custom parser | Standard Python |
| Less AST control | Full control |
| Hard to debug | Debuggable |

**Decision**: Rules in pure Python using Tree-sitter queries, not custom YAML.

### 5.2 Why we adopt Bandit's pattern

- Proven and simple architecture
- Easy to add new rules
- Each rule is self-contained
- Straightforward testing

### 5.3 Qodacode's Differentiator

```
Semgrep/Bandit: File → AST → Rules → Issues
                         ↓
                   (no memory)

Qodacode:        File → AST → Rules → Issues
                         ↓          ↓
                      Memory ← Cross-file context
                         ↓
                   AI explains with context
```

---

## 6. Implementation Plan

### Phase 1 - MVP (15-20 rules)

| Priority | Rule | Complexity |
|----------|------|------------|
| 1 | SEC-001 hardcoded-secret | Low |
| 2 | SEC-002 sql-injection | Medium |
| 3 | ROB-001 no-error-handling | Low |
| 4 | ROB-002 no-timeout | Low |
| 5 | OPS-002 hardcoded-config | Low |
| 6 | MNT-002 long-function | Low |
| 7 | SEC-003 command-injection | Medium |
| 8 | SEC-004 xss-vulnerability | Medium |
| 9 | MNT-003 circular-import | High (cross-file) |
| 10 | OPS-001 no-logging | Medium |

### Tree-sitter Queries to Develop

```
# Base queries needed for MVP

# Assignments
(assignment left: (identifier) @name right: (_) @value)

# Function calls
(call function: (identifier) @func arguments: (_) @args)

# Function definitions
(function_definition name: (identifier) @name parameters: (_) @params body: (_) @body)

# String literals
(string) @string

# Imports
(import_statement) @import
(import_from_statement) @import_from
```

---

## 7. Success Metrics

| Metric | Target |
|--------|--------|
| Precision (true positives / total positives) | > 90% |
| Scan time 10K loc | < 5 seconds |
| Rules implemented | 15-20 |
| Languages supported | Python, JS, TS |

---

## 8. References

- [Semgrep GitHub](https://github.com/semgrep/semgrep)
- [Semgrep Rule Syntax](https://semgrep.dev/docs/writing-rules/rule-syntax)
- [Bandit GitHub](https://github.com/PyCQA/bandit)
- [Tree-sitter Queries](https://tree-sitter.github.io/tree-sitter/using-parsers#pattern-matching-with-queries)

---

**Document completed**: Phase 0 - Detection Engine
**Next**: parsing.md (Tree-sitter + Ruff)

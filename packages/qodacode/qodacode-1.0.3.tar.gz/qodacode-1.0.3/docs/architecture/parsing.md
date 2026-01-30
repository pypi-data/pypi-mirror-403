# Parsing Architecture

**Document**: Phase 0 - Research
**Projects analyzed**: Tree-sitter, Ruff
**Goal**: Define Qodacode's parsing layer

---

## 1. Executive Summary

Tree-sitter is the chosen parser for Qodacode. This document details how to integrate it and what performance lessons we extract from Ruff.

**Key decisions**:
- Tree-sitter for multi-language parsing
- Queries for pattern matching (not manual traversal)
- AST caching for performance
- Incremental parsing for watch mode

---

## 2. Tree-sitter Analysis

### 2.1 Why Tree-sitter

| Feature | Benefit for Qodacode |
|---------|---------------------|
| **Incremental parsing** | Only re-parses what changed - critical for watch mode |
| **Error recovery** | Generates useful AST even with syntax errors |
| **Multi-language** | One API for Python, JS, TS, Go, Rust, Java |
| **Speed** | Milliseconds per file, can parse on every keystroke |
| **C core** | Native performance, Python bindings available |

### 2.2 Installation

```bash
# Core library
pip install tree-sitter

# Per-language parsers
pip install tree-sitter-python
pip install tree-sitter-javascript
pip install tree-sitter-typescript
```

### 2.3 Basic Usage

```python
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

# Create parser
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

# Parse code
source = b'''
def hello(name):
    print(f"Hello, {name}!")
'''
tree = parser.parse(source)

# Access AST
root = tree.root_node
print(root.type)  # "module"
print(root.child_count)  # 1
```

### 2.4 AST Navigation

```python
# Method 1: Direct child access
for child in root.children:
    print(child.type, child.start_point, child.end_point)

# Method 2: TreeCursor (more efficient for large trees)
cursor = tree.walk()
cursor.goto_first_child()
while True:
    print(cursor.node.type)
    if not cursor.goto_next_sibling():
        break
```

### 2.5 Queries (Pattern Matching)

Queries are the preferred method for finding patterns in the AST.

```python
from tree_sitter import Query

# Query to find all functions
query = PY_LANGUAGE.query("""
(function_definition
  name: (identifier) @func_name
  parameters: (parameters) @params
  body: (block) @body
)
""")

# Execute query
captures = query.captures(tree.root_node)
for node, name in captures:
    print(f"{name}: {node.text.decode()}")
```

### 2.6 Query Syntax

| Pattern | Description | Example |
|---------|-------------|---------|
| `(node_type)` | Match by type | `(function_definition)` |
| `field: (child)` | Match by field | `name: (identifier)` |
| `@capture` | Capture node | `@func_name` |
| `(_)` | Any node | `arguments: (_)` |
| `"literal"` | Literal match | `"def"` |
| `#match?` | Regex predicate | `(#match? @name "^test_")` |

### 2.7 Common Queries for Qodacode

```python
# Assignments (for detecting hardcoded secrets)
ASSIGNMENT_QUERY = """
(assignment
  left: (identifier) @var_name
  right: (string) @value
)
"""

# Function calls (for detecting dangerous calls)
CALL_QUERY = """
(call
  function: (identifier) @func_name
  arguments: (argument_list) @args
)
"""

# Function definitions (for complexity analysis)
FUNCTION_QUERY = """
(function_definition
  name: (identifier) @name
  parameters: (parameters) @params
  body: (block) @body
)
"""

# Imports (for detecting dangerous imports)
IMPORT_QUERY = """
[
  (import_statement
    name: (dotted_name) @module)
  (import_from_statement
    module_name: (dotted_name) @module
    name: (dotted_name) @name)
]
"""

# Try/except (for verifying error handling)
TRY_QUERY = """
(try_statement
  body: (block) @try_body
  (except_clause) @except
)
"""

# String literals (for finding secrets)
STRING_QUERY = """
(string) @string_value
"""
```

---

## 3. Ruff Analysis (Performance Lessons)

### 3.1 How Ruff achieves 10-100x speed

| Technique | Application in Qodacode |
|-----------|------------------------|
| **Rust (compiled)** | Not applicable - we use Python, but Tree-sitter is C |
| **Parallelization** | Yes - multiprocessing for directory scans |
| **Caching** | Yes - AST cache in `.qodacode/` |
| **Single-pass** | Yes - all rules in one AST pass |
| **Minimal I/O** | Yes - only read modified files |

### 3.2 Ruff Patterns to Adopt

**1. Rule organization by prefix**
```
SEC-xxx: Security
ROB-xxx: Robustness
MNT-xxx: Maintainability
OPS-xxx: Operability
```

**2. Flexible configuration**
```toml
# qodacode.toml
[rules]
enable = ["SEC-*", "ROB-001", "ROB-002"]
disable = ["MNT-004"]

[rules.SEC-001]
ignore_patterns = ["test_*.py"]
```

**3. Batch processing**
- Process multiple files in parallel
- Consolidate results at the end

### 3.3 What we DON'T adopt from Ruff

| Ruff does | Qodacode doesn't do |
|-----------|---------------------|
| Rewritten in Rust | Python + Tree-sitter (sufficient performance) |
| 800+ rules | 20 focused rules |
| Includes formatter | No - detection only |

---

## 4. Scanner Architecture

### 4.1 Module Structure

```
qodacode/
├── scanner.py          # Main module
├── parsers/
│   ├── __init__.py     # Parser factory
│   ├── base.py         # Base class
│   └── queries.py      # Common queries
└── cache/
    ├── __init__.py
    └── ast_cache.py    # AST cache
```

### 4.2 Scanner Implementation

```python
# qodacode/scanner.py
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ProcessPoolExecutor
import tree_sitter

from .parsers import get_parser, get_language
from .cache import ASTCache
from .rules import get_rules_by_language
from .rules.base import Issue

class Scanner:
    """Parsing and detection engine."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache = ASTCache(cache_dir) if cache_dir else None
        self._parsers: Dict[str, tree_sitter.Parser] = {}

    def get_parser(self, language: str) -> tree_sitter.Parser:
        """Get or create parser for a language."""
        if language not in self._parsers:
            lang = get_language(language)
            parser = tree_sitter.Parser(lang)
            self._parsers[language] = parser
        return self._parsers[language]

    def parse_file(self, filepath: str) -> Optional[tree_sitter.Tree]:
        """Parse a file, using cache if available."""
        path = Path(filepath)
        language = self._detect_language(path)
        if not language:
            return None

        # Check cache
        if self.cache:
            cached = self.cache.get(filepath)
            if cached:
                return cached

        # Parse
        with open(filepath, 'rb') as f:
            source = f.read()

        parser = self.get_parser(language)
        tree = parser.parse(source)

        # Save to cache
        if self.cache:
            self.cache.set(filepath, tree)

        return tree

    def scan_file(self, filepath: str) -> List[Issue]:
        """Scan a file and return issues."""
        path = Path(filepath)
        language = self._detect_language(path)

        if not language:
            return []

        with open(filepath, 'rb') as f:
            source = f.read()

        tree = self.parse_file(filepath)
        if not tree:
            return []

        issues = []
        rules = get_rules_by_language(language)

        for rule_class in rules:
            rule = rule_class()
            rule_issues = rule.check(tree, source, filepath)
            issues.extend(rule_issues)

        return issues

    def scan_directory(
        self,
        directory: str,
        exclude: List[str] = None,
        parallel: bool = True
    ) -> List[Issue]:
        """Scan directory, optionally in parallel."""
        exclude = exclude or ['.git', 'node_modules', '__pycache__', '.qodacode', 'venv']
        files = self._find_files(directory, exclude)

        if parallel and len(files) > 10:
            return self._scan_parallel(files)
        else:
            return self._scan_sequential(files)

    def _scan_parallel(self, files: List[str]) -> List[Issue]:
        """Scan files in parallel."""
        all_issues = []
        with ProcessPoolExecutor() as executor:
            results = executor.map(self.scan_file, files)
            for issues in results:
                all_issues.extend(issues)
        return all_issues

    def _scan_sequential(self, files: List[str]) -> List[Issue]:
        """Scan files sequentially."""
        all_issues = []
        for filepath in files:
            issues = self.scan_file(filepath)
            all_issues.extend(issues)
        return all_issues

    def _find_files(self, directory: str, exclude: List[str]) -> List[str]:
        """Find files to scan."""
        files = []
        for path in Path(directory).rglob('*'):
            if path.is_file() and not any(ex in str(path) for ex in exclude):
                if self._detect_language(path):
                    files.append(str(path))
        return files

    def _detect_language(self, path: Path) -> Optional[str]:
        """Detect language by extension."""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
        }
        return ext_map.get(path.suffix.lower())
```

### 4.3 AST Cache

```python
# qodacode/cache/ast_cache.py
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict
import tree_sitter

class ASTCache:
    """Cache for parsed ASTs."""

    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir) / 'ast'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index: Dict[str, str] = self._load_index()

    def _load_index(self) -> Dict[str, str]:
        """Load cache index."""
        index_file = self.cache_dir / 'index.json'
        if index_file.exists():
            return json.loads(index_file.read_text())
        return {}

    def _save_index(self):
        """Save cache index."""
        index_file = self.cache_dir / 'index.json'
        index_file.write_text(json.dumps(self._index, indent=2))

    def _file_hash(self, filepath: str) -> str:
        """Calculate file hash."""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def get(self, filepath: str) -> Optional[tree_sitter.Tree]:
        """Get cached AST if valid."""
        if filepath not in self._index:
            return None

        current_hash = self._file_hash(filepath)
        if self._index[filepath] != current_hash:
            return None

        return None  # For now, only use hash check

    def set(self, filepath: str, tree: tree_sitter.Tree):
        """Save reference to cached AST."""
        file_hash = self._file_hash(filepath)
        self._index[filepath] = file_hash
        self._save_index()

    def invalidate(self, filepath: str):
        """Invalidate cache for a file."""
        if filepath in self._index:
            del self._index[filepath]
            self._save_index()

    def clear(self):
        """Clear all cache."""
        self._index = {}
        self._save_index()
```

### 4.4 Parser Factory

```python
# qodacode/parsers/__init__.py
from typing import Dict
import tree_sitter
from tree_sitter import Language

_languages: Dict[str, Language] = {}

def get_language(name: str) -> Language:
    """Get Language object for a language."""
    if name not in _languages:
        if name == 'python':
            import tree_sitter_python as tsp
            _languages[name] = Language(tsp.language())
        elif name == 'javascript':
            import tree_sitter_javascript as tsjs
            _languages[name] = Language(tsjs.language())
        elif name == 'typescript':
            import tree_sitter_typescript as tsts
            _languages[name] = Language(tsts.language_typescript())
        else:
            raise ValueError(f"Unsupported language: {name}")
    return _languages[name]

def get_parser(language: str) -> tree_sitter.Parser:
    """Create parser for a language."""
    lang = get_language(language)
    return tree_sitter.Parser(lang)
```

---

## 5. Performance Optimizations

### 5.1 Implemented Strategies

| Strategy | Implementation |
|----------|----------------|
| **AST Cache** | Hash-based invalidation |
| **Parallelization** | ProcessPoolExecutor for dir scans |
| **Efficient queries** | One query per rule type, not traversal |
| **Lazy loading** | Parsers created on demand |
| **File filtering** | Early exclusion by extension |

### 5.2 Target Benchmarks

| Operation | Target | Justification |
|-----------|--------|---------------|
| Parse single file | < 50ms | Tree-sitter is typically < 10ms |
| Scan 10K loc | < 5s | With parallelization |
| Watch mode detect | < 1s | Only modified file |
| Init 100K loc | < 60s | With initial cache |

### 5.3 Incremental Parsing (Watch Mode)

```python
# For watch mode, use incremental editing API
def update_tree(old_tree, source, edit):
    """Update tree with incremental edit."""
    old_tree.edit(
        start_byte=edit['start_byte'],
        old_end_byte=edit['old_end_byte'],
        new_end_byte=edit['new_end_byte'],
        start_point=edit['start_point'],
        old_end_point=edit['old_end_point'],
        new_end_point=edit['new_end_point'],
    )
    return parser.parse(source, old_tree)
```

---

## 6. Node Types by Language

### 6.1 Python

```
module
├── function_definition
│   ├── name: identifier
│   ├── parameters: parameters
│   └── body: block
├── class_definition
│   ├── name: identifier
│   └── body: block
├── assignment
│   ├── left: identifier | pattern
│   └── right: expression
├── call
│   ├── function: identifier | attribute
│   └── arguments: argument_list
├── import_statement
│   └── name: dotted_name
└── import_from_statement
    ├── module_name: dotted_name
    └── name: dotted_name
```

### 6.2 JavaScript/TypeScript

```
program
├── function_declaration
│   ├── name: identifier
│   ├── parameters: formal_parameters
│   └── body: statement_block
├── class_declaration
│   ├── name: identifier
│   └── body: class_body
├── variable_declaration
│   └── variable_declarator
│       ├── name: identifier
│       └── value: expression
├── call_expression
│   ├── function: identifier | member_expression
│   └── arguments: arguments
└── import_statement
    └── import_clause
```

---

## 7. Success Metrics

| Metric | Target |
|--------|--------|
| Parse time per file | < 50ms |
| Scan time 10K loc | < 5s |
| Memory per file | < 10MB |
| MVP languages supported | Python, JS, TS |

---

## 8. References

- [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [py-tree-sitter GitHub](https://github.com/tree-sitter/py-tree-sitter)
- [Ruff GitHub](https://github.com/astral-sh/ruff)
- [Tree-sitter Playground](https://tree-sitter.github.io/tree-sitter/playground)

---

**Document completed**: Phase 0 - Parsing
**Next**: memory-system.md (Mem0 + Code-Graph-RAG)

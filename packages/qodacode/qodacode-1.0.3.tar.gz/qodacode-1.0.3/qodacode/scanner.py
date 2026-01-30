"""
Qodacode Scanner - Tree-sitter based code parser and analyzer.

Handles multi-language parsing with caching, parallel processing,
and rule execution.
"""

import hashlib
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import tree_sitter
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript

from qodacode.rules.base import Issue, Rule, RuleRegistry, Category, Severity
from qodacode.models.issue import Location, EngineSource
from qodacode.cache import ScanCache


# Language configuration
LANGUAGE_CONFIG = {
    ".py": {
        "name": "python",
        "language": tree_sitter.Language(tree_sitter_python.language()),
    },
    ".js": {
        "name": "javascript",
        "language": tree_sitter.Language(tree_sitter_javascript.language()),
    },
    ".jsx": {
        "name": "javascript",
        "language": tree_sitter.Language(tree_sitter_javascript.language()),
    },
    ".ts": {
        "name": "typescript",
        "language": tree_sitter.Language(tree_sitter_typescript.language_typescript()),
    },
    ".tsx": {
        "name": "typescript",
        "language": tree_sitter.Language(tree_sitter_typescript.language_tsx()),
    },
}

# Default patterns to exclude
DEFAULT_EXCLUDE = {
    # Directories
    ".git",
    ".qodacode",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    # File extensions (skip non-code files)
    "*.min.js",
    "*.bundle.js",
    "*.md",
    "*.txt",
    "*.pyc",
    "*.pyo",
    "*.log",
}


def load_qodacodeignore(path: str = ".") -> Set[str]:
    """
    Load patterns from .qodacodeignore file.

    Format is similar to .gitignore:
    - One pattern per line
    - Lines starting with # are comments
    - Empty lines are ignored
    - Patterns can be directories, files, or glob patterns

    Example .qodacodeignore:
        # Ignore test fixtures
        tests/fixtures/
        *.test.js

        # Ignore generated files
        generated/
        *.gen.py

    Args:
        path: Root directory to look for .qodacodeignore

    Returns:
        Set of patterns from .qodacodeignore, empty if file doesn't exist
    """
    ignore_file = Path(path) / ".qodacodeignore"

    if not ignore_file.exists():
        return set()

    patterns = set()

    try:
        with open(ignore_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Remove trailing slashes for directories
                if line.endswith('/'):
                    line = line[:-1]

                patterns.add(line)
    except (IOError, OSError):
        return set()

    return patterns


def get_exclude_patterns(path: str = ".") -> Set[str]:
    """
    Get combined exclude patterns from DEFAULT_EXCLUDE and .qodacodeignore.

    Args:
        path: Root directory to look for .qodacodeignore

    Returns:
        Combined set of all exclude patterns
    """
    patterns = DEFAULT_EXCLUDE.copy()
    patterns.update(load_qodacodeignore(path))
    return patterns


@dataclass
class CachedTree:
    """Cached AST with file hash for invalidation."""
    hash: str
    tree: tree_sitter.Tree
    language: str


@dataclass
class ScanResult:
    """Result of a scan operation."""
    issues: List[Issue]
    files_scanned: int
    files_with_issues: int
    parse_errors: List[str]

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.LOW)

    def by_severity(self) -> Dict[Severity, List[Issue]]:
        """Group issues by severity."""
        result: Dict[Severity, List[Issue]] = {s: [] for s in Severity}
        for issue in self.issues:
            result[issue.severity].append(issue)
        return result

    def by_category(self) -> Dict[Category, List[Issue]]:
        """Group issues by category."""
        result: Dict[Category, List[Issue]] = {c: [] for c in Category}
        for issue in self.issues:
            result[issue.category].append(issue)
        return result

    def by_file(self) -> Dict[str, List[Issue]]:
        """Group issues by file path."""
        result: Dict[str, List[Issue]] = {}
        for issue in self.issues:
            # Pydantic Issue uses location.filepath
            filepath = issue.location.filepath
            if filepath not in result:
                result[filepath] = []
            result[filepath].append(issue)
        return result


class Scanner:
    """
    Tree-sitter based code scanner.

    Features:
    - Multi-language support (Python, JavaScript, TypeScript)
    - AST caching with hash-based invalidation
    - Parallel file processing
    - Configurable rule execution
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        max_workers: int = 4,
        persistent_cache: bool = True,
        project_path: str = ".",
    ):
        """
        Initialize the scanner.

        Args:
            cache_enabled: Whether to cache parsed ASTs (in-memory)
            max_workers: Maximum parallel workers for scanning
            persistent_cache: Whether to use disk cache for scan results
            project_path: Project root for persistent cache location
        """
        self.cache_enabled = cache_enabled
        self.max_workers = max_workers
        self.persistent_cache = persistent_cache
        self._ast_cache: Dict[str, CachedTree] = {}
        self._parsers: Dict[str, tree_sitter.Parser] = {}
        self._scan_cache: Optional[ScanCache] = None

        # Initialize persistent cache
        if persistent_cache:
            try:
                self._scan_cache = ScanCache(project_path)
            except Exception:
                self._scan_cache = None

        # Initialize parsers for each language
        for ext, config in LANGUAGE_CONFIG.items():
            lang_name = config["name"]
            if lang_name not in self._parsers:
                parser = tree_sitter.Parser(config["language"])
                self._parsers[lang_name] = parser

    def save_cache(self) -> None:
        """Save the persistent cache to disk."""
        if self._scan_cache:
            self._scan_cache.save()

    def get_cache_stats(self) -> Dict[str, any]:
        """Get statistics about the persistent cache."""
        if self._scan_cache:
            return self._scan_cache.stats()
        return {"enabled": False}

    def clear_cache(self) -> None:
        """Clear all cached scan results."""
        if self._scan_cache:
            self._scan_cache.clear()

    def _get_file_hash(self, filepath: str) -> str:
        """Compute MD5 hash of file contents."""
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def _get_language_for_file(self, filepath: str) -> Optional[str]:
        """Determine the language based on file extension."""
        ext = Path(filepath).suffix.lower()
        if ext in LANGUAGE_CONFIG:
            return LANGUAGE_CONFIG[ext]["name"]
        return None

    def _get_parser_for_file(self, filepath: str) -> Optional[tree_sitter.Parser]:
        """Get the appropriate parser for a file."""
        language = self._get_language_for_file(filepath)
        if language:
            return self._parsers.get(language)
        return None

    def parse_file(self, filepath: str) -> Optional[Tuple[tree_sitter.Tree, bytes, str]]:
        """
        Parse a single file, using cache if available.

        Args:
            filepath: Path to the file to parse

        Returns:
            Tuple of (AST tree, source bytes, language) or None if parsing fails
        """
        language = self._get_language_for_file(filepath)
        if not language:
            return None

        try:
            with open(filepath, "rb") as f:
                source = f.read()
        except (IOError, OSError):
            return None

        file_hash = hashlib.md5(source).hexdigest()

        # Check cache
        if self.cache_enabled and filepath in self._ast_cache:
            cached = self._ast_cache[filepath]
            if cached.hash == file_hash:
                return cached.tree, source, language

        # Parse the file
        parser = self._parsers.get(language)
        if not parser:
            return None

        try:
            tree = parser.parse(source)
        except Exception:
            return None

        # Update cache
        if self.cache_enabled:
            self._ast_cache[filepath] = CachedTree(
                hash=file_hash,
                tree=tree,
                language=language,
            )

        return tree, source, language

    def _should_exclude(self, path: str, exclude: Set[str]) -> bool:
        """Check if a path should be excluded from scanning."""
        path_parts = Path(path).parts
        for pattern in exclude:
            # Check if any path component matches
            if pattern in path_parts:
                return True
            # Check glob patterns
            if pattern.startswith("*") and path.endswith(pattern[1:]):
                return True
        return False

    def _collect_files(
        self,
        path: str,
        exclude: Optional[Set[str]] = None,
    ) -> List[str]:
        """Collect all scannable files from a path.

        Automatically loads .qodacodeignore patterns if no exclude is provided.
        """
        exclude = exclude or get_exclude_patterns(path)
        files = []

        path_obj = Path(path)
        if path_obj.is_file():
            if self._get_language_for_file(str(path_obj)):
                return [str(path_obj)]
            return []

        for root, dirs, filenames in os.walk(path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d), exclude)]

            for filename in filenames:
                filepath = os.path.join(root, filename)
                if self._should_exclude(filepath, exclude):
                    continue
                if self._get_language_for_file(filepath):
                    files.append(filepath)

        return files

    def _scan_file(
        self,
        filepath: str,
        rules: List[Rule],
        use_cache: bool = True,
    ) -> Tuple[List[Issue], Optional[str]]:
        """
        Scan a single file with the given rules.

        Uses persistent cache when available to skip re-scanning
        unchanged files. Target: <10ms for cache hits.

        Args:
            filepath: Path to the file to scan
            rules: List of rules to apply
            use_cache: Whether to use persistent disk cache

        Returns:
            Tuple of (issues list, parse error message or None)
        """
        # Check persistent cache first
        if use_cache and self._scan_cache:
            cached_issues = self._scan_cache.get_for_file(filepath)
            if cached_issues is not None:
                # Reconstruct Issue objects from cached dicts
                try:
                    issues = [Issue.model_validate(d) for d in cached_issues]
                    return issues, None
                except Exception:
                    pass  # Cache corrupted, continue with scan

        # Parse the file
        parsed = self.parse_file(filepath)
        if not parsed:
            return [], f"Failed to parse: {filepath}"

        tree, source, language = parsed
        issues = []

        for rule in rules:
            # Skip rules that don't support this language
            if language not in rule.languages:
                continue

            try:
                rule_issues = rule.check(tree, source, filepath)
                issues.extend(rule_issues)
            except Exception as e:
                # Log but don't fail on rule errors
                issues.append(Issue(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    category=rule.category,
                    severity=Severity.INFO,
                    engine=EngineSource.TREESITTER,
                    location=Location(
                        filepath=filepath,
                        line=1,
                        column=0,
                        end_line=1,
                        end_column=0,
                    ),
                    message=f"Rule execution error: {str(e)}",
                ))

        # Store results in persistent cache
        if use_cache and self._scan_cache:
            try:
                issue_dicts = [i.model_dump() for i in issues]
                self._scan_cache.set_for_file(filepath, issue_dicts)
            except Exception:
                pass  # Cache save failure is not critical

        return issues, None

    def scan(
        self,
        path: str = ".",
        exclude: Optional[Set[str]] = None,
        rules: Optional[List[Rule]] = None,
        categories: Optional[List[Category]] = None,
        severities: Optional[List[Severity]] = None,
        parallel: bool = True,
    ) -> ScanResult:
        """
        Scan files at the given path.

        Args:
            path: File or directory to scan
            exclude: Patterns to exclude (defaults to DEFAULT_EXCLUDE)
            rules: Specific rules to run (defaults to all registered rules)
            categories: Filter rules by category
            severities: Only return issues of these severities
            parallel: Whether to use parallel processing

        Returns:
            ScanResult with all issues found
        """
        # Get rules to run
        if rules is None:
            rules = RuleRegistry.get_all()

        # Filter by category if specified
        if categories:
            rules = [r for r in rules if r.category in categories]

        if not rules:
            return ScanResult(
                issues=[],
                files_scanned=0,
                files_with_issues=0,
                parse_errors=[],
            )

        # Collect files
        files = self._collect_files(path, exclude)
        if not files:
            return ScanResult(
                issues=[],
                files_scanned=0,
                files_with_issues=0,
                parse_errors=[],
            )

        all_issues: List[Issue] = []
        parse_errors: List[str] = []
        files_with_issues: Set[str] = set()

        # Scan files (parallel or sequential)
        if parallel and len(files) > 10:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._scan_file, f, rules): f
                    for f in files
                }
                for future in as_completed(futures):
                    issues, error = future.result()
                    if error:
                        parse_errors.append(error)
                    if issues:
                        all_issues.extend(issues)
                        files_with_issues.add(futures[future])
        else:
            for filepath in files:
                issues, error = self._scan_file(filepath, rules)
                if error:
                    parse_errors.append(error)
                if issues:
                    all_issues.extend(issues)
                    files_with_issues.add(filepath)

        # Filter by severity if specified
        if severities:
            all_issues = [i for i in all_issues if i.severity in severities]

        # Sort issues: by severity (critical first), then by file, then by line
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        all_issues.sort(key=lambda i: (
            severity_order[i.severity],
            i.location.filepath,
            i.location.line,
        ))

        return ScanResult(
            issues=all_issues,
            files_scanned=len(files),
            files_with_issues=len(files_with_issues),
            parse_errors=parse_errors,
        )

    def scan_file(
        self,
        filepath: str,
        rules: Optional[List[Rule]] = None,
        categories: Optional[List[Category]] = None,
        severities: Optional[List[Severity]] = None,
    ) -> ScanResult:
        """
        Scan a single file.

        Args:
            filepath: Path to the file to scan
            rules: Specific rules to run (defaults to all registered rules)
            categories: Filter rules by category
            severities: Only return issues of these severities

        Returns:
            ScanResult with issues found in this file
        """
        # Get rules to run
        if rules is None:
            rules = RuleRegistry.get_all()

        # Filter by category if specified
        if categories:
            rules = [r for r in rules if r.category in categories]

        if not rules:
            return ScanResult(
                issues=[],
                files_scanned=1,
                files_with_issues=0,
                parse_errors=[],
            )

        issues, error = self._scan_file(filepath, rules)
        parse_errors = [error] if error else []

        # Filter by severity if specified
        if severities:
            issues = [i for i in issues if i.severity in severities]

        return ScanResult(
            issues=issues,
            files_scanned=1,
            files_with_issues=1 if issues else 0,
            parse_errors=parse_errors,
        )

    def get_changed_files(
        self,
        path: str = ".",
        base: str = "HEAD",
        include_staged: bool = True,
        include_unstaged: bool = True,
        include_untracked: bool = True,
    ) -> List[str]:
        """
        Get list of changed files using git.

        Args:
            path: Root path to check for changes
            base: Git ref to compare against (default HEAD)
            include_staged: Include staged changes
            include_unstaged: Include unstaged changes
            include_untracked: Include untracked files

        Returns:
            List of changed file paths that are scannable
        """
        changed_files: Set[str] = set()
        path_obj = Path(path).resolve()

        try:
            # Check if we're in a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=str(path_obj),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return []  # Not a git repo

            # Staged changes
            if include_staged:
                result = subprocess.run(
                    ["git", "diff", "--cached", "--name-only", base],
                    cwd=str(path_obj),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            changed_files.add(str(path_obj / line))

            # Unstaged changes
            if include_unstaged:
                result = subprocess.run(
                    ["git", "diff", "--name-only"],
                    cwd=str(path_obj),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            changed_files.add(str(path_obj / line))

            # Untracked files
            if include_untracked:
                result = subprocess.run(
                    ["git", "ls-files", "--others", "--exclude-standard"],
                    cwd=str(path_obj),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            changed_files.add(str(path_obj / line))

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return []

        # Filter to only scannable files
        return [
            f for f in changed_files
            if self._get_language_for_file(f) and Path(f).exists()
        ]

    def scan_diff(
        self,
        path: str = ".",
        base: str = "HEAD",
        exclude: Optional[Set[str]] = None,
        rules: Optional[List[Rule]] = None,
        categories: Optional[List[Category]] = None,
        severities: Optional[List[Severity]] = None,
    ) -> ScanResult:
        """
        Scan only changed files (diff-aware scanning).

        Much faster than full scan - only analyzes git changes.
        Target: <100ms for typical development changes.

        Args:
            path: Root path for git operations
            base: Git ref to compare against (default HEAD)
            exclude: Patterns to exclude
            rules: Specific rules to run
            categories: Filter rules by category
            severities: Only return issues of these severities

        Returns:
            ScanResult with issues found in changed files
        """
        # Get changed files
        changed_files = self.get_changed_files(path, base)

        if not changed_files:
            return ScanResult(
                issues=[],
                files_scanned=0,
                files_with_issues=0,
                parse_errors=[],
            )

        # Filter out excluded files (includes .qodacodeignore)
        exclude = exclude or get_exclude_patterns(path)
        changed_files = [
            f for f in changed_files
            if not self._should_exclude(f, exclude)
        ]

        if not changed_files:
            return ScanResult(
                issues=[],
                files_scanned=0,
                files_with_issues=0,
                parse_errors=[],
            )

        # Get rules to run
        if rules is None:
            rules = RuleRegistry.get_all()

        if categories:
            rules = [r for r in rules if r.category in categories]

        if not rules:
            return ScanResult(
                issues=[],
                files_scanned=len(changed_files),
                files_with_issues=0,
                parse_errors=[],
            )

        # Scan changed files (no parallel needed for small sets)
        all_issues: List[Issue] = []
        parse_errors: List[str] = []
        files_with_issues: Set[str] = set()

        for filepath in changed_files:
            issues, error = self._scan_file(filepath, rules)
            if error:
                parse_errors.append(error)
            if issues:
                all_issues.extend(issues)
                files_with_issues.add(filepath)

        # Filter by severity if specified
        if severities:
            all_issues = [i for i in all_issues if i.severity in severities]

        # Sort issues
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        all_issues.sort(key=lambda i: (
            severity_order[i.severity],
            i.location.filepath,
            i.location.line,
        ))

        return ScanResult(
            issues=all_issues,
            files_scanned=len(changed_files),
            files_with_issues=len(files_with_issues),
            parse_errors=parse_errors,
        )

    def clear_cache(self) -> None:
        """Clear the AST cache."""
        self._ast_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_files": len(self._ast_cache),
            "languages": len(self._parsers),
        }

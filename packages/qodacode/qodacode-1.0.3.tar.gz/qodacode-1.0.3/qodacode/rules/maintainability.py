"""
Maintainability rules for Qodacode.

MNT-001: code-duplication - Duplicate code between files
MNT-002: long-function - Functions exceeding 200 lines
MNT-003: high-complexity - High cyclomatic complexity (>10 branches)
"""

from typing import List, Dict
import tree_sitter

from qodacode.rules.base import Rule, Issue, Severity, Category


class LongFunctionRule(Rule):
    """
    MNT-002: Detect functions that are too long.

    Functions longer than 200 lines are hard to understand and maintain.
    They should be broken down into smaller, focused functions.
    """
    id = "MNT-002"
    name = "long-function"
    description = "Detects functions exceeding 200 lines"
    severity = Severity.MEDIUM
    category = Category.MAINTAINABILITY
    languages = ["python", "javascript", "typescript"]

    MAX_LINES = 200

    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        issues = []
        cursor = tree.walk()
        self._check_node(cursor.node, source, filepath, issues)
        return issues

    def _check_node(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Recursively check for long functions."""

        # Python function definition
        if node.type in ("function_definition", "method_definition"):
            self._check_function(node, source, filepath, issues)

        # JavaScript/TypeScript function
        elif node.type in ("function_declaration", "arrow_function", "method_definition"):
            self._check_function(node, source, filepath, issues)

        for child in node.children:
            self._check_node(child, source, filepath, issues)

    def _check_function(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check if a function exceeds the line limit."""
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        line_count = end_line - start_line

        if line_count > self.MAX_LINES:
            # Get function name
            name_node = node.child_by_field_name("name")
            func_name = self.get_node_text(name_node, source) if name_node else "<anonymous>"

            issues.append(self.create_issue(
                filepath=filepath,
                node=node,
                source=source,
                message=f"Function '{func_name}' is {line_count} lines (max: {self.MAX_LINES})",
                fix_suggestion="Break down into smaller functions with single responsibilities",
                context={
                    "function": func_name,
                    "line_count": line_count,
                    "max_lines": self.MAX_LINES,
                },
            ))


class HighComplexityRule(Rule):
    """
    MNT-003: Detect functions with high cyclomatic complexity.

    Cyclomatic complexity measures the number of independent paths through code.
    High complexity (>10) makes code hard to test and maintain.
    """
    id = "MNT-003"
    name = "high-complexity"
    description = "Detects functions with cyclomatic complexity > 10"
    severity = Severity.MEDIUM
    category = Category.MAINTAINABILITY
    languages = ["python", "javascript", "typescript"]

    MAX_COMPLEXITY = 10

    # Node types that increase complexity
    COMPLEXITY_NODES = {
        # Branching
        "if_statement", "elif_clause", "else_clause",
        "conditional_expression", "ternary_expression",
        # Loops
        "for_statement", "while_statement", "for_in_statement",
        "do_statement",
        # Exception handling
        "except_clause", "catch_clause",
        # Logical operators (short-circuit)
        "and", "or", "&&", "||",
        # Case/switch
        "case_clause", "match_statement",
    }

    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        issues = []
        cursor = tree.walk()
        self._check_node(cursor.node, source, filepath, issues)
        return issues

    def _check_node(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Find functions and check their complexity."""

        if node.type in ("function_definition", "function_declaration",
                         "method_definition", "arrow_function"):
            complexity = self._calculate_complexity(node)

            if complexity > self.MAX_COMPLEXITY:
                name_node = node.child_by_field_name("name")
                func_name = self.get_node_text(name_node, source) if name_node else "<anonymous>"

                issues.append(self.create_issue(
                    filepath=filepath,
                    node=node,
                    source=source,
                    message=f"Function '{func_name}' has complexity {complexity} (max: {self.MAX_COMPLEXITY})",
                    fix_suggestion="Reduce branches by extracting logic into separate functions",
                    context={
                        "function": func_name,
                        "complexity": complexity,
                        "max_complexity": self.MAX_COMPLEXITY,
                    },
                ))

        for child in node.children:
            self._check_node(child, source, filepath, issues)

    def _calculate_complexity(self, node: tree_sitter.Node) -> int:
        """
        Calculate cyclomatic complexity of a function.

        Complexity = 1 + number of decision points
        """
        complexity = 1  # Base complexity

        def count_decisions(n: tree_sitter.Node) -> int:
            count = 0
            if n.type in self.COMPLEXITY_NODES:
                count = 1

            # Count logical operators in binary expressions
            if n.type == "binary_operator":
                op = n.child_by_field_name("operator")
                if op and self.get_node_text(op, b"") in ("and", "or"):
                    count = 1

            for child in n.children:
                count += count_decisions(child)
            return count

        return complexity + count_decisions(node)


class CircularImportRule(Rule):
    """
    MNT-004: Detect potential circular imports.

    This is a simplified check that flags suspicious import patterns.
    Full circular import detection requires analyzing the entire module graph.
    """
    id = "MNT-004"
    name = "circular-import"
    description = "Detects potential circular import patterns"
    severity = Severity.MEDIUM
    category = Category.MAINTAINABILITY
    languages = ["python"]

    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        issues = []

        # Find all imports inside functions (often a sign of circular import workaround)
        cursor = tree.walk()
        self._check_node(cursor.node, source, filepath, issues)

        return issues

    def _check_node(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check for imports inside functions."""

        if node.type in ("function_definition", "method_definition"):
            # Check if this function has imports inside it
            self._check_function_imports(node, source, filepath, issues)
        else:
            for child in node.children:
                self._check_node(child, source, filepath, issues)

    def _check_function_imports(
        self,
        func_node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check if a function contains import statements."""

        def find_imports(node: tree_sitter.Node) -> List[tree_sitter.Node]:
            imports = []
            if node.type in ("import_statement", "import_from_statement"):
                imports.append(node)
            for child in node.children:
                imports.extend(find_imports(child))
            return imports

        imports = find_imports(func_node)

        if imports:
            func_name = self.find_parent_function(imports[0])
            for imp_node in imports:
                issues.append(self.create_issue(
                    filepath=filepath,
                    node=imp_node,
                    source=source,
                    message="Import inside function - often indicates circular import issue",
                    fix_suggestion="Move import to top of file or refactor to break the circular dependency",
                    context={"function": func_name},
                ))

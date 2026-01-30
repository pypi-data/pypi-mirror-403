"""
Robustness rules for Qodacode.

ROB-001: no-error-handling - External calls without try/catch
ROB-002: no-timeout - Requests without timeout defined
"""

from typing import List, Set

import tree_sitter

from qodacode.rules.base import Rule, Issue, Severity, Category


# Functions that make external calls and should have error handling
EXTERNAL_CALL_FUNCTIONS = {
    "python": {
        "requests.get",
        "requests.post",
        "requests.put",
        "requests.delete",
        "requests.patch",
        "httpx.get",
        "httpx.post",
        "aiohttp.get",
        "urllib.request.urlopen",
        "socket.connect",
        "open",  # File operations
        "json.loads",
        "json.load",
    },
    "javascript": {
        "fetch",
        "axios.get",
        "axios.post",
        "axios.put",
        "axios.delete",
        "http.get",
        "https.get",
        "fs.readFile",
        "fs.writeFile",
        "JSON.parse",
    },
    "typescript": {
        "fetch",
        "axios.get",
        "axios.post",
        "axios.put",
        "axios.delete",
        "http.get",
        "https.get",
        "fs.readFile",
        "fs.writeFile",
        "JSON.parse",
    },
}

# Request functions that should have timeout
REQUEST_FUNCTIONS = {
    "requests.get",
    "requests.post",
    "requests.put",
    "requests.delete",
    "requests.patch",
    "requests.request",
    "httpx.get",
    "httpx.post",
    "fetch",
    "axios.get",
    "axios.post",
}


class NoErrorHandlingRule(Rule):
    """
    ROB-001: Detect external calls without error handling.

    External operations (HTTP requests, file I/O, JSON parsing) can fail.
    They should be wrapped in try/except (Python) or try/catch (JS/TS).
    """
    id = "ROB-001"
    name = "no-error-handling"
    description = "Detects external calls without try/except handling"
    severity = Severity.HIGH
    category = Category.ROBUSTNESS
    languages = ["python", "javascript", "typescript"]

    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        issues = []
        cursor = tree.walk()

        # Detect language from file extension
        if filepath.endswith(".py"):
            lang = "python"
        elif filepath.endswith((".js", ".jsx")):
            lang = "javascript"
        else:
            lang = "typescript"

        external_funcs = EXTERNAL_CALL_FUNCTIONS.get(lang, set())
        self._check_node(cursor.node, source, filepath, issues, external_funcs)

        return issues

    def _check_node(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
        external_funcs: Set[str],
    ) -> None:
        """Recursively check for unhandled external calls."""

        # Check if this is a function call
        if node.type == "call":
            self._check_call(node, source, filepath, issues, external_funcs)

        # Recurse into children
        for child in node.children:
            self._check_node(child, source, filepath, issues, external_funcs)

    def _is_inside_try(self, node: tree_sitter.Node) -> bool:
        """Check if a node is inside a try block."""
        current = node.parent
        while current:
            if current.type in ("try_statement", "try"):
                return True
            current = current.parent
        return False

    def _check_call(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
        external_funcs: Set[str],
    ) -> None:
        """Check if a function call needs error handling."""
        func_node = node.child_by_field_name("function")
        if not func_node:
            return

        func_name = self.get_node_text(func_node, source)

        # Check if it's an external call
        is_external = any(ext in func_name for ext in external_funcs)
        if not is_external:
            return

        # Check if it's inside a try block
        if self._is_inside_try(node):
            return

        issues.append(self.create_issue(
            filepath=filepath,
            node=node,
            source=source,
            message=f"External call to '{func_name}' without error handling",
            fix_suggestion="Wrap in try/except to handle potential failures",
            context={"function": self.find_parent_function(node)},
        ))


class NoTimeoutRule(Rule):
    """
    ROB-002: Detect HTTP requests without timeout.

    Requests without timeout can hang indefinitely if the server
    doesn't respond, blocking your application.
    """
    id = "ROB-002"
    name = "no-timeout"
    description = "Detects HTTP requests without timeout defined"
    severity = Severity.HIGH
    category = Category.ROBUSTNESS
    languages = ["python", "javascript", "typescript"]

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
        """Recursively check for requests without timeout."""

        if node.type == "call":
            self._check_call(node, source, filepath, issues)

        for child in node.children:
            self._check_node(child, source, filepath, issues)

    def _check_call(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check if a request call has timeout."""
        func_node = node.child_by_field_name("function")
        if not func_node:
            return

        func_name = self.get_node_text(func_node, source)

        # Check if it's a request function
        is_request = any(req in func_name for req in REQUEST_FUNCTIONS)
        if not is_request:
            return

        # Get the full call text to check for timeout argument
        call_text = self.get_node_text(node, source)

        # Check for timeout parameter
        has_timeout = (
            "timeout" in call_text.lower() or
            # axios config with timeout
            "timeout:" in call_text
        )

        if not has_timeout:
            issues.append(self.create_issue(
                filepath=filepath,
                node=node,
                source=source,
                message=f"HTTP request '{func_name}' without timeout - can hang indefinitely",
                fix_suggestion="Add timeout parameter: requests.get(url, timeout=30)",
                context={"function": self.find_parent_function(node)},
            ))

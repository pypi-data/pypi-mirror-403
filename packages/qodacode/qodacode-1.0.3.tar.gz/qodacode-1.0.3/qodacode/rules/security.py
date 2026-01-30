"""
Security rules for Qodacode.

SEC-001: hardcoded-secret - Secrets in source code (Gitleaks-level detection)
SEC-002: sql-injection - SQL queries without sanitization
SEC-003: command-injection - Shell commands with unvalidated input
SEC-005: no-auth-endpoint - Public endpoints without authentication
SEC-007: path-traversal - File operations with unsanitized paths
"""

import re
from typing import List

import tree_sitter

from qodacode.rules.base import Rule, Issue, Severity, Category
from qodacode.models.issue import Location, EngineSource


# Variable name patterns that indicate potential secrets (AST-based detection)
SECRET_VAR_PATTERNS = [
    # API keys and tokens
    (r"(?i)(api[_-]?key|apikey)", "API key"),
    (r"(?i)(secret[_-]?key|secretkey)", "secret key"),
    (r"(?i)(auth[_-]?token|authtoken)", "auth token"),
    (r"(?i)(access[_-]?token|accesstoken)", "access token"),
    (r"(?i)(private[_-]?key|privatekey)", "private key"),
    (r"(?i)(client[_-]?secret)", "client secret"),
    # Database
    (r"(?i)(password|passwd|pwd)", "password"),
    (r"(?i)(db[_-]?password)", "database password"),
    (r"(?i)(database[_-]?url)", "database URL"),
    (r"(?i)(connection[_-]?string)", "connection string"),
    # Cloud providers
    (r"(?i)(aws[_-]?secret)", "AWS secret"),
    (r"(?i)(azure[_-]?key)", "Azure key"),
    (r"(?i)(gcp[_-]?key|google[_-]?key)", "GCP key"),
]

# SQL keywords that indicate query building
SQL_KEYWORDS = [
    "SELECT", "INSERT", "UPDATE", "DELETE", "DROP",
    "CREATE", "ALTER", "TRUNCATE", "EXEC", "EXECUTE",
]

# Variable name patterns that suggest SQL query context (real queries, not logs)
SQL_CONTEXT_PATTERNS = [
    r"(?i)query",
    r"(?i)sql",
    r"(?i)statement",
    r"(?i)command",
    r"(?i)select",
    r"(?i)insert",
    r"(?i)update",
    r"(?i)delete",
    r"(?i)cursor",
]

# Variable name patterns that suggest log/error messages (NOT SQL queries)
LOG_CONTEXT_PATTERNS = [
    r"(?i)msg",
    r"(?i)message",
    r"(?i)error",
    r"(?i)log",
    r"(?i)info",
    r"(?i)warn",
    r"(?i)debug",
    r"(?i)exception",
    r"(?i)reason",
    r"(?i)description",
    r"(?i)detail",
    r"(?i)text",
]

# Dangerous functions for command injection
DANGEROUS_COMMANDS = {
    "python": [
        "os.system",
        "os.popen",
        "subprocess.call",
        "subprocess.run",
        "subprocess.Popen",
        "eval",
        "exec",
    ],
    "javascript": [
        "eval",
        "exec",
        "execSync",
        "spawn",
        "spawnSync",
        "child_process.exec",
    ],
    "typescript": [
        "eval",
        "exec",
        "execSync",
        "spawn",
        "spawnSync",
        "child_process.exec",
    ],
}


class HardcodedSecretRule(Rule):
    """
    SEC-001: Detect hardcoded secrets in source code.

    Uses two detection methods:
    1. AST-based: Variable names suggesting secrets (api_key, password, etc.)
    2. Pattern-based: Gitleaks-level patterns for known secret formats

    This provides comprehensive coverage similar to Gitleaks but integrated
    into the Qodacode scanning pipeline.
    """
    id = "SEC-001"
    name = "hardcoded-secret"
    description = "Detects secrets hardcoded in source code (Gitleaks-level)"
    severity = Severity.CRITICAL
    category = Category.SECURITY
    languages = ["python", "javascript", "typescript"]

    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        issues = []
        source_str = source.decode("utf-8", errors="replace")

        # Method 1: AST-based detection (variable names)
        cursor = tree.walk()
        self._check_node(cursor.node, source, filepath, issues)

        # Method 2: Pattern-based detection (Gitleaks patterns)
        pattern_issues = self._check_gitleaks_patterns(filepath, source_str)
        issues.extend(pattern_issues)

        # Deduplicate by line number
        seen_lines = set()
        unique_issues = []
        for issue in issues:
            if issue.location.line not in seen_lines:
                seen_lines.add(issue.location.line)
                unique_issues.append(issue)

        return unique_issues

    def _check_gitleaks_patterns(self, filepath: str, source_str: str) -> List[Issue]:
        """Check for secrets using comprehensive Gitleaks-level patterns."""
        try:
            from qodacode.secrets import scan_for_secrets, should_skip_file

            if should_skip_file(filepath):
                return []

            findings = scan_for_secrets(source_str)
            issues = []

            for finding in findings:
                issues.append(Issue(
                    rule_id=self.id,
                    rule_name=self.name,
                    category=self.category,
                    severity=self.severity,
                    engine=EngineSource.TREESITTER,
                    location=Location(
                        filepath=filepath,
                        line=finding["line"],
                        column=finding["column"],
                        end_line=finding["line"],
                        end_column=finding["column"] + len(finding["match"]),
                    ),
                    message=f"Found {finding['pattern_name']}: {finding['match']}",
                    snippet=finding["match"],
                    fix_suggestion="Remove secret and use environment variable or secret manager",
                    context={
                        "pattern_id": finding["pattern_id"],
                        "pattern_name": finding["pattern_name"],
                    },
                ))

            return issues

        except ImportError:
            # secrets.py not available, skip pattern detection
            return []

    def _check_node(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Recursively check nodes for hardcoded secrets."""

        # Python: assignment (name = "value")
        if node.type == "assignment":
            self._check_python_assignment(node, source, filepath, issues)

        # JavaScript/TypeScript: variable_declarator (const name = "value")
        elif node.type == "variable_declarator":
            self._check_js_declarator(node, source, filepath, issues)

        # Recurse into children
        for child in node.children:
            self._check_node(child, source, filepath, issues)

    def _check_python_assignment(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check Python assignment for hardcoded secrets."""
        # Get left side (variable name)
        left = node.child_by_field_name("left")
        right = node.child_by_field_name("right")

        if not left or not right:
            return

        var_name = self.get_node_text(left, source)

        # Check if right side is a string literal
        if right.type not in ("string", "concatenated_string"):
            return

        # Check if variable name matches secret patterns
        for pattern, secret_type in SECRET_VAR_PATTERNS:
            if re.search(pattern, var_name):
                value = self.get_node_text(right, source)
                # Skip if it's reading from environment
                if "os.environ" in value or "os.getenv" in value:
                    continue
                # Skip empty strings or placeholders
                if value in ('""', "''", '"placeholder"', "'placeholder'"):
                    continue

                issues.append(self.create_issue(
                    filepath=filepath,
                    node=node,
                    source=source,
                    message=f"Variable '{var_name}' contains hardcoded {secret_type}",
                    fix_suggestion=f"Use environment variable: {var_name} = os.environ['{var_name.upper()}']",
                    context={
                        "function": self.find_parent_function(node),
                        "class": self.find_parent_class(node),
                        "secret_type": secret_type,
                    },
                ))
                break

    def _check_js_declarator(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check JavaScript/TypeScript variable declarator for hardcoded secrets."""
        name_node = node.child_by_field_name("name")
        value_node = node.child_by_field_name("value")

        if not name_node or not value_node:
            return

        var_name = self.get_node_text(name_node, source)

        # Check if value is a string literal
        if value_node.type not in ("string", "template_string"):
            return

        # Check if variable name matches secret patterns
        for pattern, secret_type in SECRET_VAR_PATTERNS:
            if re.search(pattern, var_name):
                value = self.get_node_text(value_node, source)
                # Skip if it's reading from environment
                if "process.env" in value:
                    continue
                # Skip empty strings
                if value in ('""', "''", '``', '""'):
                    continue

                issues.append(self.create_issue(
                    filepath=filepath,
                    node=node,
                    source=source,
                    message=f"Variable '{var_name}' contains hardcoded {secret_type}",
                    fix_suggestion=f"Use environment variable: const {var_name} = process.env.{var_name.upper()}",
                    context={
                        "function": self.find_parent_function(node),
                        "secret_type": secret_type,
                    },
                ))
                break


class SQLInjectionRule(Rule):
    """
    SEC-002: Detect potential SQL injection vulnerabilities.

    Looks for SQL queries built with string concatenation or f-strings
    instead of parameterized queries.
    """
    id = "SEC-002"
    name = "sql-injection"
    description = "Detects SQL queries vulnerable to injection"
    severity = Severity.CRITICAL
    category = Category.SECURITY
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
        """Recursively check for SQL injection patterns."""

        # Python f-string or string concatenation
        if node.type in ("binary_operator", "concatenated_string"):
            self._check_string_concat(node, source, filepath, issues)

        # Python f-string (formatted_string in some tree-sitter versions)
        if node.type == "string" and "f\"" in self.get_node_text(node, source)[:3]:
            self._check_fstring(node, source, filepath, issues)

        # JavaScript template literal
        if node.type == "template_string":
            self._check_template_literal(node, source, filepath, issues)

        for child in node.children:
            self._check_node(child, source, filepath, issues)

    def _contains_sql(self, text: str) -> bool:
        """Check if text contains SQL keywords."""
        upper_text = text.upper()
        return any(kw in upper_text for kw in SQL_KEYWORDS)

    def _check_string_concat(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check string concatenation for SQL."""
        text = self.get_node_text(node, source)
        if self._contains_sql(text):
            # Check if it involves variables (not just string + string)
            if "+" in text or "%" in text:
                issues.append(self.create_issue(
                    filepath=filepath,
                    node=node,
                    source=source,
                    message="SQL query built with string concatenation - vulnerable to injection",
                    fix_suggestion="Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
                    context={"function": self.find_parent_function(node)},
                ))

    def _is_log_context(self, node: tree_sitter.Node, source: bytes) -> bool:
        """Check if the f-string is in a logging/error context (not a real SQL query)."""
        # Check parent nodes for context
        parent = node.parent
        context_depth = 0
        while parent and context_depth < 5:
            parent_text = self.get_node_text(parent, source)
            # Check if it's in a log/error context
            for pattern in LOG_CONTEXT_PATTERNS:
                if re.search(pattern, parent_text[:100]):  # Check first 100 chars
                    return True
            # Check common logging calls
            if any(log in parent_text[:50] for log in ["logger.", "logging.", "print(", "raise ", ".error(", ".warning(", ".info(", ".debug("]):
                return True
            parent = parent.parent
            context_depth += 1
        return False

    def _check_fstring(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check f-strings for SQL."""
        text = self.get_node_text(node, source)
        if self._contains_sql(text) and "{" in text:
            # Skip if this is in a log/error context (not a real SQL query)
            if self._is_log_context(node, source):
                return

            issues.append(self.create_issue(
                filepath=filepath,
                node=node,
                source=source,
                message="SQL query built with f-string - vulnerable to injection",
                fix_suggestion="Use parameterized queries instead of f-strings for SQL",
                context={"function": self.find_parent_function(node)},
            ))

    def _check_template_literal(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check JavaScript template literals for SQL."""
        text = self.get_node_text(node, source)
        if self._contains_sql(text) and "${" in text:
            issues.append(self.create_issue(
                filepath=filepath,
                node=node,
                source=source,
                message="SQL query built with template literal - vulnerable to injection",
                fix_suggestion="Use parameterized queries with prepared statements",
                context={"function": self.find_parent_function(node)},
            ))


class CommandInjectionRule(Rule):
    """
    SEC-003: Detect command injection vulnerabilities.

    Looks for shell commands executed with user-controlled input
    without proper sanitization.

    Safe patterns (no warning):
    - subprocess.run([...], shell=False)  # list args, no shell
    - subprocess.call([...])  # list args without shell=True
    - subprocess.Popen([...], shell=False)

    Dangerous patterns (warning):
    - os.system(...)  # always uses shell
    - subprocess.run(..., shell=True)  # shell=True is dangerous
    - eval(...)  # arbitrary code execution
    - exec(...)  # arbitrary code execution
    """
    id = "SEC-003"
    name = "command-injection"
    description = "Detects shell commands with unsanitized input"
    severity = Severity.CRITICAL
    category = Category.SECURITY
    languages = ["python", "javascript", "typescript"]

    # Functions that are ALWAYS dangerous (no safe usage)
    # Note: Use full function names to avoid false positives (e.g., executor.submit != exec)
    ALWAYS_DANGEROUS = [
        "os.system",
        "os.popen",
    ]

    # These need exact match (not substring) to avoid false positives like executor.submit
    EXACT_MATCH_DANGEROUS = [
        "eval",
        "exec",
    ]

    # Functions that are dangerous only with shell=True or string args
    CONDITIONAL_DANGEROUS = [
        "subprocess.call",
        "subprocess.run",
        "subprocess.Popen",
        "subprocess.check_output",
        "subprocess.check_call",
    ]

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
        """Recursively check for command injection patterns."""

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
        """Check function calls for dangerous command execution."""
        func_node = node.child_by_field_name("function")
        if not func_node:
            return

        func_name = self.get_node_text(func_node, source)
        args_node = node.child_by_field_name("arguments")
        args_text = self.get_node_text(args_node, source) if args_node else ""

        # Check ALWAYS dangerous functions (substring match for os.system, os.popen)
        if any(f in func_name for f in self.ALWAYS_DANGEROUS):
            # Check if argument is a static string (safe) vs dynamic (dangerous)
            if self._is_static_string_arg(args_node, source):
                return  # Static string literal is safe

            # Dynamic input is dangerous
            issues.append(self.create_issue(
                filepath=filepath,
                node=node,
                source=source,
                message=f"{func_name} is vulnerable to command injection",
                fix_suggestion="Use subprocess with shell=False and pass arguments as a list",
                context={"function": self.find_parent_function(node)},
            ))
            return

        # Check EXACT match dangerous functions (eval, exec - not executor.submit!)
        func_basename = func_name.split(".")[-1]  # Get the last part: executor.submit -> submit
        if func_basename in self.EXACT_MATCH_DANGEROUS:
            if self._is_static_string_arg(args_node, source):
                return  # Static string literal is less dangerous

            issues.append(self.create_issue(
                filepath=filepath,
                node=node,
                source=source,
                message=f"{func_name}() executes arbitrary code - potential code injection",
                fix_suggestion="Avoid eval/exec. Use ast.literal_eval for safe evaluation or refactor to avoid dynamic code execution",
                context={"function": self.find_parent_function(node)},
            ))
            return

        # Check CONDITIONAL dangerous functions (subprocess.*)
        is_subprocess = any(f in func_name for f in self.CONDITIONAL_DANGEROUS)
        if not is_subprocess:
            return

        # Safe: shell=False is explicitly set
        if "shell=False" in args_text or "shell = False" in args_text:
            return

        # Safe: First argument is a list (not a string) and no shell=True
        # List detection: starts with [ or is a variable (not a string literal)
        first_arg_is_list = args_text.lstrip("(").lstrip().startswith("[")
        has_shell_true = "shell=True" in args_text or "shell = True" in args_text

        if first_arg_is_list and not has_shell_true:
            # List args without shell=True is safe
            return

        # Dangerous: shell=True
        if has_shell_true:
            issues.append(self.create_issue(
                filepath=filepath,
                node=node,
                source=source,
                message=f"{func_name} with shell=True is vulnerable to command injection",
                fix_suggestion="Use shell=False and pass arguments as a list: subprocess.run(['cmd', 'arg1'], shell=False)",
                context={"function": self.find_parent_function(node)},
            ))
            return

        # Check for dynamic content with string arguments
        has_dynamic = (
            "{" in args_text or  # f-string
            "+" in args_text or  # concatenation
            "$" in args_text     # template literal
        )

        # Only warn if using strings (not lists) with dynamic content
        if has_dynamic and not first_arg_is_list:
            issues.append(self.create_issue(
                filepath=filepath,
                node=node,
                source=source,
                message=f"{func_name} with dynamic string argument may be vulnerable",
                fix_suggestion="Use subprocess with shell=False and pass arguments as a list",
                context={"function": self.find_parent_function(node)},
            ))

    def _is_static_string_arg(
        self,
        args_node: tree_sitter.Node,
        source: bytes
    ) -> bool:
        """Check if the first argument is a static string literal."""
        if not args_node:
            return False

        args_text = self.get_node_text(args_node, source)

        # Check for dynamic content indicators
        has_dynamic = (
            "f'" in args_text or 'f"' in args_text or  # f-string
            "{" in args_text or  # f-string interpolation
            "+" in args_text or  # concatenation
            "%" in args_text or  # old-style formatting
            ".format" in args_text  # .format() method
        )

        if has_dynamic:
            return False

        # Check if first arg is a simple string literal
        # Strip the parentheses and check first character
        inner = args_text.strip("()")
        first_char = inner.strip()[0:1] if inner.strip() else ""
        return first_char in ('"', "'")


class NoAuthEndpointRule(Rule):
    """
    SEC-005: Detect endpoints without authentication.

    Looks for route/endpoint definitions that lack authentication decorators.
    """
    id = "SEC-005"
    name = "no-auth-endpoint"
    description = "Detects public endpoints without authentication"
    severity = Severity.HIGH
    category = Category.SECURITY
    languages = ["python", "javascript", "typescript"]

    # Paths that typically require authentication
    SENSITIVE_PATHS = [
        "/admin",
        "/api/users",
        "/api/payments",
        "/api/settings",
        "/api/private",
        "/dashboard",
        "/account",
    ]

    # Auth decorator patterns
    AUTH_DECORATORS = [
        "login_required",
        "auth_required",
        "authenticated",
        "requires_auth",
        "jwt_required",
        "token_required",
        "permission_required",
        "IsAuthenticated",
    ]

    def check(
        self,
        tree: tree_sitter.Tree,
        source: bytes,
        filepath: str
    ) -> List[Issue]:
        issues = []
        source_str = source.decode("utf-8", errors="replace")

        # Find route definitions
        cursor = tree.walk()
        self._check_node(cursor.node, source, source_str, filepath, issues)

        return issues

    def _check_node(
        self,
        node: tree_sitter.Node,
        source: bytes,
        source_str: str,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check for unprotected route definitions."""

        # Python decorator
        if node.type == "decorated_definition":
            self._check_python_route(node, source, source_str, filepath, issues)

        for child in node.children:
            self._check_node(child, source, source_str, filepath, issues)

    def _check_python_route(
        self,
        node: tree_sitter.Node,
        source: bytes,
        source_str: str,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check Python decorated function for auth."""
        decorators = []
        route_path = None

        for child in node.children:
            if child.type == "decorator":
                dec_text = self.get_node_text(child, source)
                decorators.append(dec_text)

                # Check if it's a route decorator
                if any(r in dec_text for r in ["@app.route", "@router.", "@api."]):
                    # Extract path
                    match = re.search(r'["\']([^"\']+)["\']', dec_text)
                    if match:
                        route_path = match.group(1)

        if not route_path:
            return

        # Check if it's a sensitive path
        is_sensitive = any(s in route_path.lower() for s in self.SENSITIVE_PATHS)
        if not is_sensitive:
            return

        # Check if any auth decorator is present
        has_auth = any(
            any(auth in dec for auth in self.AUTH_DECORATORS)
            for dec in decorators
        )

        if not has_auth:
            issues.append(self.create_issue(
                filepath=filepath,
                node=node,
                source=source,
                message=f"Sensitive endpoint '{route_path}' has no authentication decorator",
                fix_suggestion="Add authentication decorator like @login_required",
                context={"route": route_path},
            ))


class PathTraversalRule(Rule):
    """
    SEC-007: Detect path traversal vulnerabilities.

    Looks for file operations with user-controlled paths that could
    allow access to files outside intended directories.
    """
    id = "SEC-007"
    name = "path-traversal"
    description = "Detects potential path traversal vulnerabilities"
    severity = Severity.HIGH
    category = Category.SECURITY
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
        """Check for path traversal patterns."""

        if node.type == "call":
            self._check_file_operation(node, source, filepath, issues)

        for child in node.children:
            self._check_node(child, source, filepath, issues)

    def _check_file_operation(
        self,
        node: tree_sitter.Node,
        source: bytes,
        filepath: str,
        issues: List[Issue],
    ) -> None:
        """Check file operations for path traversal."""
        func_node = node.child_by_field_name("function")
        if not func_node:
            return

        func_name = self.get_node_text(func_node, source)

        # File operations that could be vulnerable
        dangerous_funcs = ["open", "read_file", "write_file", "send_file",
                          "os.path.join", "Path", "readFile", "writeFile"]

        if not any(f in func_name for f in dangerous_funcs):
            return

        # Check arguments for dynamic paths
        args_node = node.child_by_field_name("arguments")
        if not args_node:
            return

        args_text = self.get_node_text(args_node, source)

        # Check for dynamic path construction without sanitization
        has_dynamic = (
            "{" in args_text or  # f-string
            "+" in args_text or  # concatenation
            "$" in args_text or  # template literal
            "request." in args_text or  # web request
            "params" in args_text or  # route params
            "query" in args_text  # query params
        )

        # Check if sanitization is present
        has_sanitization = (
            "secure_filename" in args_text or
            "realpath" in args_text or
            "abspath" in args_text or
            "normpath" in args_text or
            ".startswith(" in args_text
        )

        if has_dynamic and not has_sanitization:
            issues.append(self.create_issue(
                filepath=filepath,
                node=node,
                source=source,
                message=f"File operation with potentially unsanitized path",
                fix_suggestion="Validate and sanitize file paths, use os.path.realpath and check against allowed directories",
                context={"function": self.find_parent_function(node)},
            ))

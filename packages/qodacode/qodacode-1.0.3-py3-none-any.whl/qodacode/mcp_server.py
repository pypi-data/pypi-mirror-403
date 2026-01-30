"""
Qodacode MCP Server - Enterprise Edition.

Exposes Qodacode analysis capabilities as MCP tools for AI assistants.
Allows Claude, Cursor, and other MCP-compatible tools to use Qodacode
for code analysis, security scanning, and quality checks.

Features:
- Multi-engine security orchestration
- Rich output with fix suggestions and CWE references
- Adaptive output modes (junior/senior)
- AI-enriched explanations when API key is available
- Unified verdict: READY FOR PRODUCTION / NOT READY
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal

from mcp.server.fastmcp import FastMCP

from qodacode.utils.verdict import calculate_scan_summary, is_test_file

# Configure logging to stderr (CRITICAL: never use stdout with STDIO transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("qodacode-mcp")

# Initialize MCP server
mcp = FastMCP("qodacode")


# CWE Mapping for common vulnerability types
CWE_MAP = {
    # Secrets
    "GL-": "CWE-798",  # Hardcoded Credentials
    # SQL Injection
    "SEC-002": "CWE-89",
    "sql-injection": "CWE-89",
    # Command Injection
    "SEC-003": "CWE-78",
    "command-injection": "CWE-78",
    # XSS
    "SEC-004": "CWE-79",
    "xss": "CWE-79",
    # Path Traversal
    "SEC-007": "CWE-22",
    "path-traversal": "CWE-22",
    # Deserialization
    "SEC-006": "CWE-502",
    # Missing Auth
    "SEC-005": "CWE-306",
}


def _get_cwe_id(rule_id: str, rule_name: str = "") -> Optional[str]:
    """Get CWE ID for a rule if available."""
    # Check direct rule_id match
    if rule_id in CWE_MAP:
        return CWE_MAP[rule_id]
    # Check prefix match (for Gitleaks GL-*)
    for prefix, cwe in CWE_MAP.items():
        if rule_id.startswith(prefix):
            return cwe
    # Check rule_name keywords
    for keyword, cwe in CWE_MAP.items():
        if keyword in rule_name.lower():
            return cwe
    return None


def _format_issue(issue, mode: str = "senior") -> dict:
    """Format an issue for JSON output with rich context."""
    base = {
        "rule_id": issue.rule_id,
        "rule_name": issue.rule_name,
        "category": issue.category.value,
        "severity": issue.severity.value,
        "file": issue.location.filepath,
        "line": issue.location.line,
        "column": issue.location.column,
        "message": issue.message,
        "fix_suggestion": issue.fix_suggestion,
    }

    # Add CWE if available
    cwe = _get_cwe_id(issue.rule_id, issue.rule_name)
    if cwe:
        base["cwe_id"] = cwe
        base["cwe_url"] = f"https://cwe.mitre.org/data/definitions/{cwe.split('-')[1]}.html"

    # Add snippet if available
    if hasattr(issue, "snippet") and issue.snippet:
        base["snippet"] = issue.snippet

    # Add engine source if available
    if hasattr(issue, "engine") and issue.engine:
        base["engine"] = issue.engine.value

    # Junior mode: add detailed explanations
    if mode == "junior":
        base["why_it_matters"] = _get_why_it_matters(issue.rule_id)
        base["how_to_fix"] = _get_how_to_fix(issue.rule_id)

    return base


def _format_issue_rich(issue, mode: str = "senior") -> dict:
    """Format an issue with maximum context for LLM consumption."""
    base = _format_issue(issue, mode)

    # Add fix code snippet if we can infer it
    fix_snippet = _get_fix_snippet(issue.rule_id, getattr(issue, "snippet", None))
    if fix_snippet:
        base["suggested_fix_snippet"] = fix_snippet

    # Add context for cross-file analysis
    if hasattr(issue, "context") and issue.context:
        base["context"] = issue.context

    return base


def _get_fix_snippet(rule_id: str, original_snippet: Optional[str] = None) -> Optional[str]:
    """Generate a code fix snippet for common patterns."""
    fix_snippets = {
        "SEC-001": "# Use environment variable\nimport os\napi_key = os.getenv('API_KEY')",
        "SEC-002": "# Use parameterized query\ncursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
        "SEC-003": "# Use subprocess with shell=False\nimport subprocess\nsubprocess.run(['ls', '-la'], shell=False)",
        "ROB-001": "# Add try-except block\ntry:\n    risky_operation()\nexcept Exception as e:\n    logger.error(f'Error: {e}')",
        "ROB-002": "# Add timeout\nrequests.get(url, timeout=30)",
    }
    # Check Gitleaks prefix
    if rule_id.startswith("GL-"):
        return fix_snippets.get("SEC-001")
    return fix_snippets.get(rule_id)


@mcp.tool()
def full_audit(path: str = ".") -> str:
    """Run a comprehensive security audit using all Qodacode engines.

    This is the most thorough scan, combining:
    1. Secret Detection - API keys, tokens, credentials
    2. Core Analysis - Fast pattern matching (code quality, security patterns)
    3. Deep SAST - Advanced static analysis (complex vulnerabilities, taint tracking)
    4. Dependency Scanner - Known vulnerabilities (CVEs)

    Use this for:
    - Pre-commit security checks
    - CI/CD pipeline gates
    - Security audits before production deployments
    - Compliance verification

    Returns a verdict: READY FOR PRODUCTION (0 critical) or NOT READY.

    Args:
        path: Directory to audit. Defaults to current directory.

    Returns:
        JSON with issues sorted by severity and production verdict.
    """
    import time
    from qodacode.scanner import Scanner
    from qodacode.rate_limiter import RateLimiter
    from qodacode.audit_log import AuditLogger

    # Initialize rate limiter and audit logger
    rate_limiter = RateLimiter.from_project(path)
    audit_logger = AuditLogger(project_root=path)

    # Check rate limit
    can_scan, limit_reason = rate_limiter.can_scan()
    if not can_scan:
        error_response = {
            "error": "rate_limit_exceeded",
            "message": limit_reason,
            "usage": rate_limiter.get_current_usage(),
        }
        return json.dumps(error_response, indent=2)

    # Record scan operation
    rate_limiter.record_scan()
    scan_start_time = time.time()

    logger.info(f"Full audit on: {path}")

    all_issues: List[Dict[str, Any]] = []
    engines_run: Dict[str, Any] = {}

    # 1. Secret Detection - PRIORITY
    try:
        from qodacode.engines.gitleaks_runner import GitleaksRunner

        gitleaks = GitleaksRunner()
        if gitleaks.is_available():
            gl_issues = gitleaks.run(path)
            engines_run["secret_detection"] = {"status": "success", "count": len(gl_issues)}
            for issue in gl_issues:
                all_issues.append(_format_issue_rich(issue))
        else:
            engines_run["secret_detection"] = {"status": "not_available"}
    except Exception as e:
        engines_run["secret_detection"] = {"status": "error", "message": str(e)}

    # 2. Core Analysis (fast patterns)
    try:
        import qodacode.rules.security  # noqa: F401
        import qodacode.rules.robustness  # noqa: F401
        import qodacode.rules.maintainability  # noqa: F401
        import qodacode.rules.operability  # noqa: F401

        scanner = Scanner()
        ts_result = scanner.scan(path)
        engines_run["core_analysis"] = {
            "status": "success",
            "count": len(ts_result.issues),
            "files_scanned": ts_result.files_scanned,
        }
        for issue in ts_result.issues:
            all_issues.append(_format_issue_rich(issue))
    except Exception as e:
        engines_run["core_analysis"] = {"status": "error", "message": str(e)}

    # 3. Deep SAST (advanced static analysis)
    try:
        from qodacode.engines.semgrep_runner import SemgrepRunner

        semgrep = SemgrepRunner()
        if semgrep.is_available():
            sg_issues = semgrep.run(path)
            engines_run["deep_sast"] = {"status": "success", "count": len(sg_issues)}
            for issue in sg_issues:
                all_issues.append(_format_issue_rich(issue))
        else:
            engines_run["deep_sast"] = {
                "status": "not_installed",
                "install": "qodacode doctor (to verify)",
            }
    except Exception as e:
        engines_run["deep_sast"] = {"status": "error", "message": str(e)}

    # 4. Dependency Scanner (known vulnerabilities)
    try:
        from qodacode.osv import (
            find_dependency_files,
            parse_dependency_file,
            query_osv_batch,
        )

        dep_files = find_dependency_files(path)
        if dep_files:
            vuln_count = 0
            for dep_file in dep_files:
                ecosystem, packages = parse_dependency_file(dep_file)
                if packages:
                    vulns = query_osv_batch(packages, ecosystem)
                    for pkg_name, pkg_vulns in vulns.items():
                        for vuln in pkg_vulns:
                            vuln_count += 1
                            all_issues.append({
                                "rule_id": vuln.get("id", "DEP-VULN"),
                                "rule_name": "vulnerable-dependency",
                                "category": "dependencies",
                                "severity": vuln.get("severity", "high"),
                                "file": str(dep_file),
                                "line": 0,
                                "message": f"{pkg_name}: {vuln.get('summary', 'Known vulnerability')}",
                                "fix_suggestion": "Update to a patched version",
                            })
            engines_run["dependency_scanner"] = {"status": "success", "count": vuln_count}
        else:
            engines_run["dependency_scanner"] = {"status": "no_dependency_files"}
    except Exception as e:
        engines_run["dependency_scanner"] = {"status": "error", "message": str(e)}

    # Sort issues by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 4))

    # Calculate scan summary with production AND test counts (same logic as CLI/TUI)
    summary = calculate_scan_summary(all_issues)

    output = {
        "verdict": summary.message,
        "ready_for_production": summary.ready,
        "summary": {
            "total_issues": summary.total_issues,
            "production": summary.production.to_dict(),
            "tests": summary.tests.to_dict(),
            "engines": engines_run,
        },
        "issues": all_issues,
    }

    # Audit log: Record scan completion
    scan_duration_ms = (time.time() - scan_start_time) * 1000
    audit_logger.log_scan(
        path=path,
        scan_type="full_audit",
        findings_count=summary.total_issues,
        critical_count=summary.production.critical,
        duration_ms=scan_duration_ms,
    )

    return json.dumps(output, indent=2)


@mcp.tool()
def scan_code(
    path: str = ".",
    mode: str = "fast",
    categories: Optional[str] = None,
    severity_filter: Optional[str] = None,
) -> str:
    """Scan code for security vulnerabilities, quality issues, and best practices.

    This tool analyzes source code using static analysis to find:
    - Security vulnerabilities (SQL injection, XSS, hardcoded secrets, etc.)
    - Robustness issues (missing error handling, no timeouts, etc.)
    - Maintainability problems (long functions, too many parameters)
    - Operability concerns (no logging, hardcoded config)

    Returns a verdict: READY FOR PRODUCTION (0 critical) or NOT READY.

    Args:
        path: File or directory path to scan. Defaults to current directory.
        mode: Scan mode - "fast" (core analysis, quick) or "deep" (includes advanced SAST).
        categories: Comma-separated list of categories to check.
                   Options: security, robustness, maintainability, operability, dependencies
        severity_filter: Minimum severity to report. Options: critical, high, medium, low
    """
    from qodacode.scanner import Scanner
    from qodacode.rules.base import Category, Severity

    logger.info(f"Scanning path: {path}")

    # Import rules to register them
    import qodacode.rules.security  # noqa: F401
    import qodacode.rules.robustness  # noqa: F401
    import qodacode.rules.maintainability  # noqa: F401
    import qodacode.rules.operability  # noqa: F401
    import qodacode.rules.dependencies  # noqa: F401

    scanner = Scanner()

    # Parse categories filter
    category_list = None
    if categories:
        category_map = {
            "security": Category.SECURITY,
            "robustness": Category.ROBUSTNESS,
            "maintainability": Category.MAINTAINABILITY,
            "operability": Category.OPERABILITY,
            "dependencies": Category.DEPENDENCIES,
        }
        category_list = [
            category_map[c.strip().lower()]
            for c in categories.split(",")
            if c.strip().lower() in category_map
        ]

    # Parse severity filter
    severity_list = None
    if severity_filter:
        severity_order = ["critical", "high", "medium", "low", "info"]
        min_index = severity_order.index(severity_filter.lower())
        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO,
        }
        severity_list = [
            severity_map[s] for s in severity_order[:min_index + 1]
        ]

    # Run Tree-sitter scan (always)
    result = scanner.scan(
        path=path,
        categories=category_list,
        severities=severity_list,
    )

    all_issues = list(result.issues)
    engines_used = ["core_analysis"]

    # Deep mode: also run advanced SAST
    if mode == "deep":
        try:
            from qodacode.engines.semgrep_runner import SemgrepRunner

            semgrep = SemgrepRunner()
            if semgrep.is_available():
                sg_issues = semgrep.run(path)
                all_issues.extend(sg_issues)
                engines_used.append("deep_sast")
        except Exception as e:
            logger.warning(f"Deep SAST scan failed: {e}")

    # Calculate scan summary with production AND test counts (same logic as CLI/TUI)
    summary = calculate_scan_summary(all_issues)

    # Format output
    output = {
        "verdict": summary.message,
        "ready_for_production": summary.ready,
        "mode": mode,
        "engines": engines_used,
        "summary": {
            "files_scanned": result.files_scanned,
            "files_with_issues": result.files_with_issues,
            "total_issues": summary.total_issues,
            "production": summary.production.to_dict(),
            "tests": summary.tests.to_dict(),
        },
        "issues": [_format_issue(i) for i in all_issues],
    }

    if result.parse_errors:
        output["parse_errors"] = result.parse_errors

    return json.dumps(output, indent=2)


@mcp.tool()
def scan_single_file(filepath: str) -> str:
    """Scan a single file for issues.

    Faster than full scan when you only need to check one file.
    Useful for real-time analysis as code is being written.

    Args:
        filepath: Path to the file to scan.
    """
    from qodacode.scanner import Scanner

    # Import rules
    import qodacode.rules.security  # noqa: F401
    import qodacode.rules.robustness  # noqa: F401
    import qodacode.rules.maintainability  # noqa: F401
    import qodacode.rules.operability  # noqa: F401
    import qodacode.rules.dependencies  # noqa: F401

    logger.info(f"Scanning file: {filepath}")

    scanner = Scanner()
    result = scanner.scan_file(filepath)

    output = {
        "file": filepath,
        "issues_found": len(result.issues),
        "issues": [_format_issue(i) for i in result.issues],
    }

    return json.dumps(output, indent=2)


@mcp.tool()
def check_secrets(path: str = ".", include_git_history: bool = False) -> str:
    """Scan for hardcoded secrets and credentials.

    Industry-standard secret detection with 700+ patterns and entropy validation.

    Detects: AWS, GCP, Azure, Stripe, GitHub, GitLab, JWT, private keys,
    database credentials, and many more secret types.

    Args:
        path: File or directory to scan for secrets.
        include_git_history: If True, also scan git commit history for secrets
                            that may have been committed and later removed.
    """
    logger.info(f"Checking secrets in: {path}")

    try:
        from qodacode.engines.gitleaks_runner import GitleaksRunner

        gitleaks = GitleaksRunner(scan_git=include_git_history)

        if not gitleaks.is_available():
            return json.dumps({
                "status": "secret_detection_unavailable",
                "message": "Secret detection engine not available.",
                "fallback": "Run: qodacode doctor",
            })

        issues = gitleaks.run(path)

        # Format issues with rich output
        findings = []
        for issue in issues:
            finding = {
                "file": issue.location.filepath,
                "line": issue.location.line,
                "type": issue.rule_id,
                "severity": issue.severity.value,
                "message": issue.message,
                "fix_suggestion": issue.fix_suggestion,
            }
            # Add CWE reference for secrets
            finding["cwe_id"] = "CWE-798"
            finding["cwe_url"] = "https://cwe.mitre.org/data/definitions/798.html"

            # Add snippet (already redacted by GitleaksRunner)
            if issue.snippet:
                finding["snippet"] = issue.snippet

            # Add git context if available
            if issue.context:
                if issue.context.get("commit"):
                    finding["commit"] = issue.context["commit"]
                if issue.context.get("author"):
                    finding["author"] = issue.context["author"]
                if issue.context.get("date"):
                    finding["date"] = issue.context["date"]

            findings.append(finding)

        output = {
            "total_secrets_found": len(findings),
            "secrets": findings,
            "recommendation": (
                "CRITICAL: Rotate all exposed secrets immediately. "
                "Remove from code and git history using git-filter-repo or BFG."
            ) if findings else "No secrets detected. Good job!",
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        logger.error(f"Error in check_secrets: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
        })


@mcp.tool()
def check_dependencies(path: str = ".") -> str:
    """Check dependencies for known vulnerabilities (CVEs).

    Queries real-time vulnerability databases for known security issues
    in your project dependencies.

    Supports: requirements.txt, package.json, Pipfile.lock, package-lock.json

    Args:
        path: Directory containing dependency files.
    """
    from qodacode.osv import (
        find_dependency_files,
        parse_dependency_file,
        query_osv_batch,
    )

    logger.info(f"Checking dependencies in: {path}")

    dep_files = find_dependency_files(path)

    if not dep_files:
        return json.dumps({
            "status": "no_dependency_files",
            "message": "No dependency files found (requirements.txt, package.json, etc.)",
        })

    all_vulnerabilities = []

    for dep_file in dep_files:
        ecosystem, packages = parse_dependency_file(dep_file)
        if not packages:
            continue

        vulns = query_osv_batch(packages, ecosystem)

        for pkg_name, pkg_vulns in vulns.items():
            for vuln in pkg_vulns:
                all_vulnerabilities.append({
                    "package": pkg_name,
                    "ecosystem": ecosystem,
                    "vulnerability_id": vuln.get("id", "unknown"),
                    "summary": vuln.get("summary", "No summary"),
                    "severity": vuln.get("severity", "unknown"),
                    "source_file": str(dep_file),
                })

    output = {
        "files_checked": [str(f) for f in dep_files],
        "total_vulnerabilities": len(all_vulnerabilities),
        "vulnerabilities": all_vulnerabilities,
        "recommendation": "Update vulnerable packages to patched versions."
        if all_vulnerabilities else "No known vulnerabilities found.",
    }

    return json.dumps(output, indent=2)


@mcp.tool()
def list_rules() -> str:
    """List all available analysis rules.

    Returns information about all rules Qodacode can check for,
    including native AST rules and external engines (Gitleaks, Semgrep).

    Total rules: ~4000+ from all engines combined.
    """
    from qodacode.rules.base import RuleRegistry

    # Import rules to register them
    import qodacode.rules.security  # noqa: F401
    import qodacode.rules.robustness  # noqa: F401
    import qodacode.rules.maintainability  # noqa: F401
    import qodacode.rules.operability  # noqa: F401
    import qodacode.rules.dependencies  # noqa: F401

    rules = RuleRegistry.get_all()

    rules_by_category = {}
    for rule in rules:
        cat = rule.category.value
        if cat not in rules_by_category:
            rules_by_category[cat] = []
        rules_by_category[cat].append({
            "id": rule.id,
            "name": rule.name,
            "severity": rule.severity.value,
            "description": rule.description,
            "languages": rule.languages,
        })

    # Qodacode engines provide thousands of additional rules
    qodacode_engines = {
        "secret_detection": {
            "name": "Qodacode Secret Detection",
            "rules_count": 700,
            "description": "700+ patterns for detecting secrets, API keys, tokens, and credentials",
            "categories": ["AWS", "GCP", "Azure", "GitHub", "Stripe", "JWT", "Private Keys", "Database credentials"],
        },
        "deep_sast": {
            "name": "Qodacode Deep SAST",
            "rules_count": 3000,
            "description": "3000+ rules for security, correctness, and best practices",
            "categories": ["SQL Injection", "XSS", "Command Injection", "Path Traversal", "Crypto", "Auth"],
            "languages": ["python", "javascript", "typescript", "go", "java", "ruby", "php", "c", "cpp", "rust"],
        },
        "dependency_scanner": {
            "name": "Qodacode Dependency Scanner",
            "rules_count": "CVE database",
            "description": "Real-time vulnerability database for dependencies",
            "ecosystems": ["PyPI", "npm", "Go", "Cargo", "Maven"],
        },
    }

    native_count = len(rules)
    secret_count = 700
    sast_count = 3000
    total_rules = native_count + secret_count + sast_count

    output = {
        "total_rules": f"{total_rules}+",
        "summary": f"Qodacode provides {total_rules}+ security rules across 4 specialized engines",
        "native_rules": {
            "count": native_count,
            "by_category": rules_by_category,
        },
        "engines": qodacode_engines,
        "coverage": {
            "secret_detection": "700+ patterns",
            "sast_analysis": "3000+ rules",
            "dependency_vulnerabilities": "Real-time CVE database",
            "ast_patterns": f"{native_count} rules",
        },
    }

    return json.dumps(output, indent=2)


@mcp.tool()
def explain_issue(rule_id: str, context: Optional[str] = None) -> str:
    """Get detailed explanation for a specific rule or issue.

    Provides educational information about why an issue matters,
    how to fix it, and examples of correct code.

    Args:
        rule_id: The rule ID (e.g., SEC-001, ROB-002)
        context: Optional code context for more specific advice
    """
    from qodacode.rules.base import RuleRegistry

    # Import rules
    import qodacode.rules.security  # noqa: F401
    import qodacode.rules.robustness  # noqa: F401
    import qodacode.rules.maintainability  # noqa: F401
    import qodacode.rules.operability  # noqa: F401
    import qodacode.rules.dependencies  # noqa: F401

    rule = RuleRegistry.get_by_id(rule_id)

    if not rule:
        return json.dumps({
            "error": f"Rule '{rule_id}' not found",
            "available_rules": [r.id for r in RuleRegistry.get_all()],
        })

    explanation = {
        "rule_id": rule.id,
        "name": rule.name,
        "category": rule.category.value,
        "severity": rule.severity.value,
        "description": rule.description,
        "why_it_matters": _get_why_it_matters(rule.id),
        "how_to_fix": _get_how_to_fix(rule.id),
        "languages": rule.languages,
    }

    return json.dumps(explanation, indent=2)


def _get_why_it_matters(rule_id: str) -> str:
    """Get explanation of why a rule matters."""
    explanations = {
        "SEC-001": "Hardcoded secrets in source code can be exposed through version control, logs, or decompilation. Attackers who gain access to your repository or binaries can use these credentials to access your systems.",
        "SEC-002": "SQL injection allows attackers to execute arbitrary SQL commands, potentially reading, modifying, or deleting data, bypassing authentication, or even executing system commands.",
        "SEC-003": "Command injection allows attackers to execute arbitrary system commands, potentially taking complete control of your server.",
        "SEC-004": "Cross-site scripting (XSS) allows attackers to inject malicious scripts that run in users' browsers, stealing sessions, credentials, or personal data.",
        "SEC-005": "Endpoints without authentication can be accessed by anyone, potentially exposing sensitive data or functionality to unauthorized users.",
        "SEC-006": "Insecure deserialization can allow attackers to execute arbitrary code by crafting malicious serialized objects.",
        "SEC-007": "Path traversal allows attackers to access files outside the intended directory, potentially reading sensitive configuration files or source code.",
        "ROB-001": "Missing error handling causes applications to crash unexpectedly, leading to poor user experience and potential data loss.",
        "ROB-002": "Operations without timeouts can hang indefinitely, consuming resources and making your application unresponsive.",
        "ROB-003": "Unvalidated input can lead to crashes, security vulnerabilities, or incorrect behavior when unexpected data is received.",
        "ROB-004": "Without retry logic, transient failures in external services cause immediate failures instead of graceful recovery.",
        "ROB-005": "Without graceful degradation, a single failing dependency can bring down your entire application.",
        "MNT-001": "Long functions are harder to understand, test, and maintain. They often indicate that a function is doing too many things.",
        "MNT-002": "Functions with many parameters are hard to call correctly and often indicate poor abstraction.",
        "OPS-001": "Without logging, it's nearly impossible to debug production issues or understand application behavior.",
        "OPS-002": "Hardcoded configuration makes it difficult to change settings across environments and may expose sensitive values.",
        "DEP-001": "Vulnerable packages contain known security flaws that attackers can exploit to compromise your application.",
        "DEP-002": "Outdated dependencies may lack security patches and bug fixes, and can become incompatible with other packages.",
        "DEP-003": "Unused dependencies increase attack surface, slow down installation, and add maintenance burden.",
        "DEP-004": "Some licenses (GPL, AGPL) have requirements that may be incompatible with proprietary software.",
    }
    return explanations.get(rule_id, "This rule helps maintain code quality and security.")


def _get_how_to_fix(rule_id: str) -> str:
    """Get fix suggestions for a rule."""
    fixes = {
        "SEC-001": "Use environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.) to store sensitive values. Never commit secrets to version control.",
        "SEC-002": "Use parameterized queries or ORM methods instead of string concatenation. Example: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
        "SEC-003": "Avoid shell commands when possible. If necessary, use subprocess with shell=False and validate/sanitize all inputs. Never pass user input directly to system commands.",
        "SEC-004": "Always escape or sanitize user input before rendering in HTML. Use templating engines with auto-escaping enabled. Set Content-Security-Policy headers.",
        "SEC-005": "Add authentication middleware or decorators to protect sensitive endpoints. Use established auth libraries (OAuth, JWT) rather than rolling your own.",
        "SEC-006": "Avoid deserializing untrusted data. If necessary, use safe serialization formats (JSON) or validate data integrity with signatures before deserialization.",
        "SEC-007": "Validate and sanitize file paths. Use os.path.basename() to extract filenames. Resolve paths and verify they're within allowed directories.",
        "ROB-001": "Wrap risky operations in try/except blocks. Handle specific exceptions appropriately. Always have a fallback for unexpected errors.",
        "ROB-002": "Set explicit timeouts on all network operations, database queries, and external API calls. Use timeout parameters provided by libraries.",
        "ROB-003": "Validate all inputs at system boundaries. Check types, ranges, formats, and lengths. Reject or sanitize invalid input early.",
        "ROB-004": "Implement retry logic with exponential backoff for transient failures. Use libraries like tenacity (Python) or async-retry (Node.js).",
        "ROB-005": "Design systems with fallbacks: cached data, default values, or degraded functionality when dependencies fail.",
        "MNT-001": "Extract logical sections into separate functions. Aim for functions that do one thing well. Use descriptive names for extracted functions.",
        "MNT-002": "Group related parameters into objects or data classes. Consider using builder pattern or configuration objects for complex initialization.",
        "OPS-001": "Add structured logging at appropriate levels (debug, info, warning, error). Include context like request IDs, user IDs, and timestamps.",
        "OPS-002": "Move configuration to environment variables, config files, or a configuration service. Use different configs per environment.",
        "DEP-001": "Update to a patched version of the package. If no patch exists, consider alternatives or implement mitigations.",
        "DEP-002": "Regularly update dependencies. Use tools like dependabot or renovate for automated updates.",
        "DEP-003": "Remove unused dependencies from your package manifest. Use tools to detect unused imports and packages.",
        "DEP-004": "Review license compatibility with your project. Consider alternatives with more permissive licenses if needed.",
    }
    return fixes.get(rule_id, "Review the code and apply best practices for this type of issue.")


@mcp.tool()
def fix_issue(
    file_path: str,
    line: int,
    rule_id: str,
    original_code: Optional[str] = None,
) -> str:
    """Generate a fix for a specific security or quality issue.

    Analyzes the issue and returns corrected code that you can apply.
    This tool does NOT modify files directly - it returns the fix for
    the AI assistant to apply.

    Use this for:
    - Getting fix suggestions for detected issues
    - Learning correct patterns for security issues
    - Auto-remediation workflows

    Args:
        file_path: Path to the file containing the issue.
        line: Line number where the issue was detected.
        rule_id: The rule ID (e.g., SEC-001, ROB-002).
        original_code: Optional - the problematic code snippet for context.

    Returns:
        JSON with the suggested fix, explanation, and corrected code.
    """
    logger.info(f"Generating fix for {rule_id} in {file_path}:{line}")

    # Get fix information
    fix_code = _get_fix_snippet(rule_id, original_code)
    why_matters = _get_why_it_matters(rule_id)
    how_to_fix = _get_how_to_fix(rule_id)

    # Try to read the original line from file for context
    context_lines = []
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            start = max(0, line - 3)
            end = min(len(lines), line + 2)
            context_lines = [
                {"line": i + 1, "code": lines[i].rstrip()}
                for i in range(start, end)
            ]
    except Exception as e:
        logger.warning(f"Could not read file for context: {e}")

    # Generate response
    output = {
        "rule_id": rule_id,
        "file": file_path,
        "line": line,
        "fix_available": fix_code is not None,
        "explanation": {
            "why_it_matters": why_matters,
            "how_to_fix": how_to_fix,
        },
    }

    if fix_code:
        output["suggested_fix"] = fix_code

    if context_lines:
        output["original_context"] = context_lines

    # Add CWE reference if available
    cwe = _get_cwe_id(rule_id)
    if cwe:
        output["cwe_id"] = cwe
        output["cwe_url"] = f"https://cwe.mitre.org/data/definitions/{cwe.split('-')[1]}.html"

    # Add specific fix patterns based on rule
    if rule_id == "SEC-001" or rule_id.startswith("GL-"):
        output["fix_pattern"] = {
            "before": "API_KEY = 'sk-xxx...'",
            "after": "API_KEY = os.getenv('API_KEY')",
            "imports_needed": ["import os"],
        }
    elif rule_id == "SEC-002":
        output["fix_pattern"] = {
            "before": "f\"SELECT * FROM users WHERE id = {user_id}\"",
            "after": "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
            "imports_needed": [],
        }
    elif rule_id == "SEC-003":
        output["fix_pattern"] = {
            "before": "os.system(f'ls {path}')",
            "after": "subprocess.run(['ls', path], shell=False, check=True)",
            "imports_needed": ["import subprocess"],
        }
    elif rule_id == "ROB-002":
        output["fix_pattern"] = {
            "before": "requests.get(url)",
            "after": "requests.get(url, timeout=30)",
            "imports_needed": [],
        }

    return json.dumps(output, indent=2)


@mcp.tool()
def check_typosquatting(path: str = ".") -> str:
    """Detect typosquatting attacks in project dependencies.

    Scans dependency files for packages with names suspiciously similar
    to popular legitimate packages. This is a supply chain security check.

    Detects:
    - Typo variations: "reqeusts" vs "requests"
    - Homoglyph attacks: "fIask" (capital I) vs "flask"
    - Keyboard proximity typos: adjacent key substitutions

    Supports: requirements.txt, package.json, Pipfile, pyproject.toml

    Use this for:
    - Pre-installation security checks
    - CI/CD supply chain gates
    - Auditing new dependencies

    Args:
        path: Directory or file to scan. Defaults to current directory.

    Returns:
        JSON with detected typosquatting attempts and risk levels.
    """
    from qodacode.typosquatting import TyposquattingDetector
    from qodacode.typosquatting.detector import scan_directory, RiskLevel
    from pathlib import Path

    logger.info(f"Checking typosquatting in: {path}")

    target = Path(path)
    matches = []

    if target.is_file():
        detector = TyposquattingDetector()
        file_matches = detector.detect_file(str(target))
        if file_matches:
            matches = file_matches
    else:
        results = scan_directory(str(target))
        for file_path, file_matches in results.items():
            matches.extend(file_matches)

    # Format output
    findings = []
    for match in matches:
        findings.append({
            "suspicious_package": match.suspicious_package,
            "legitimate_package": match.legitimate_package,
            "risk_level": match.risk_level.value,
            "distance": match.distance,
            "reason": match.reason,
            "has_homoglyphs": match.has_homoglyphs,
            "keyboard_typo": match.keyboard_typo_score > 0.5,
        })

    # Sort by risk level
    risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda x: risk_order.get(x["risk_level"], 4))

    # Determine verdict
    critical_count = sum(1 for f in findings if f["risk_level"] == "critical")
    high_count = sum(1 for f in findings if f["risk_level"] == "high")

    if critical_count > 0:
        verdict = "🚨 SUPPLY CHAIN ATTACK DETECTED"
        recommendation = "CRITICAL: Remove malicious packages immediately. Do NOT install."
    elif high_count > 0:
        verdict = "⚠️ SUSPICIOUS PACKAGES FOUND"
        recommendation = "Review packages before installing. Verify correct package names."
    elif findings:
        verdict = "⚡ POSSIBLE TYPOS DETECTED"
        recommendation = "Double-check package names for typos."
    else:
        verdict = "✅ NO TYPOSQUATTING DETECTED"
        recommendation = "All packages appear legitimate."

    output = {
        "verdict": verdict,
        "safe": len(findings) == 0,
        "summary": {
            "total_suspicious": len(findings),
            "critical": critical_count,
            "high": high_count,
            "medium": sum(1 for f in findings if f["risk_level"] == "medium"),
        },
        "findings": findings,
        "recommendation": recommendation,
    }

    return json.dumps(output, indent=2)


@mcp.tool()
def scan_diff(path: str = ".", base: str = "HEAD") -> str:
    """Scan only changed files since the last commit.

    Much faster than full scan - only analyzes files that have been modified.
    Perfect for real-time feedback during AI-assisted coding sessions.

    Detects:
    - Staged changes (git add)
    - Unstaged changes (modified but not added)
    - Untracked files (new files not yet in git)

    Use this for:
    - Quick feedback while coding with AI assistants
    - Pre-commit checks on changed files only
    - Continuous monitoring during development

    Args:
        path: Project directory (must be a git repository).
        base: Git reference to compare against (default: HEAD).

    Returns:
        JSON with issues found in changed files and verdict.
    """
    from qodacode.scanner import Scanner

    logger.info(f"Scanning diff in: {path} (base: {base})")

    # Import rules
    import qodacode.rules.security  # noqa: F401
    import qodacode.rules.robustness  # noqa: F401
    import qodacode.rules.maintainability  # noqa: F401
    import qodacode.rules.operability  # noqa: F401
    import qodacode.rules.dependencies  # noqa: F401

    scanner = Scanner()

    # Get changed files
    changed_files = scanner.get_changed_files(path)

    if not changed_files:
        return json.dumps({
            "verdict": "✅ No changed files to scan",
            "ready_for_production": True,
            "changed_files": 0,
            "issues": [],
        })

    # Scan only changed files
    result = scanner.scan_diff(path)

    # Calculate summary
    summary = calculate_scan_summary(result.issues)

    output = {
        "verdict": summary.message,
        "ready_for_production": summary.ready,
        "changed_files": len(changed_files),
        "files_list": [str(f) for f in changed_files[:20]],  # Limit to first 20
        "summary": {
            "total_issues": summary.total_issues,
            "production": summary.production.to_dict(),
            "tests": summary.tests.to_dict(),
        },
        "issues": [_format_issue(i) for i in result.issues],
    }

    return json.dumps(output, indent=2)


@mcp.tool()
def get_project_health(path: str = ".") -> str:
    """Get overall health assessment of a project.

    Provides a summary of code quality, security posture, and
    actionable recommendations prioritized by impact.

    Args:
        path: Project directory to analyze.
    """
    import json as json_module
    from qodacode.scanner import Scanner
    from qodacode.rules.base import Category, Severity

    # Import rules
    import qodacode.rules.security  # noqa: F401
    import qodacode.rules.robustness  # noqa: F401
    import qodacode.rules.maintainability  # noqa: F401
    import qodacode.rules.operability  # noqa: F401
    import qodacode.rules.dependencies  # noqa: F401

    logger.info(f"Analyzing project health: {path}")

    scanner = Scanner()
    result = scanner.scan(path=path)

    # Calculate health score (0-100)
    # Deduct points based on issues
    score = 100
    score -= result.critical_count * 15
    score -= result.high_count * 8
    score -= result.medium_count * 3
    score -= result.low_count * 1
    score = max(0, score)

    # Determine grade
    if score >= 90:
        grade = "A"
        status = "Excellent"
    elif score >= 80:
        grade = "B"
        status = "Good"
    elif score >= 70:
        grade = "C"
        status = "Needs Improvement"
    elif score >= 60:
        grade = "D"
        status = "Poor"
    else:
        grade = "F"
        status = "Critical"

    # Get top issues to fix
    critical_issues = [i for i in result.issues if i.severity == Severity.CRITICAL][:5]
    high_issues = [i for i in result.issues if i.severity == Severity.HIGH][:5]

    # Count by category
    by_category = result.by_category()

    output = {
        "health_score": score,
        "grade": grade,
        "status": status,
        "summary": {
            "files_analyzed": result.files_scanned,
            "total_issues": len(result.issues),
            "critical": result.critical_count,
            "high": result.high_count,
            "medium": result.medium_count,
            "low": result.low_count,
        },
        "by_category": {
            cat.value: len(issues)
            for cat, issues in by_category.items()
            if issues
        },
        "priority_fixes": [
            {
                "rule": i.rule_id,
                "file": i.filepath,
                "line": i.line,
                "message": i.message,
            }
            for i in (critical_issues + high_issues)
        ],
        "recommendations": _get_recommendations(result),
    }

    return json_module.dumps(output, indent=2)


def _get_recommendations(result) -> list:
    """Generate prioritized recommendations based on scan results."""
    recommendations = []

    if result.critical_count > 0:
        recommendations.append(
            "URGENT: Address critical security issues immediately. "
            "These could allow attackers to compromise your system."
        )

    by_category = result.by_category()
    from qodacode.rules.base import Category

    if len(by_category.get(Category.SECURITY, [])) > 3:
        recommendations.append(
            "Security: Multiple security issues detected. "
            "Consider a security audit and implementing security best practices."
        )

    if len(by_category.get(Category.ROBUSTNESS, [])) > 5:
        recommendations.append(
            "Reliability: Add error handling and timeouts to improve "
            "application stability and resilience."
        )

    if len(by_category.get(Category.DEPENDENCIES, [])) > 0:
        recommendations.append(
            "Dependencies: Update vulnerable packages and set up automated "
            "dependency updates (Dependabot, Renovate)."
        )

    if not recommendations:
        recommendations.append(
            "Good job! Continue maintaining code quality with regular scans."
        )

    return recommendations


# =============================================================================
# PROACTIVE MODE TOOLS (Premium Features)
# =============================================================================


@mcp.tool()
def start_proactive_mode(
    path: str = ".",
    level: str = "passive",
) -> str:
    """Start the Qodacode security daemon for proactive scanning.

    The daemon watches file changes and maintains an issue cache,
    enabling real-time security feedback during development.

    Proactivity Levels:
    - passive: Only responds when called (Free tier)
    - reactive: Suggests scans after file changes (Pro tier)
    - proactive: Auto-scans on save (Team tier)
    - guardian: Blocks dangerous commits (Business tier)

    MANDATORY BEHAVIORS when active:
    1. Before any git commit, call scan_staged()
    2. If critical issues exist, DO NOT proceed until fixed
    3. Check get_realtime_issues() after editing files

    Args:
        path: Project directory to watch.
        level: Proactivity level (passive, reactive, proactive, guardian).

    Returns:
        JSON with daemon status and context for Claude Code.
    """
    from qodacode.daemon import start_daemon, ProactivityLevel

    logger.info(f"Starting proactive mode: {level} for {path}")

    try:
        daemon = start_daemon(path, level)
        status = daemon.get_status()
        context = daemon.get_context_for_claude()

        return json.dumps({
            "status": "daemon_started",
            "proactivity": level,
            "project": str(daemon.project_path),
            "issue_summary": status["issue_summary"],
            "claude_context": context,
            "instructions": [
                "Daemon is now watching for file changes",
                "Use get_realtime_issues() to check current issues",
                "Use scan_staged() before git commit",
                "Use poll_events() to get push notifications",
            ],
        }, indent=2)

    except Exception as e:
        logger.error(f"Error starting daemon: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
        })


@mcp.tool()
def stop_proactive_mode() -> str:
    """Stop the Qodacode security daemon.

    Stops file watching and clears the issue cache.
    Use when done with a coding session.

    Returns:
        JSON confirmation of daemon shutdown.
    """
    from qodacode.daemon import stop_daemon, get_daemon

    daemon = get_daemon()
    if daemon:
        project = str(daemon.project_path)
        stop_daemon()
        return json.dumps({
            "status": "daemon_stopped",
            "project": project,
        }, indent=2)
    else:
        return json.dumps({
            "status": "no_daemon_running",
        }, indent=2)


@mcp.tool()
def get_daemon_status() -> str:
    """Get status of the Qodacode security daemon.

    Shows current state, issue summary, and pending events.
    Use this to check if proactive mode is active.

    Returns:
        JSON with daemon status, issue counts, and health summary.
    """
    from qodacode.daemon import get_daemon

    daemon = get_daemon()
    if not daemon:
        return json.dumps({
            "status": "inactive",
            "message": "No daemon running. Use start_proactive_mode() to enable.",
        }, indent=2)

    status = daemon.get_status()
    context = daemon.get_context_for_claude()

    return json.dumps({
        "status": "active",
        "daemon": status,
        "claude_context": context,
    }, indent=2)


@mcp.tool()
def get_realtime_issues(file_path: Optional[str] = None) -> str:
    """Get security issues from the real-time cache.

    Returns cached issues without rescanning - instant response.
    Issues are updated automatically by the background daemon.

    Use this frequently during coding to get instant feedback.

    Args:
        file_path: Optional specific file to get issues for.
                  If not provided, returns all cached issues.

    Returns:
        JSON with cached issues and summary.
    """
    from qodacode.daemon import get_daemon

    daemon = get_daemon()
    if not daemon:
        return json.dumps({
            "status": "daemon_not_running",
            "message": "Start daemon with start_proactive_mode() first.",
            "issues": [],
        }, indent=2)

    if file_path:
        issues = daemon.issue_cache.get(file_path)
    else:
        issues = daemon.issue_cache.get_all()

    summary = daemon.issue_cache.get_summary()

    # Determine security status
    if summary["critical"] > 0:
        security_status = "CRITICAL - Fix security issues before proceeding"
    elif summary["high"] > 0:
        security_status = "WARNING - Security issues detected"
    elif sum(summary.values()) > 0:
        security_status = f"OK - {sum(summary.values())} minor issues"
    else:
        security_status = "EXCELLENT - No issues detected"

    return json.dumps({
        "security_status": security_status,
        "summary": summary,
        "total_issues": len(issues),
        "issues": [issue.to_dict() for issue in issues],
        "instructions": (
            "Fix critical issues immediately before proceeding."
            if summary["critical"] > 0
            else "Code looks good. Continue working."
        ),
    }, indent=2)


@mcp.tool()
def poll_events(limit: int = 10) -> str:
    """Poll events from the daemon event queue.

    Returns push notifications about file changes, scan results,
    and security alerts. Events are consumed (removed from queue).

    Use this periodically during coding sessions to stay informed.

    Args:
        limit: Maximum number of events to return.

    Returns:
        JSON with queued events and recommended actions.
    """
    from qodacode.daemon import get_daemon

    daemon = get_daemon()
    if not daemon:
        return json.dumps({
            "status": "daemon_not_running",
            "events": [],
        }, indent=2)

    events = daemon.event_queue.pop_all()[:limit]

    # Process events to generate recommended actions
    actions = []
    for event in events:
        if event.event_type == "issues_found":
            data = event.data
            if data.get("critical", 0) > 0:
                actions.append(f"CRITICAL: Fix {data['critical']} critical issues in {data.get('file', 'project')}")
            elif data.get("high", 0) > 0:
                actions.append(f"Review {data['high']} high severity issues in {data.get('file', 'project')}")
        elif event.event_type == "scan_suggested":
            actions.append(event.data.get("message", "Consider running a scan"))
        elif event.event_type == "file_changed":
            actions.append(f"File modified: {event.data.get('file', 'unknown')}")

    return json.dumps({
        "event_count": len(events),
        "events": [e.to_dict() for e in events],
        "recommended_actions": actions if actions else ["No actions required"],
    }, indent=2)


@mcp.tool()
def scan_staged() -> str:
    """Scan git staged files for security issues.

    MANDATORY: Call this before any git commit to ensure
    you're not committing security vulnerabilities.

    In GUARDIAN mode, commits with critical issues are blocked.

    Returns:
        JSON with staged file analysis and commit verdict.
    """
    from qodacode.daemon import get_daemon

    daemon = get_daemon()

    # If daemon not running, do a quick staged scan anyway
    if not daemon:
        # Run manual staged scan
        from qodacode.scanner import Scanner
        import subprocess
        from pathlib import Path

        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
            )
            staged_files = [f for f in result.stdout.strip().split('\n') if f]

            if not staged_files:
                return json.dumps({
                    "status": "ok",
                    "message": "No staged files to scan",
                    "commit_allowed": True,
                }, indent=2)

            # Import rules
            import qodacode.rules.security  # noqa: F401
            import qodacode.rules.robustness  # noqa: F401

            scanner = Scanner()
            all_issues = []

            for file_path in staged_files:
                if Path(file_path).exists():
                    file_result = scanner.scan_file(file_path)
                    all_issues.extend(file_result.issues)

            critical = [i for i in all_issues if i.severity.value == "critical"]
            high = [i for i in all_issues if i.severity.value == "high"]

            return json.dumps({
                "status": "blocked" if critical else "ok",
                "commit_allowed": len(critical) == 0,
                "staged_files": staged_files,
                "total_issues": len(all_issues),
                "critical": len(critical),
                "high": len(high),
                "issues": [_format_issue(i) for i in all_issues[:10]],
                "verdict": (
                    f"BLOCKED: {len(critical)} critical issues. Fix before commit."
                    if critical else
                    f"OK: {len(all_issues)} issues (no critical). Safe to commit."
                ),
            }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
            })

    # Use daemon's scan_staged
    result = daemon.scan_staged()

    return json.dumps({
        **result,
        "commit_allowed": result.get("status") == "ok",
        "verdict": result.get("message"),
    }, indent=2)


@mcp.tool()
def register_file_hook(
    pattern: str,
    action: str = "scan",
    severity_threshold: str = "critical",
) -> str:
    """Register a hook for specific file patterns.

    Hooks trigger automatic actions when matching files change.
    Useful for enforcing security policies on sensitive files.

    Examples:
    - "*.py" with action="scan" - scan all Python files on change
    - "src/auth/*" with action="alert" - alert on auth changes
    - "*.env*" with action="block" - block committing env files

    Args:
        pattern: Glob pattern to match files (e.g., "*.py", "src/**/*.ts")
        action: Action to take: "scan", "alert", or "block"
        severity_threshold: Minimum severity to trigger (critical, high, medium, low)

    Returns:
        JSON confirmation of hook registration.
    """
    from qodacode.daemon import get_daemon

    daemon = get_daemon()
    if not daemon:
        return json.dumps({
            "status": "error",
            "message": "Daemon not running. Start with start_proactive_mode() first.",
        })

    daemon.register_hook(
        pattern=pattern,
        action=action,
        severity_threshold=severity_threshold,
    )

    return json.dumps({
        "status": "hook_registered",
        "pattern": pattern,
        "action": action,
        "severity_threshold": severity_threshold,
        "message": f"Files matching '{pattern}' will trigger {action} action.",
    }, indent=2)


@mcp.tool()
def analyze_command_safety(
    command: str,
    tool_name: str = "bash",
) -> str:
    """Analyze command safety for PreToolUse hook integration.

    This tool is designed for integration with Claude Code's PreToolUse hook.
    It analyzes commands before execution to detect:
    - Dangerous patterns (rm -rf, sudo, etc.)
    - Encoding bypass attempts (base64, hex, URL encoding)
    - Environment variable manipulation
    - Command obfuscation
    - Pipe chains and command substitution

    Use this BEFORE executing any bash/shell commands from AI agents.

    Args:
        command: The command to analyze
        tool_name: Tool being used (bash, python, etc.)

    Returns:
        JSON with safety verdict and suggestions
    """
    from qodacode.security_hooks import analyze_command, suggest_safe_alternative
    from qodacode.audit_log import AuditLogger

    is_safe, reason = analyze_command(command, tool_name)

    output = {
        "safe": is_safe,
        "reason": reason,
        "command": command[:100] + "..." if len(command) > 100 else command,
        "tool": tool_name,
    }

    if not is_safe:
        # Add safe alternative if available
        alternative = suggest_safe_alternative(command)
        if alternative:
            output["safe_alternative"] = alternative

        # Log the block
        audit_logger = AuditLogger()
        audit_logger.log_block(
            tool_name=tool_name,
            reason=reason,
            details={"command": command[:200]},
        )

        output["recommendation"] = "BLOCK: This command appears dangerous and should not be executed."
    else:
        output["recommendation"] = "ALLOW: Command appears safe to execute."

    return json.dumps(output, indent=2)


@mcp.tool()
def get_security_context() -> str:
    """Get comprehensive security context for the current project.

    Returns all information needed for Claude Code to make
    security-aware decisions during coding.

    This is the primary tool for understanding the security
    posture before making code changes.

    Returns:
        JSON with security status, recent issues, and mandatory actions.
    """
    from qodacode.daemon import get_daemon

    daemon = get_daemon()

    if daemon:
        context = daemon.get_context_for_claude()
        summary = daemon.issue_cache.get_summary()
        status = daemon.get_status()

        return json.dumps({
            "daemon_active": True,
            "proactivity_level": status["proactivity"],
            "security_status": context,
            "issue_summary": summary,
            "total_cached_issues": status["total_cached_issues"],
            "pending_events": status["pending_events"],
            "mandatory_actions": [
                "Call scan_staged() before git commit",
                "Fix critical issues before proceeding",
                "Check get_realtime_issues() after editing files",
            ],
        }, indent=2)

    # Daemon not running - return basic context
    return json.dumps({
        "daemon_active": False,
        "security_status": "UNKNOWN - Daemon not active",
        "recommendation": "Start daemon with start_proactive_mode() for real-time security feedback.",
        "mandatory_actions": [
            "Run full_audit() before major deployments",
            "Use check_secrets() to find credentials",
            "Use check_typosquatting() before adding dependencies",
        ],
    }, indent=2)


def main():
    """Run the MCP server."""
    logger.info("Starting Qodacode MCP server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

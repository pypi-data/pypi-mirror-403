"""
Qodacode Reporter - Rich terminal output.

Provides formatted output for scan results, status, and messages.
Supports Junior/Senior modes for adaptive learning.

Phase 6.2: Terminal UX Premium Cards
- Visual card-style issue display
- Severity color bands and category icons
- Progress indicators
- Grouped by file with visual separators
- Syntax-highlighted code snippets
- Summary dashboard at end
"""

from collections import defaultdict
from typing import Dict, Any, Optional, List

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

from qodacode.scanner import ScanResult
from qodacode.rules.base import Severity, Category, RuleRegistry, EngineSource
from qodacode.utils.masking import mask_snippet_for_issue
from qodacode.utils.verdict import (
    calculate_scan_summary,
    sort_issues_by_severity,
    group_issues_by_file,
    QODACODE_ORANGE,
)


# Visual indicators for severity levels
SEVERITY_ICONS = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH: "🟠",
    Severity.MEDIUM: "🟡",
    Severity.LOW: "🔵",
    Severity.INFO: "⚪",
}

SEVERITY_COLORS = {
    Severity.CRITICAL: "red",
    Severity.HIGH: "dark_orange",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "blue",
    Severity.INFO: "dim",
}

SEVERITY_LABELS = {
    Severity.CRITICAL: "CRITICAL",
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MEDIUM",
    Severity.LOW: "LOW",
    Severity.INFO: "INFO",
}

# Category icons
CATEGORY_ICONS = {
    Category.SECURITY: "🔒",
    Category.ROBUSTNESS: "🛡️",
    Category.MAINTAINABILITY: "🔧",
    Category.OPERABILITY: "⚙️",
    Category.DEPENDENCIES: "📦",
}

# Engine badges
ENGINE_BADGES = {
    EngineSource.TREESITTER: "[dim]AST[/dim]",
    EngineSource.SEMGREP: "[magenta]SG[/magenta]",
    EngineSource.GITLEAKS: "[red]GL[/red]",
    EngineSource.OSV: "[cyan]OSV[/cyan]",
}


# Enterprise knowledge database for Junior mode
ENTERPRISE_KNOWLEDGE = {
    "SEC-001": {
        "why": "Hardcoded secrets are the #1 cause of data breaches. Once in git, they're compromised forever.",
        "impact": "Uber (2022): $148M fine after hardcoded AWS keys leaked. Attackers scan GitHub every minute.",
        "patterns": {
            "Stripe": "HashiCorp Vault with automatic 24h rotation",
            "Netflix": "Environment injection via Spinnaker, never in code",
            "Google": "Secret Manager with IAM policies",
        },
        "learn": "https://owasp.org/www-community/vulnerabilities/Hardcoded_Secrets",
    },
    "SEC-002": {
        "why": "SQL injection allows attackers to read/modify/delete your entire database.",
        "impact": "Heartland (2008): 130M cards stolen via SQL injection. Still in OWASP Top 10.",
        "patterns": {
            "Stripe": "Always parameterized queries, no string building",
            "Shopify": "ORM-only access, raw SQL prohibited",
            "GitHub": "Query builders with automatic escaping",
        },
        "learn": "https://owasp.org/www-community/attacks/SQL_Injection",
    },
    "SEC-003": {
        "why": "Command injection = full server takeover. Attacker can run any system command.",
        "impact": "Equifax (2017): 147M records via command injection. $700M settlement.",
        "patterns": {
            "AWS": "Lambda with minimal IAM, no shell access",
            "Google": "gVisor sandboxing for all containers",
            "Cloudflare": "Workers isolates with no system access",
        },
        "learn": "https://owasp.org/www-community/attacks/Command_Injection",
    },
    "ROB-001": {
        "why": "Unhandled errors crash your service. In production, everything fails eventually.",
        "impact": "Knight Capital (2012): $440M lost in 45 min from unhandled error cascade.",
        "patterns": {
            "Netflix": "Hystrix circuit breakers on all calls",
            "Amazon": "Every call has timeout + retry + fallback",
            "Stripe": "Idempotency keys for safe retries",
        },
        "learn": "https://docs.microsoft.com/en-us/azure/architecture/patterns/retry",
    },
    "ROB-002": {
        "why": "No timeout = hung service. One slow dependency can block all your threads.",
        "impact": "AWS S3 outage (2017): Services without timeouts cascaded failure globally.",
        "patterns": {
            "Netflix": "Default 1s timeout, max 30s for batch",
            "Google": "Deadline propagation across all services",
            "Stripe": "30s default, configurable per endpoint",
        },
        "learn": "https://microservices.io/patterns/reliability/timeout.html",
    },
    "DEP-001": {
        "why": "Vulnerable dependencies = easy attack vector. Attackers scan for known CVEs.",
        "impact": "Log4Shell (2021): Affected 93% of enterprise clouds. Trivial remote code execution.",
        "patterns": {
            "Google": "OSV database, automated PR for updates",
            "Microsoft": "Dependabot + mandatory security reviews",
            "Netflix": "Automated CVE scanning in CI, blocks deploy",
        },
        "learn": "https://owasp.org/www-project-dependency-check/",
    },
}


class Reporter:
    """Rich-based reporter for terminal output."""

    def __init__(self):
        self.console = Console()

    def info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"[blue]ℹ[/blue] {message}")

    def success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[green]✓[/green] {message}")

    def warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"[red]✗[/red] {message}")

    def section(self, title: str) -> None:
        """Print section header."""
        self.console.print(f"\n[bold]{title}[/bold]")
        self.console.print("─" * len(title))

    def newline(self) -> None:
        """Print empty line."""
        self.console.print()

    def rule_info(
        self,
        rule_id: str,
        name: str,
        severity: str,
        description: str,
        severity_color: str = "white",
    ) -> None:
        """Print rule information."""
        self.console.print(
            f"  [{severity_color}]{rule_id}[/{severity_color}] "
            f"[dim]{name}[/dim] - {description}"
        )

    def report_scan_result(
        self,
        result: ScanResult,
        show_fixes: bool = False,
        mode: str = "senior"
    ) -> None:
        """Print scan results with Rich formatting.

        Phase 6.1: Groups by file, shows syntax-highlighted snippets.

        Args:
            result: Scan results to display
            show_fixes: Whether to show fix suggestions
            mode: "junior" for learning mode, "senior" for terse output
        """
        is_junior = mode == "junior"

        # Premium header panel
        if result.issues:
            if result.critical_count > 0:
                header_style = "red"
                header_icon = "🚨"
            elif result.high_count > 0:
                header_style = "dark_orange"
                header_icon = "⚠️"
            else:
                header_style = "yellow"
                header_icon = "📋"

            header_text = f"{header_icon} [bold]QODACODE ANALYSIS[/bold]\n"
            header_text += f"[dim]Found {len(result.issues)} issue(s) in {result.files_scanned} files[/dim]"
            if is_junior:
                header_text += "\n[cyan]💡 Learning mode: detailed explanations included[/cyan]"
        else:
            header_style = "green"
            header_text = "✨ [bold]QODACODE ANALYSIS[/bold]\n"
            header_text += f"[green]All clear! No issues found in {result.files_scanned} files[/green]"

        self.console.print(Panel(
            header_text,
            border_style=header_style,
            box=box.DOUBLE,
            padding=(0, 1),
        ))

        if not result.issues:
            self.console.print(Panel(
                "[green bold]✨ CODE CLEAN & SECURE[/green bold]\n[dim]Ready for production deployment[/dim]",
                border_style="green",
                box=box.DOUBLE,
                padding=(1, 2),
            ))
            return

        # Group issues by file using shared utility (sorted by severity)
        by_file = group_issues_by_file(result.issues)
        sorted_files = list(by_file.keys())

        # Print issues grouped by file (already sorted by severity)
        for filepath in sorted_files:
            issues = by_file[filepath]
            # Issues already sorted by severity within group_issues_by_file

            # Count severity for this file
            file_critical = sum(1 for i in issues if i.severity == Severity.CRITICAL)
            file_high = sum(1 for i in issues if i.severity == Severity.HIGH)

            # File header with severity indicator
            if file_critical > 0:
                file_style = "red"
                file_icon = "🔴"
            elif file_high > 0:
                file_style = "dark_orange"
                file_icon = "🟠"
            else:
                file_style = "blue"
                file_icon = "📄"

            # File section header as a subtle panel
            file_header = f"{file_icon} [bold]{filepath}[/bold] [dim]({len(issues)} issues)[/dim]"
            self.console.print()
            self.console.print(f"╭─ {file_header}")
            self.console.print(f"│")

            for issue in issues:
                self._print_issue_compact(issue, show_fixes, is_junior)

            self.console.print(f"╰{'─' * 40}")

        # Summary table at end
        self._print_summary_table(result)

    def _print_issue(
        self,
        issue,
        style: str,
        show_fix: bool,
        is_junior: bool = False
    ) -> None:
        """Print a single issue with optional learning content."""
        # Location
        location = f"{issue.location.filepath}:{issue.location.line}"

        # Engine attribution per COMMERCIAL_GUIDELINES.md
        engine_name = getattr(issue, 'engine', EngineSource.TREESITTER).value
        engine_tag = f"[dim][Source: {engine_name}][/dim]"

        self.console.print(f"\n[{style}]●[/{style}] [{style}]{issue.rule_id}[/{style}] {location} {engine_tag}")
        self.console.print(f"  [bold]{issue.rule_name}[/bold]")
        self.console.print(f"  [dim]→[/dim] {issue.message}")

        # Show code snippet (MASKED for security)
        if issue.snippet:
            safe_snippet = mask_snippet_for_issue(
                issue.snippet,
                issue.rule_id,
                engine_name
            )
            snippet = safe_snippet
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            self.console.print(f"  [dim]{snippet}[/dim]")

        # JUNIOR MODE: Show educational content
        if is_junior and issue.rule_id in ENTERPRISE_KNOWLEDGE:
            knowledge = ENTERPRISE_KNOWLEDGE[issue.rule_id]
            self.console.print()
            self.console.print(f"  [cyan bold]WHY THIS MATTERS:[/cyan bold]")
            self.console.print(f"  [cyan]{knowledge['why']}[/cyan]")
            self.console.print()
            self.console.print(f"  [yellow bold]REAL IMPACT:[/yellow bold]")
            self.console.print(f"  [yellow]{knowledge['impact']}[/yellow]")
            self.console.print()
            self.console.print(f"  [green bold]ENTERPRISE PATTERNS:[/green bold]")
            for company, pattern in knowledge["patterns"].items():
                self.console.print(f"  [green]• {company}:[/green] {pattern}")
            if knowledge.get("learn"):
                self.console.print()
                self.console.print(f"  [blue]Learn more:[/blue] {knowledge['learn']}")

        # Show fix suggestion (always in junior, optional in senior)
        if issue.fix_suggestion and (is_junior or show_fix):
            self.console.print()
            self.console.print(f"  [green bold]FIX:[/green bold] {issue.fix_suggestion}")

    def report_status(
        self,
        path: str,
        files_scanned: int,
        result: ScanResult,
        index_data: Dict[str, Any],
    ) -> None:
        """Print project status."""

        self.console.print(Panel(
            f"[bold]QODACODE STATUS[/bold]\n{path}",
            box=box.ROUNDED,
        ))

        # Stats table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Label", style="dim")
        table.add_column("Value")

        table.add_row("Files indexed", str(files_scanned))
        table.add_row("Version", index_data.get("version", "unknown"))

        self.console.print(table)

        # Issues summary
        self.console.print("\n[bold]Issues Summary[/bold]")

        if not result.issues:
            self.console.print("[green]✓ No issues found - ready for production![/green]")
        else:
            issues_table = Table(show_header=True, box=box.SIMPLE)
            issues_table.add_column("Severity", style="bold")
            issues_table.add_column("Count", justify="right")

            if result.critical_count:
                issues_table.add_row("[red]Critical[/red]", str(result.critical_count))
            if result.high_count:
                issues_table.add_row("[yellow]High[/yellow]", str(result.high_count))
            if result.medium_count:
                issues_table.add_row("[blue]Medium[/blue]", str(result.medium_count))
            if result.low_count:
                issues_table.add_row("[dim]Low[/dim]", str(result.low_count))

            self.console.print(issues_table)

            if result.critical_count > 0:
                self.console.print(
                    "\n[red]⚠ Critical issues must be fixed before production[/red]"
                )
                self.console.print("[dim]Run 'qodacode check --fix' to see suggestions[/dim]")

    def _print_issue_compact(
        self,
        issue,
        show_fix: bool,
        is_junior: bool = False
    ) -> None:
        """Print a single issue as a visual card with syntax highlighting."""
        # Get visual elements
        severity = issue.severity
        color = SEVERITY_COLORS.get(severity, "white")
        icon = SEVERITY_ICONS.get(severity, "○")
        label = SEVERITY_LABELS.get(severity, "???")
        category_icon = CATEGORY_ICONS.get(issue.category, "")
        engine = getattr(issue, 'engine', EngineSource.TREESITTER)
        engine_badge = ENGINE_BADGES.get(engine, f"[dim]{engine.value}[/dim]")
        engine_name = engine.value

        # Build card content
        card_lines = []

        # Header line: severity + rule + location
        header = (
            f"{icon} [{color} bold]{label}[/{color} bold] "
            f"[bold]{issue.rule_id}[/bold] "
            f"[dim]L{issue.location.line}[/dim] "
            f"{category_icon} {engine_badge}"
        )
        card_lines.append(header)

        # Message
        card_lines.append(f"[{color}]→[/{color}] {issue.message}")

        # Syntax-highlighted snippet (MASKED for security)
        if issue.snippet:
            safe_snippet = mask_snippet_for_issue(
                issue.snippet,
                issue.rule_id,
                engine_name
            )
            snippet = safe_snippet.strip()
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."

            lexer = self._get_lexer_for_file(issue.location.filepath)
            syntax = Syntax(
                snippet,
                lexer,
                theme="monokai",
                line_numbers=False,
                word_wrap=True,
                background_color="default",
            )
            # Print card header first
            self.console.print(Panel(
                "\n".join(card_lines),
                border_style=color,
                box=box.ROUNDED,
                padding=(0, 1),
            ))
            # Then snippet inside
            self.console.print(f"    ", end="")
            self.console.print(syntax)
        else:
            self.console.print(Panel(
                "\n".join(card_lines),
                border_style=color,
                box=box.ROUNDED,
                padding=(0, 1),
            ))

        # JUNIOR MODE: Educational panel
        if is_junior and issue.rule_id in ENTERPRISE_KNOWLEDGE:
            knowledge = ENTERPRISE_KNOWLEDGE[issue.rule_id]
            edu_content = []
            edu_content.append(f"[cyan bold]WHY:[/cyan bold] {knowledge['why']}")
            edu_content.append(f"[yellow bold]IMPACT:[/yellow bold] {knowledge['impact']}")
            if knowledge.get("learn"):
                edu_content.append(f"[blue]📚 Learn:[/blue] {knowledge['learn']}")

            self.console.print(Panel(
                "\n".join(edu_content),
                title="[bold]💡 Learn[/bold]",
                title_align="left",
                border_style="cyan",
                box=box.SIMPLE,
                padding=(0, 1),
            ))

        # Fix suggestion panel
        if issue.fix_suggestion and (is_junior or show_fix):
            self.console.print(Panel(
                f"[green]{issue.fix_suggestion}[/green]",
                title="[bold green]✓ Fix[/bold green]",
                title_align="left",
                border_style="green",
                box=box.SIMPLE,
                padding=(0, 1),
            ))

    def _get_lexer_for_file(self, filepath: str) -> str:
        """Get the appropriate syntax lexer based on file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "jsx",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
            ".sh": "bash",
            ".bash": "bash",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".rb": "ruby",
            ".php": "php",
        }
        for ext, lexer in ext_map.items():
            if filepath.endswith(ext):
                return lexer
        return "text"

    def _print_summary_table(self, result: ScanResult) -> None:
        """Print a premium summary dashboard at the end of the report.

        Uses unified verdict logic (same as TUI):
        - 0 critical = READY FOR PRODUCTION
        - 1+ critical = NOT READY
        - HIGH/MEDIUM/LOW are warnings, not blockers
        """
        self.console.print()

        # Calculate scan summary (production + tests separated)
        summary = calculate_scan_summary(result.issues)

        # Create severity breakdown as visual bars (production files)
        prod_total = summary.production.total
        bars = []

        if summary.production.critical:
            pct = (summary.production.critical / prod_total) * 100 if prod_total > 0 else 0
            bars.append(f"🔴 [red bold]CRITICAL[/red bold] {summary.production.critical} ({pct:.0f}%)")
        if summary.production.high:
            pct = (summary.production.high / prod_total) * 100 if prod_total > 0 else 0
            bars.append(f"🟠 [{QODACODE_ORANGE} bold]HIGH[/{QODACODE_ORANGE} bold] {summary.production.high} ({pct:.0f}%)")
        if summary.production.medium:
            pct = (summary.production.medium / prod_total) * 100 if prod_total > 0 else 0
            bars.append(f"🟡 [yellow]MEDIUM[/yellow] {summary.production.medium} ({pct:.0f}%)")
        if summary.production.low:
            pct = (summary.production.low / prod_total) * 100 if prod_total > 0 else 0
            bars.append(f"🔵 [blue]LOW[/blue] {summary.production.low} ({pct:.0f}%)")

        # Summary content
        summary_lines = []
        summary_lines.append(f"[bold]📊 Scan Complete[/bold]")
        summary_lines.append(f"[dim]Files scanned:[/dim] {result.files_scanned}")
        summary_lines.append("")
        summary_lines.append(f"[bold]Production:[/bold] {prod_total} issues")
        summary_lines.extend(bars)

        # Test file issues (if any)
        if summary.tests.total > 0:
            summary_lines.append("")
            summary_lines.append(f"[dim]Tests (excluded from verdict):[/dim] {summary.tests.total} issues")
            summary_lines.append(f"[dim]  🔴 {summary.tests.critical}  🟠 {summary.tests.high}  🟡 {summary.tests.medium}  🔵 {summary.tests.low}[/dim]")

        # The Verdict - UNIFIED with TUI/CLI/MCP
        if summary.ready:
            if summary.production.high > 0:
                verdict = f"[green bold]✅ READY FOR PRODUCTION[/green bold] [dim]({summary.production.high} warnings)[/dim]"
            else:
                verdict = "[green bold]✅ READY FOR PRODUCTION[/green bold]"
            verdict_msg = "No critical issues in production code"
            verdict_style = "green"
        else:
            verdict = f"[red bold]⛔ NOT READY[/red bold] — Fix {summary.production.critical} critical issues"
            verdict_msg = "Critical issues must be fixed before production"
            verdict_style = "red"

        summary_lines.append("")
        summary_lines.append(verdict)
        summary_lines.append(f"[dim]{verdict_msg}[/dim]")

        # Print as a panel
        self.console.print(Panel(
            "\n".join(summary_lines),
            title=f"[bold {QODACODE_ORANGE}]🎯 Summary[/bold {QODACODE_ORANGE}]",
            title_align="left",
            border_style=verdict_style,
            box=box.DOUBLE,
            padding=(1, 2),
        ))

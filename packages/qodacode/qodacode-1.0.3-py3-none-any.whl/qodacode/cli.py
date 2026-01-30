"""
Qodacode CLI - Command line interface.

Commands:
- init: Index repository and create .qodacode/
- check: Scan code for issues
- status: Show project status
- git-history: Scan git history for secrets
- watch: Real-time file monitoring
"""

import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from qodacode import __version__
from qodacode.scanner import Scanner, ScanResult
from qodacode.rules.base import Severity, Category, RuleRegistry
from qodacode.reporter import Reporter
from qodacode.utils.verdict import QODACODE_ORANGE


# ─────────────────────────────────────────────────────────────────────────────
# GRACEFUL SHUTDOWN HANDLER (Phase 5.2)
# ─────────────────────────────────────────────────────────────────────────────
_shutdown_requested = False


def _signal_handler(signum: int, frame) -> None:
    """
    Handle Ctrl+C (SIGINT) gracefully.

    First press: Request graceful shutdown, show message
    Second press: Force exit immediately
    """
    global _shutdown_requested

    if _shutdown_requested:
        # Second Ctrl+C - force exit
        console.print("\n[bold red]Force quit.[/bold red]")
        sys.exit(130)  # Standard exit code for SIGINT

    _shutdown_requested = True
    console.print("\n[yellow]⚠ Interrupt received. Finishing current task...[/yellow]")
    console.print("[dim]Press Ctrl+C again to force quit.[/dim]")


def is_shutdown_requested() -> bool:
    """Check if graceful shutdown was requested."""
    return _shutdown_requested


# Register signal handler
signal.signal(signal.SIGINT, _signal_handler)


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL EXCEPTION HANDLER (Phase 5.3)
# ─────────────────────────────────────────────────────────────────────────────
def _write_crash_log(exc_type, exc_value, exc_tb) -> Optional[str]:
    """
    Write crash details to .qodacode/crash.log

    Returns the path to the crash log if written, None otherwise.
    """
    import traceback
    from datetime import datetime

    try:
        crash_dir = Path(".qodacode")
        crash_dir.mkdir(exist_ok=True)
        crash_file = crash_dir / "crash.log"

        crash_info = [
            f"═══ QODACODE CRASH REPORT ═══",
            f"Timestamp: {datetime.now().isoformat()}",
            f"Version: {__version__}",
            f"Python: {sys.version}",
            f"Platform: {sys.platform}",
            f"",
            f"Exception: {exc_type.__name__}: {exc_value}",
            f"",
            f"Traceback:",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        ]

        with open(crash_file, "a") as f:
            f.write("\n".join(crash_info))
            f.write("\n\n")

        return str(crash_file)
    except Exception:
        return None


def _global_exception_handler(exc_type, exc_value, exc_tb):
    """
    Global exception handler for unhandled exceptions.

    - Writes crash log
    - Shows user-friendly error message
    - Exits with error code
    """
    # Don't handle KeyboardInterrupt here (signal handler does that)
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    # Write crash log
    crash_path = _write_crash_log(exc_type, exc_value, exc_tb)

    # Show user-friendly message
    console.print("\n[bold red]╔═══════════════════════════════════════╗[/bold red]")
    console.print("[bold red]║        UNEXPECTED ERROR               ║[/bold red]")
    console.print("[bold red]╚═══════════════════════════════════════╝[/bold red]")
    console.print(f"\n[red]{exc_type.__name__}:[/red] {exc_value}")

    if crash_path:
        console.print(f"\n[dim]Crash details saved to: {crash_path}[/dim]")
        console.print("[dim]Please include this file when reporting bugs.[/dim]")

    console.print("\n[yellow]Report issues at:[/yellow] https://github.com/qodacode/qodacode/issues")

    sys.exit(1)


# Register global exception handler
sys.excepthook = _global_exception_handler


# ─────────────────────────────────────────────────────────────────────────────


# Initialize scanner globally for reuse (with persistent cache)
scanner = Scanner(persistent_cache=True, project_path=".")
reporter = Reporter()
console = Console()


# ASCII Banner - static, compatible with all terminals
BANNER = r"""
   ___   ___  ____    _    ____ ___  ____  _____
  / _ \ / _ \|  _ \  / \  / ___/ _ \|  _ \| ____|
 | | | | | | | | | |/ _ \| |  | | | | | | |  _|
 | |_| | |_| | |_| / ___ \ |__| |_| | |_| | |___
  \__\_\\___/|____/_/   \_\____\___/|____/|_____|
"""


def show_banner():
    """Display the Qodacode banner - static, compatible with all terminals."""
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")
    console.print(
        f"  [bold green]v{__version__}[/bold green]  "
        "[yellow]|[/yellow]  "
        "[bold white]Functional code[/bold white] [dim]to[/dim] "
        "[bold green]enterprise production[/bold green]\n"
    )


def show_welcome():
    """Display welcome message with quick start guide."""
    console.print("[bold white]Quick Start:[/bold white]\n")

    console.print("  [cyan]1.[/cyan] Quick scan:")
    console.print("     [dim]$[/dim] [green]qodacode scan[/green]\n")

    console.print("  [cyan]2.[/cyan] Full security suite:")
    console.print("     [dim]$[/dim] [green]qodacode scan --full[/green]\n")

    console.print("  [cyan]3.[/cyan] Save report:")
    console.print("     [dim]$[/dim] [green]qodacode scan --save[/green]\n")

    console.print("[bold white]Scan Modes:[/bold white]\n")
    console.print("  [yellow]--mode senior[/yellow]  [dim](default)[/dim]  Concise output")
    console.print("  [yellow]--mode junior[/yellow]            Learn while fixing\n")

    console.print("[bold white]Other Commands:[/bold white]\n")
    console.print("  [green]qodacode check[/green]        [dim]Advanced scan with more options[/dim]")
    console.print("  [green]qodacode doctor[/green]       [dim]Check system health[/dim]")
    console.print("  [green]qodacode status[/green]       [dim]Show project health[/dim]")
    console.print("  [green]qodacode watch[/green]        [dim]Real-time monitoring[/dim]")
    console.print()
    console.print("[dim]Run 'qodacode --help' for all options.[/dim]\n")


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="qodacode")
@click.option("--no-banner", is_flag=True, hidden=True, help="Hide banner")
@click.option("--classic", is_flag=True, help="Use classic CLI mode instead of interactive")
@click.pass_context
def main(ctx, no_banner, classic):
    """Qodacode - Take your code from functional to enterprise production.

    Detects exactly what line, variable, or configuration will break your deploy.
    """
    ctx.ensure_object(dict)

    # If no subcommand provided, launch interactive mode
    if ctx.invoked_subcommand is None:
        if classic:
            # Classic mode: show banner and help
            if not no_banner:
                show_banner()
            show_welcome()
        else:
            # Interactive mode
            from qodacode.interactive import run_interactive
            run_interactive(".")


@main.command()
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Path to repository (default: current directory)"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Force re-indexing even if .qodacode exists"
)
def init(path: str, force: bool):
    """Initialize Qodacode for a repository.

    Creates .qodacode/ directory with indexes and configuration.
    """
    qodacode_dir = Path(path) / ".qodacode"

    if qodacode_dir.exists() and not force:
        reporter.warning(f".qodacode/ already exists. Use --force to re-index.")
        return

    reporter.info("Initializing Qodacode...")

    # Create directory structure
    qodacode_dir.mkdir(exist_ok=True)
    (qodacode_dir / "cache").mkdir(exist_ok=True)

    # Run initial scan to warm up cache
    reporter.info("Scanning repository...")
    result = scanner.scan(path)

    # Save index metadata
    index_data = {
        "version": __version__,
        "files_scanned": result.files_scanned,
        "issues_found": len(result.issues),
        "path": os.path.abspath(path),
    }

    with open(qodacode_dir / "index.json", "w") as f:
        json.dump(index_data, f, indent=2)

    # Create default config
    config_data = {
        "exclude": [
            ".git",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
        ],
        "severity_threshold": "medium",
        "categories": ["security", "robustness", "maintainability", "operability", "dependencies"],
    }

    with open(qodacode_dir / "config.json", "w") as f:
        json.dump(config_data, f, indent=2)

    reporter.success(f"Initialized Qodacode")
    reporter.info(f"  Files scanned: {result.files_scanned}")
    reporter.info(f"  Issues found: {len(result.issues)}")
    reporter.info(f"  Config: .qodacode/config.json")


@main.command()
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Path to scan (default: current directory)"
)
@click.option(
    "--severity", "-s",
    type=click.Choice(["critical", "high", "medium", "low", "all"]),
    default="all",
    help="Minimum severity to report"
)
@click.option(
    "--category", "-c",
    type=click.Choice(["security", "robustness", "maintainability", "operability", "dependencies", "all"]),
    default="all",
    help="Category to check"
)
@click.option(
    "--format", "-f",
    "output_format",
    type=click.Choice(["terminal", "json", "sarif", "markdown"]),
    default="terminal",
    help="Output format: terminal (rich), json (machine-readable), sarif (GitHub Security), markdown (PR comments)"
)
@click.option(
    "--fix",
    is_flag=True,
    help="Show fix suggestions"
)
@click.option(
    "--mode", "-m",
    type=click.Choice(["junior", "senior"]),
    default="senior",
    help="Output mode: junior (learn while fixing) or senior (just facts)"
)
@click.option(
    "--deep",
    is_flag=True,
    help="Deep SAST analysis (advanced static analysis)"
)
@click.option(
    "--secrets",
    is_flag=True,
    help="Scan for hardcoded secrets and credentials"
)
@click.option(
    "--deps",
    is_flag=True,
    help="Scan dependencies for known vulnerabilities"
)
@click.option(
    "--all", "scan_all",
    is_flag=True,
    help="Full security suite (all engines)"
)
@click.option(
    "--skip-missing",
    is_flag=True,
    help="Skip missing engines silently (for CI/CD, no interactive prompts)"
)
@click.option(
    "--export", "-e",
    is_flag=True,
    help="Export results to file (auto-generates qodacode-report-TIMESTAMP.txt)"
)
@click.option(
    "--baseline", "-b",
    is_flag=True,
    help="Only show NEW issues not in baseline (run 'qodacode baseline save' first)"
)
def check(path: str, severity: str, category: str, output_format: str, fix: bool, mode: str, deep: bool, secrets: bool, deps: bool, scan_all: bool, skip_missing: bool, export: bool, baseline: bool):
    """Qodacode Security Scanner.

    Enterprise-grade code analysis: SAST, Secrets, and Supply Chain
    security in a single command. OWASP Top 10 compliant.

    Scan modes:
      (default)     Instant structural analysis (<50ms)
      --deep        Advanced SAST analysis
      --secrets     Credential and secret detection
      --deps        Dependency vulnerability scanning
      --all         Full security suite

    Output modes:
      --mode junior    Learn while fixing (explanations)
      --mode senior    Just the facts (concise)

    CI/CD:
      --skip-missing   Skip unavailable engines silently
      --format json    Machine-readable output
      --format sarif   GitHub Security compatible

    Examples:
      qodacode check                       # Quick scan
      qodacode check --all                 # Full security suite
      qodacode check --all --skip-missing  # CI/CD mode
    """
    from qodacode.rate_limiter import RateLimiter
    from qodacode.audit_log import AuditLogger

    # Initialize rate limiter and audit logger
    rate_limiter = RateLimiter.from_project(path)
    audit_logger = AuditLogger(project_root=path)

    # Check rate limit
    can_scan, limit_reason = rate_limiter.can_scan()
    if not can_scan:
        reporter.warning(f"⚠️  {limit_reason}")
        reporter.info("To disable rate limiting, edit .qodacode/config.json")
        sys.exit(1)

    # Record scan operation
    rate_limiter.record_scan()
    scan_start_time = time.time()

    # Check and install engines if needed (first-run experience)
    if deep or secrets or scan_all:
        from qodacode.engine_installer import check_and_install_if_needed
        check_and_install_if_needed()

    # --all activates everything
    if scan_all:
        deep = True
        secrets = True
        deps = True
    # Map severity filter
    severity_filter = None
    if severity != "all":
        severity_map = {
            "critical": [Severity.CRITICAL],
            "high": [Severity.CRITICAL, Severity.HIGH],
            "medium": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM],
            "low": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW],
        }
        severity_filter = severity_map.get(severity)

    # Map category filter
    category_filter = None
    if category != "all":
        category_map = {
            "security": [Category.SECURITY],
            "robustness": [Category.ROBUSTNESS],
            "maintainability": [Category.MAINTAINABILITY],
            "operability": [Category.OPERABILITY],
            "dependencies": [Category.DEPENDENCIES],
        }
        category_filter = category_map.get(category)

    # Run core scan (always runs - fast, local)
    result = scanner.scan(
        path=path,
        categories=category_filter,
        severities=severity_filter,
    )

    # Deep SAST analysis
    if deep:
        from qodacode.engines import SemgrepRunner

        semgrep = SemgrepRunner()

        if not semgrep.is_available():
            if skip_missing:
                # CI mode: log to stderr and continue
                import sys as _sys
                print("SKIPPED: Deep SAST engine not available (--skip-missing)", file=_sys.stderr)
            else:
                # Interactive mode: offer to help install
                console.print()
                console.print("[yellow]⚠ Deep SAST engine not available.[/yellow]")
                console.print(f"  Install with: [cyan]{semgrep.get_install_instructions()}[/cyan]")
                console.print()
                if sys.stdin.isatty():
                    # Only prompt if interactive terminal
                    from rich.prompt import Confirm
                    if Confirm.ask("Continue without deep analysis?", default=True):
                        reporter.info("Continuing with quick scan...")
                    else:
                        reporter.info("Aborting. Install dependencies and try again.")
                        sys.exit(0)
                else:
                    reporter.info("Continuing with quick scan...")
        else:
            reporter.info("Running deep SAST analysis...")
            try:
                semgrep_issues = semgrep.run(path)

                # Merge issues
                result.issues.extend(semgrep_issues)

                # Update files_with_issues count
                files_with_semgrep = set(issue.location.filepath for issue in semgrep_issues)
                files_with_treesitter = set(issue.location.filepath for issue in result.issues if issue not in semgrep_issues)
                result.files_with_issues = len(files_with_semgrep | files_with_treesitter)

                reporter.success(f"Deep analysis: {len(semgrep_issues)} additional issues found")
            except Exception as e:
                reporter.warning(f"Deep analysis failed: {e}")
                reporter.info("Continuing with quick scan...")

    # Secrets mode: Secret detection
    if secrets:
        from qodacode.engines import GitleaksRunner

        gitleaks = GitleaksRunner()

        if not gitleaks.is_available():
            if skip_missing:
                # CI mode: log to stderr and continue
                import sys as _sys
                print("SKIPPED: Secret detection engine not available (--skip-missing)", file=_sys.stderr)
            else:
                # Interactive mode: offer to help install
                console.print()
                console.print("[yellow]⚠ Secret detection engine not available.[/yellow]")
                console.print(f"  Install with: [cyan]{gitleaks.get_install_instructions()}[/cyan]")
                console.print()
                if sys.stdin.isatty():
                    from rich.prompt import Confirm
                    if Confirm.ask("Continue without secret scanning?", default=True):
                        reporter.info("Continuing without secret scanning...")
                    else:
                        reporter.info("Aborting. Install dependencies and try again.")
                        sys.exit(0)
                else:
                    reporter.info("Continuing without secret scanning...")
        else:
            reporter.info("Scanning for secrets and credentials...")
            try:
                gitleaks_issues = gitleaks.run(path)

                # Merge issues
                result.issues.extend(gitleaks_issues)

                # Update files_with_issues count
                all_files = set(issue.location.filepath for issue in result.issues)
                result.files_with_issues = len(all_files)

                reporter.success(f"Secret scan: {len(gitleaks_issues)} credential(s) found")
            except Exception as e:
                reporter.warning(f"Secret scan failed: {e}")
                reporter.info("Continuing without secret scanning...")

    # Deps mode: Dependency vulnerability scanning
    if deps:
        from qodacode.engines import OSVRunner

        osv = OSVRunner()
        reporter.info("Scanning dependencies for vulnerabilities...")

        try:
            osv_issues = osv.run(path)

            # Merge issues
            result.issues.extend(osv_issues)

            # Update files_with_issues count
            all_files = set(issue.location.filepath for issue in result.issues)
            result.files_with_issues = len(all_files)

            if osv_issues:
                reporter.success(f"Dependency scan: {len(osv_issues)} vulnerable package(s) found")
            else:
                reporter.success("Dependency scan: No vulnerabilities found")
        except Exception as e:
            reporter.warning(f"Dependency scan failed (offline?): {e}")
            reporter.info("Continuing without dependency scanning...")

    # Deduplicate and filter suppressed issues
    from qodacode.context import Deduplicator

    dedup = Deduplicator(project_root=path)
    original_count = len(result.issues)

    # Deduplicate: same file+line+category = 1 alert
    # Priority: Secrets > SAST > Deps > Core
    result.issues = dedup.deduplicate(result.issues)
    duplicates_removed = original_count - len(result.issues)
    if duplicates_removed > 0:
        reporter.info(f"[Dedup] Removed {duplicates_removed} duplicate(s)")

    # Filter suppressed issues (fingerprint + inline comments)
    result.issues, fp_suppressed, inline_ignored = dedup.filter_suppressed(result.issues)
    if fp_suppressed > 0:
        reporter.info(f"[Suppress] Filtered {fp_suppressed} suppressed issue(s)")
    if inline_ignored > 0:
        reporter.info(f"[Ignore] Filtered {inline_ignored} inline-ignored issue(s)")

    # Semantic context filtering (reduce false positives)
    from qodacode.context import filter_semantic_false_positives
    result.issues, semantic_filtered, _ = filter_semantic_false_positives(result.issues)
    if semantic_filtered > 0:
        reporter.info(f"[Semantic] Filtered {semantic_filtered} likely false positive(s)")

    # Filter baseline issues (only show NEW issues)
    if baseline:
        if dedup.has_baseline():
            result.issues, baseline_filtered = dedup.filter_baseline(result.issues)
            if baseline_filtered > 0:
                reporter.info(f"[Baseline] Filtered {baseline_filtered} known issue(s)")
        else:
            reporter.warning("No baseline found. Run 'qodacode baseline save' first.")

    # Add fingerprints to issues for suppress command
    for issue in result.issues:
        issue.context["fingerprint"] = dedup.get_fingerprint(issue)

    # Output results
    # Output based on format
    if output_format == "json":
        from qodacode.github import calculate_health_score
        health = calculate_health_score(result)
        output = {
            "version": "1.0",
            "files_scanned": result.files_scanned,
            "files_with_issues": result.files_with_issues,
            "summary": {
                "total": len(result.issues),
                "critical": result.critical_count,
                "high": result.high_count,
                "medium": result.medium_count,
                "low": result.low_count,
            },
            "health": health,
            "issues": [issue.model_dump(mode="json") for issue in result.issues],
        }
        click.echo(json.dumps(output, indent=2))
    elif output_format == "sarif":
        from qodacode.github import generate_sarif
        sarif = generate_sarif(result)
        click.echo(json.dumps(sarif, indent=2))
    elif output_format == "markdown":
        from qodacode.github import generate_pr_comment
        markdown = generate_pr_comment(result, show_suggestions=fix, mode=mode)
        click.echo(markdown)
    else:
        reporter.report_scan_result(result, show_fixes=fix, mode=mode)

    # Export to file if requested
    if export:
        from datetime import datetime
        from qodacode.utils.verdict import calculate_scan_summary, sort_issues_by_severity

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"qodacode-report-{timestamp}.txt"

        # Calculate scan summary (production + tests)
        summary = calculate_scan_summary(result.issues)

        # Build report content
        lines = []
        lines.append("=" * 50)
        lines.append("QODACODE SCAN REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Path: {os.path.abspath(path)}")
        lines.append("=" * 50)
        lines.append("")
        lines.append("PRODUCTION FILES")
        lines.append("-" * 30)
        lines.append(f"Critical: {summary.production.critical}")
        lines.append(f"High:     {summary.production.high}")
        lines.append(f"Medium:   {summary.production.medium}")
        lines.append(f"Low:      {summary.production.low}")
        lines.append("")
        if summary.tests.total > 0:
            lines.append("TEST FILES (excluded from verdict)")
            lines.append("-" * 30)
            lines.append(f"Critical: {summary.tests.critical}")
            lines.append(f"High:     {summary.tests.high}")
            lines.append(f"Medium:   {summary.tests.medium}")
            lines.append(f"Low:      {summary.tests.low}")
            lines.append("")
        lines.append(f"VERDICT: {summary.message}")
        lines.append("")
        lines.append("=" * 50)
        lines.append("ISSUES")
        lines.append("=" * 50)

        # Sort issues by severity
        sorted_issues = sort_issues_by_severity(result.issues)

        for issue in sorted_issues:
            sev = issue.severity.value.upper()
            lines.append("")
            lines.append(f"[{sev}] {issue.rule_id}: {issue.rule_name}")
            lines.append(f"  File: {issue.location.filepath}:{issue.location.line}")
            lines.append(f"  {issue.message}")
            if issue.fix_suggestion:
                lines.append(f"  Fix: {issue.fix_suggestion}")

        # Write file
        with open(filename, "w") as f:
            f.write("\n".join(lines))

        console.print(f"\n[green]📁 Exported to:[/green] {filename}")

    # Audit log: Record scan completion
    scan_duration_ms = (time.time() - scan_start_time) * 1000
    scan_type = "full" if scan_all else ("deep" if deep else ("secrets" if secrets else ("deps" if deps else "quick")))
    audit_logger.log_scan(
        path=path,
        scan_type=scan_type,
        findings_count=len(result.issues),
        critical_count=result.critical_count,
        duration_ms=scan_duration_ms,
    )

    # Exit with error code if critical issues found
    if result.critical_count > 0:
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# SIMPLIFIED SCAN COMMAND (qodacode scan)
# ─────────────────────────────────────────────────────────────────────────────
@main.command()
@click.option("--full", is_flag=True, help="Run full security suite (all engines)")
@click.option("--diff", "diff_only", is_flag=True, help="Only scan changed files (git-aware, faster)")
@click.option("--save", is_flag=True, help="Save results to file")
@click.option("--format", "save_format", type=click.Choice(["txt", "md"]), default="txt", help="Export format: txt (plain text) or md (markdown)")
@click.argument("path", default=".", required=False)
def scan(path: str, full: bool, diff_only: bool, save: bool, save_format: str):
    """Quick scan - the simplest way to scan your code.

    Examples:
        qodacode scan              # Scan current directory
        qodacode scan ./src        # Scan specific path
        qodacode scan --diff       # Only scan changed files (fast!)
        qodacode scan --full       # Run all engines
        qodacode scan --save       # Save report (.txt)
        qodacode scan --save --format md  # Save as markdown

    For more options, use 'qodacode check --help'
    """
    from qodacode.utils.verdict import calculate_scan_summary, sort_issues_by_severity
    import time

    # Run scan
    start_time = time.perf_counter()

    if diff_only:
        # Diff-aware scan - only changed files
        console.print(f"[bold {QODACODE_ORANGE}]⚡ Diff scan (changed files only)...[/bold {QODACODE_ORANGE}]")
        result = scanner.scan_diff(path=path)
        if result.files_scanned == 0:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            console.print(f"\n[dim]No changed files to scan ({elapsed_ms:.0f}ms)[/dim]")
            console.print(f"[green bold]✅ Clean - nothing to check[/green bold]")
            raise SystemExit(0)
    elif full:
        # Run with all engines
        console.print(f"[bold {QODACODE_ORANGE}]🔍 Full scan...[/bold {QODACODE_ORANGE}]")
        result = scanner.scan(path=path)
    else:
        console.print(f"[bold {QODACODE_ORANGE}]🔍 Quick scan...[/bold {QODACODE_ORANGE}]")
        result = scanner.scan(path=path)

    # Run additional engines if --full
    if full:
        # Secret detection
        try:
            from qodacode.engines import GitleaksRunner
            engine = GitleaksRunner()
            if engine.is_available():
                issues = engine.run(path)
                result.issues.extend(issues)
        except Exception:
            pass

        # Deep SAST
        try:
            from qodacode.engines import SemgrepRunner
            engine = SemgrepRunner()
            if engine.is_available():
                issues = engine.run(path)
                result.issues.extend(issues)
        except Exception:
            pass

    # Save cache to disk for future runs
    scanner.save_cache()

    # Calculate scan summary (production + tests separated)
    summary = calculate_scan_summary(result.issues)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # Simple output
    console.print()
    if diff_only:
        console.print(f"[dim]Changed files scanned:[/dim] {result.files_scanned} [dim]({elapsed_ms:.0f}ms)[/dim]")
    else:
        console.print(f"[dim]Files scanned:[/dim] {result.files_scanned}")
    console.print()

    # Production counts
    console.print("[bold]Production:[/bold]")
    if summary.production.critical:
        console.print(f"  🔴 [red bold]Critical:[/red bold] {summary.production.critical}")
    if summary.production.high:
        console.print(f"  🟠 [{QODACODE_ORANGE}]High:[/{QODACODE_ORANGE}] {summary.production.high}")
    if summary.production.medium:
        console.print(f"  🟡 [yellow]Medium:[/yellow] {summary.production.medium}")
    if summary.production.low:
        console.print(f"  🔵 [blue]Low:[/blue] {summary.production.low}")
    if summary.production.total == 0:
        console.print(f"  [dim]No issues[/dim]")

    # Test counts (if any)
    if summary.tests.total > 0:
        console.print()
        console.print("[bold dim]Tests (excluded from verdict):[/bold dim]")
        if summary.tests.critical:
            console.print(f"  🔴 [dim]Critical: {summary.tests.critical}[/dim]")
        if summary.tests.high:
            console.print(f"  🟠 [dim]High: {summary.tests.high}[/dim]")
        if summary.tests.medium:
            console.print(f"  🟡 [dim]Medium: {summary.tests.medium}[/dim]")
        if summary.tests.low:
            console.print(f"  🔵 [dim]Low: {summary.tests.low}[/dim]")

    console.print()

    # Verdict
    if summary.ready:
        console.print(f"[green bold]{summary.message}[/green bold]")
    else:
        console.print(f"[red bold]{summary.message}[/red bold]")

    # Save if requested
    if save:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        if save_format == "md":
            # Markdown format
            filename = f"qodacode-report-{timestamp}.md"
            lines = []
            lines.append("# Qodacode Scan Report")
            lines.append("")
            lines.append(f"**Path:** `{os.path.abspath(path)}`")
            lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
            lines.append("## Verdict")
            lines.append("")
            if summary.ready:
                lines.append(f"> {summary.message}")
            else:
                lines.append(f"> ⛔ **{summary.message}**")
            lines.append("")
            lines.append("## Production Files")
            lines.append("")
            lines.append("| Severity | Count |")
            lines.append("|----------|-------|")
            lines.append(f"| 🔴 Critical | {summary.production.critical} |")
            lines.append(f"| 🟠 High | {summary.production.high} |")
            lines.append(f"| 🟡 Medium | {summary.production.medium} |")
            lines.append(f"| 🔵 Low | {summary.production.low} |")

            if summary.tests.total > 0:
                lines.append("")
                lines.append("## Test Files (excluded from verdict)")
                lines.append("")
                lines.append("| Severity | Count |")
                lines.append("|----------|-------|")
                lines.append(f"| 🔴 Critical | {summary.tests.critical} |")
                lines.append(f"| 🟠 High | {summary.tests.high} |")
                lines.append(f"| 🟡 Medium | {summary.tests.medium} |")
                lines.append(f"| 🔵 Low | {summary.tests.low} |")

            if result.issues:
                lines.append("")
                lines.append("## Issues")
                lines.append("")
                for issue in sort_issues_by_severity(result.issues):
                    sev = issue.severity.value.upper()
                    icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(sev, "⚪")
                    lines.append(f"### {icon} [{sev}] {issue.rule_name}")
                    lines.append("")
                    lines.append(f"- **File:** `{issue.location.filepath}:{issue.location.line}`")
                    lines.append(f"- **Message:** {issue.message}")
                    if issue.fix_suggestion:
                        lines.append(f"- **Fix:** {issue.fix_suggestion}")
                    lines.append("")
        else:
            # Plain text format (default)
            filename = f"qodacode-report-{timestamp}.txt"
            lines = []
            lines.append("QODACODE SCAN REPORT")
            lines.append(f"Path: {os.path.abspath(path)}")
            lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
            lines.append(f"VERDICT: {summary.message}")
            lines.append("")
            lines.append("PRODUCTION:")
            lines.append(f"  Critical: {summary.production.critical}")
            lines.append(f"  High: {summary.production.high}")
            lines.append(f"  Medium: {summary.production.medium}")
            lines.append(f"  Low: {summary.production.low}")
            if summary.tests.total > 0:
                lines.append("")
                lines.append("TESTS (excluded from verdict):")
                lines.append(f"  Critical: {summary.tests.critical}")
                lines.append(f"  High: {summary.tests.high}")
                lines.append(f"  Medium: {summary.tests.medium}")
                lines.append(f"  Low: {summary.tests.low}")

            if result.issues:
                lines.append("")
                lines.append("ISSUES:")
                for issue in sort_issues_by_severity(result.issues):
                    sev = issue.severity.value.upper()
                    lines.append(f"  [{sev}] {issue.location.filepath}:{issue.location.line} - {issue.message}")

        with open(filename, "w") as f:
            f.write("\n".join(lines))

        console.print(f"\n[green]📁 Saved:[/green] {filename}")

    # Exit code (fail if production has critical issues)
    if summary.production.critical > 0:
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────


@main.command()
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Path to check (default: current directory)"
)
def status(path: str):
    """Show project status.

    Displays summary of indexed files and current issues.
    """
    qodacode_dir = Path(path) / ".qodacode"

    if not qodacode_dir.exists():
        reporter.warning("Qodacode not initialized. Run 'qodacode init' first.")
        return

    # Load index
    try:
        with open(qodacode_dir / "index.json") as f:
            index_data = json.load(f)
    except FileNotFoundError:
        reporter.error("Index file not found. Run 'qodacode init' to re-index.")
        return

    # Run quick scan for current status
    result = scanner.scan(path)

    reporter.report_status(
        path=path,
        files_scanned=result.files_scanned,
        result=result,
        index_data=index_data,
    )


@main.command()
@click.argument("fingerprint")
@click.option(
    "--reason", "-r",
    default="",
    help="Reason for suppressing (e.g., 'false positive', 'accepted risk')"
)
@click.option(
    "--expires", "-e",
    type=int,
    default=None,
    help="Auto-expire after N days (default: permanent)"
)
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Project root (default: current directory)"
)
def suppress(fingerprint: str, reason: str, expires: int, path: str):
    """Suppress an issue by fingerprint.

    The fingerprint is shown in scan output (e.g., 'abc123def456').
    Suppressed issues won't appear in future scans.

    Example:
        qodacode suppress abc123def456 --reason "false positive"
        qodacode suppress abc123def456 --expires 30  # Expires in 30 days
    """
    from qodacode.context import Deduplicator

    dedup = Deduplicator(project_root=path)

    if dedup.suppress(fingerprint, reason=reason, expires_in_days=expires):
        reporter.success(f"Issue {fingerprint} suppressed")
        if reason:
            reporter.info(f"Reason: {reason}")
        if expires:
            reporter.info(f"Expires in {expires} days")
    else:
        reporter.warning(f"Issue {fingerprint} was already suppressed")


@main.command()
@click.argument("fingerprint")
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Project root (default: current directory)"
)
def unsuppress(fingerprint: str, path: str):
    """Remove a suppression.

    Example:
        qodacode unsuppress abc123def456
    """
    from qodacode.context import Deduplicator

    dedup = Deduplicator(project_root=path)

    if dedup.unsuppress(fingerprint):
        reporter.success(f"Suppression removed for {fingerprint}")
    else:
        reporter.warning(f"Issue {fingerprint} was not suppressed")


@main.command()
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Project root (default: current directory)"
)
def suppressions(path: str):
    """List all active suppressions.

    Example:
        qodacode suppressions
    """
    from qodacode.context import Deduplicator

    dedup = Deduplicator(project_root=path)
    supps = dedup.list_suppressions()

    if not supps:
        reporter.info("No active suppressions")
        return

    reporter.info(f"Active suppressions: {len(supps)}")
    for s in supps:
        expires = f" (expires: {s.expires_at})" if s.expires_at else ""
        reason = f" - {s.reason}" if s.reason else ""
        click.echo(f"  {s.fingerprint}{reason}{expires}")


# ─────────────────────────────────────────────────────────────────────────────
# BASELINE MODE (for legacy projects)
# ─────────────────────────────────────────────────────────────────────────────


@main.group()
def baseline():
    """Manage issue baseline for legacy projects.

    Save current issues as baseline, then use --baseline flag to only
    see NEW issues in future scans.

    Example workflow:
        qodacode baseline save       # Save current issues
        qodacode check --baseline    # Only show NEW issues
        qodacode baseline show       # View baseline info
        qodacode baseline clear      # Remove baseline
    """
    pass


@baseline.command("save")
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Project root (default: current directory)"
)
def baseline_save(path: str):
    """Save current issues as baseline.

    Future scans with --baseline will only show NEW issues.
    Useful for legacy projects with many existing issues.

    Example:
        qodacode baseline save
    """
    from qodacode.context import Deduplicator
    from qodacode.scanner import Scanner

    reporter.info("Scanning project to create baseline...")

    # Run a full scan
    scanner = Scanner()
    result = scanner.scan(path)

    # Deduplicate before saving
    dedup = Deduplicator(project_root=path)
    issues = dedup.deduplicate(result.issues)

    # Save baseline
    count = dedup.save_baseline(issues)

    reporter.success(f"Baseline saved with {count} issues")
    reporter.info("Use 'qodacode check --baseline' to only see NEW issues")


@baseline.command("show")
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Project root (default: current directory)"
)
def baseline_show(path: str):
    """Show baseline information.

    Example:
        qodacode baseline show
    """
    from qodacode.context import Deduplicator

    dedup = Deduplicator(project_root=path)
    info = dedup.get_baseline_info()

    if not info:
        reporter.warning("No baseline found. Run 'qodacode baseline save' first.")
        return

    reporter.info("Baseline information:")
    console.print(f"  Issues: [bold]{info['issue_count']}[/bold]")
    console.print(f"  Created: [dim]{info['created_at']}[/dim]")


@baseline.command("clear")
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Project root (default: current directory)"
)
def baseline_clear(path: str):
    """Remove the baseline.

    Example:
        qodacode baseline clear
    """
    from qodacode.context import Deduplicator

    dedup = Deduplicator(project_root=path)

    if dedup.clear_baseline():
        reporter.success("Baseline cleared")
    else:
        reporter.warning("No baseline to clear")


@main.command()
def doctor():
    """Check Qodacode system health and engine availability.

    Verifies all analysis engines are properly configured.

    Example:
        qodacode doctor
    """
    import shutil
    import subprocess

    console.print()
    console.print(f"[bold {QODACODE_ORANGE}]QODACODE Doctor[/bold {QODACODE_ORANGE}] - System health check")
    console.print()

    # Create table
    table = Table(title="Engine Status", show_header=True, header_style="bold cyan")
    table.add_column("Engine", style="bold")
    table.add_column("Status")
    table.add_column("Info")

    # Core Engine (always available - it's a Python package)
    try:
        import tree_sitter
        table.add_row(
            "Core Engine",
            "[green]✓ Ready[/green]",
            "[dim]Instant analysis (<50ms)[/dim]"
        )
    except ImportError:
        table.add_row(
            "Core Engine",
            "[red]✗ Error[/red]",
            "[yellow]Reinstall qodacode[/yellow]"
        )

    # Deep SAST Engine
    semgrep_path = shutil.which("semgrep")
    if semgrep_path:
        table.add_row(
            "Deep SAST",
            "[green]✓ Ready[/green]",
            "[dim]Advanced static analysis[/dim]"
        )
    else:
        table.add_row(
            "Deep SAST",
            "[yellow]○ Optional[/yellow]",
            "[dim]pip install qodacode[deep][/dim]"
        )

    # Secret Detection Engine
    gitleaks_path = shutil.which("gitleaks")
    if gitleaks_path:
        table.add_row(
            "Secret Detection",
            "[green]✓ Ready[/green]",
            "[dim]Credential scanning[/dim]"
        )
    else:
        table.add_row(
            "Secret Detection",
            "[yellow]○ Auto-install[/yellow]",
            "[dim]Downloads on first use[/dim]"
        )

    # Dependency Scanner (API-based, check internet)
    try:
        import urllib.request
        urllib.request.urlopen("https://api.osv.dev", timeout=3)
        table.add_row(
            "Dependency Scanner",
            "[green]✓ Ready[/green]",
            "[dim]Vulnerability database[/dim]"
        )
    except Exception:
        table.add_row(
            "Dependency Scanner",
            "[yellow]⚠ Offline[/yellow]",
            "[dim]Requires internet[/dim]"
        )

    console.print(table)
    console.print()

    # Summary
    all_installed = semgrep_path and gitleaks_path
    if all_installed:
        console.print(f"[green]✓ All engines ready![/green] Use [bold]qodacode check --all[/bold] for full analysis.")
    else:
        console.print("[dim]Optional engines add deeper analysis.[/dim]")
        console.print("[dim]Core scanning works without them.[/dim]")
    console.print()


@main.command()
@click.option(
    "--ai-provider", "-p",
    type=click.Choice(["anthropic", "openai", "ollama", "none"]),
    help="AI provider for explanations"
)
@click.option(
    "--ai-key", "-k",
    help="API key for AI provider (not needed for Ollama)"
)
@click.option(
    "--ai-model", "-m",
    help="Model to use (e.g., claude-3-haiku-20240307, gpt-4o-mini, llama3.2)"
)
@click.option(
    "--show", "-s",
    is_flag=True,
    help="Show current configuration"
)
def config(ai_provider: Optional[str], ai_key: Optional[str], ai_model: Optional[str], show: bool):
    """Configure Qodacode settings.

    Set up AI provider for contextual explanations in junior mode.

    Examples:
        qodacode config --show
        qodacode config --ai-provider anthropic --ai-key sk-ant-xxx
        qodacode config --ai-provider openai --ai-key sk-xxx
        qodacode config --ai-provider ollama --ai-model llama3.2
        qodacode config --ai-provider none

    Environment variables (alternative):
        ANTHROPIC_API_KEY=sk-ant-xxx
        OPENAI_API_KEY=sk-xxx
        OLLAMA_HOST=http://localhost:11434
    """
    from qodacode.ai_explainer import load_config, save_config, get_provider_info

    if show or (not ai_provider and not ai_key and not ai_model):
        # Show current config
        info = get_provider_info()
        reporter.info("Current AI Configuration:")
        if info["available"]:
            console.print(f"  Provider: [green]{info['provider']}[/green]")
            console.print(f"  Model: [cyan]{info['model']}[/cyan]")
            console.print(f"  Status: [green]✓ AI explanations enabled[/green]")
        else:
            console.print(f"  Provider: [dim]none[/dim]")
            console.print(f"  Status: [yellow]Static explanations only[/yellow]")
            console.print()
            console.print("[dim]To enable AI explanations:[/dim]")
            console.print("  qodacode config --ai-provider anthropic --ai-key YOUR_KEY")
            console.print("  qodacode config --ai-provider ollama  [dim](free, local)[/dim]")
        return

    if ai_provider:
        config_path = save_config(
            provider=ai_provider,
            api_key=ai_key,
            model=ai_model,
        )
        reporter.success(f"Configuration saved to {config_path}")

        if ai_provider == "none":
            reporter.info("AI explanations disabled. Using static explanations.")
        elif ai_provider == "ollama":
            reporter.info(f"Using Ollama (local). Model: {ai_model or 'llama3.2'}")
            reporter.info("Make sure Ollama is running: ollama serve")
        else:
            reporter.info(f"Using {ai_provider}. Model: {ai_model or 'default'}")


@main.command()
def rules():
    """List all available rules."""
    all_rules = RuleRegistry.get_all()

    reporter.info(f"Available rules ({len(all_rules)}):\n")

    # Group by category
    by_category = {}
    for rule in all_rules:
        cat = rule.category.value
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(rule)

    for category, rules_list in sorted(by_category.items()):
        reporter.section(category.upper())
        for rule in sorted(rules_list, key=lambda r: r.id):
            severity_color = {
                Severity.CRITICAL: "red",
                Severity.HIGH: "yellow",
                Severity.MEDIUM: "blue",
                Severity.LOW: "dim",
            }.get(rule.severity, "white")

            reporter.rule_info(
                rule_id=rule.id,
                name=rule.name,
                severity=rule.severity.value,
                description=rule.description,
                severity_color=severity_color,
            )
        reporter.newline()


@main.command("git-history")
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Path to git repository (default: current directory)"
)
@click.option(
    "--max-commits", "-n",
    default=50,
    help="Maximum number of commits to scan"
)
@click.option(
    "--since", "-s",
    default=None,
    help="Only scan commits since this date (YYYY-MM-DD)"
)
@click.option(
    "--format", "-f",
    "output_format",
    type=click.Choice(["terminal", "json"]),
    default="terminal",
    help="Output format"
)
def git_history(path: str, max_commits: int, since: Optional[str], output_format: str):
    """Scan git history for secrets.

    Detects secrets that may have been committed and later removed,
    but still exist in git history.

    Examples:
        qodacode git-history
        qodacode git-history --max-commits 100
        qodacode git-history --since 2024-01-01
    """
    from qodacode.git_scanner import scan_git_history, is_git_repo, format_git_findings

    if not is_git_repo(path):
        reporter.error("Not a git repository. Run from inside a git repo.")
        sys.exit(1)

    reporter.info(f"Scanning git history (last {max_commits} commits)...")

    findings = scan_git_history(path, max_commits=max_commits, since=since)

    if output_format == "json":
        output = {
            "findings": [
                {
                    "commit_hash": f.commit_hash,
                    "commit_author": f.commit_author,
                    "commit_date": f.commit_date,
                    "commit_message": f.commit_message,
                    "file_path": f.file_path,
                    "secret_type": f.secret_type,
                    "match": f.match,
                }
                for f in findings
            ],
            "total": len(findings),
        }
        click.echo(json.dumps(output, indent=2))
    else:
        if not findings:
            reporter.success("No secrets found in git history!")
        else:
            console.print(f"\n[red bold]⚠ Found {len(findings)} secret(s) in git history![/red bold]\n")

            table = Table(show_header=True, header_style="bold")
            table.add_column("Commit", style="cyan")
            table.add_column("Date")
            table.add_column("File")
            table.add_column("Type", style="yellow")
            table.add_column("Match", style="red")

            for finding in findings:
                table.add_row(
                    finding.commit_hash,
                    finding.commit_date,
                    finding.file_path[:30],
                    finding.secret_type,
                    finding.match[:20] + "..." if len(finding.match) > 20 else finding.match,
                )

            console.print(table)
            console.print()
            console.print("[yellow]WARNING:[/yellow] Secrets in git history remain accessible even after removal.")
            console.print("[dim]Consider: git filter-branch or BFG Repo-Cleaner to purge history.[/dim]")

            sys.exit(1)


@main.command("serve")
def serve():
    """Start the MCP server for AI integration.

    Exposes Qodacode as an MCP (Model Context Protocol) server that
    can be used by Claude, Cursor, and other MCP-compatible AI tools.

    The server provides tools for:
    - Code scanning and analysis
    - Secret detection
    - Dependency vulnerability checking
    - Rule explanations

    Configure in Claude Code:
        Add to ~/.claude/claude_desktop_config.json:
        {
          "mcpServers": {
            "qodacode": {
              "command": "qodacode",
              "args": ["serve"]
            }
          }
        }
    """
    reporter.info("Starting Qodacode MCP server...")
    reporter.info("Server is ready. Waiting for MCP connections.\n")

    try:
        from qodacode.mcp_server import main as mcp_main
        mcp_main()
    except ImportError as e:
        reporter.error(f"MCP dependencies not installed: {e}")
        reporter.info("Install with: pip install mcp")
        sys.exit(1)


@main.command()
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Path to watch (default: current directory)"
)
@click.option(
    "--severity", "-s",
    type=click.Choice(["critical", "high", "medium", "low", "all"]),
    default="high",
    help="Minimum severity to report (default: high)"
)
@click.option(
    "--mode", "-m",
    type=click.Choice(["junior", "senior"]),
    default="senior",
    help="Output mode"
)
@click.option(
    "--debounce",
    default=200,
    type=int,
    help="Debounce time in milliseconds (default: 200)"
)
def watch(path: str, severity: str, mode: str, debounce: int):
    """Watch files for changes and scan in real-time.

    Monitors the directory for file changes and automatically
    scans modified files for issues. Optimized for AI-assisted
    development workflows.

    Press Ctrl+C to stop watching.

    Examples:
        qodacode watch
        qodacode watch --path ./src
        qodacode watch --severity critical
        qodacode watch --debounce 100
    """
    from datetime import datetime
    from threading import Timer, Lock

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        reporter.error("watchdog package required. Install with: pip install watchdog")
        sys.exit(1)

    # Map severity filter
    severity_filter = None
    if severity != "all":
        severity_map = {
            "critical": [Severity.CRITICAL],
            "high": [Severity.CRITICAL, Severity.HIGH],
            "medium": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM],
            "low": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW],
        }
        severity_filter = severity_map.get(severity)

    # Extensions to watch
    WATCH_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".json", ".yaml", ".yml", ".env"}
    IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".qodacode", ".next", "target"}

    class WatchStats:
        """Track running statistics for watch mode."""
        def __init__(self):
            self.files_scanned = 0
            self.total_critical = 0
            self.total_high = 0
            self.total_medium = 0
            self.total_low = 0
            self.issues_fixed = 0
            self.file_issues: dict[str, int] = {}  # Track issues per file

        def update(self, filepath: str, issues: list):
            """Update stats after scanning a file."""
            self.files_scanned += 1

            # Count by severity
            critical = sum(1 for i in issues if i.severity == Severity.CRITICAL)
            high = sum(1 for i in issues if i.severity == Severity.HIGH)
            medium = sum(1 for i in issues if i.severity == Severity.MEDIUM)
            low = sum(1 for i in issues if i.severity == Severity.LOW)

            # Check if issues were fixed (file had issues before, now has fewer or none)
            prev_count = self.file_issues.get(filepath, 0)
            curr_count = len(issues)
            if prev_count > 0 and curr_count < prev_count:
                self.issues_fixed += (prev_count - curr_count)

            self.file_issues[filepath] = curr_count
            self.total_critical = sum(1 for f, c in self.file_issues.items()
                                      for _ in range(c) if c > 0)  # Simplified

        def get_summary(self) -> str:
            """Get summary string for display."""
            active_issues = sum(self.file_issues.values())
            parts = []
            if self.total_critical > 0:
                parts.append(f"[red]🔴 {self.total_critical} critical[/red]")
            if self.total_high > 0:
                parts.append(f"[{QODACODE_ORANGE}]🟠 {self.total_high} high[/{QODACODE_ORANGE}]")
            if self.total_medium > 0:
                parts.append(f"[yellow]🟡 {self.total_medium} medium[/yellow]")

            if not parts:
                return "[green]✅ No issues[/green]"
            return " | ".join(parts)

    class QodacodeHandler(FileSystemEventHandler):
        """Handler for file system events with debounced batch processing."""

        def __init__(self):
            self.scanner = Scanner(persistent_cache=True, project_path=path)
            self.pending_files: set = set()
            self.timer: Optional[Timer] = None
            self.lock = Lock()
            self.stats = WatchStats()
            self.debounce_sec = debounce / 1000.0  # Convert ms to seconds

        def should_scan(self, filepath: str) -> bool:
            """Check if file should be scanned."""
            p = Path(filepath)

            # Skip directories in ignore list
            for part in p.parts:
                if part in IGNORE_DIRS:
                    return False

            # Only scan supported extensions
            if p.suffix.lower() not in WATCH_EXTENSIONS:
                return False

            # Skip if file doesn't exist (might have been deleted)
            if not p.exists():
                return False

            return True

        def on_modified(self, event):
            if event.is_directory:
                return
            if self.should_scan(event.src_path):
                self._queue_scan(event.src_path)

        def on_created(self, event):
            if event.is_directory:
                return
            if self.should_scan(event.src_path):
                self._queue_scan(event.src_path)

        def _queue_scan(self, filepath: str):
            """Queue a file for scanning with debounce."""
            with self.lock:
                self.pending_files.add(filepath)

                # Cancel existing timer
                if self.timer:
                    self.timer.cancel()

                # Start new debounce timer
                self.timer = Timer(self.debounce_sec, self._process_batch)
                self.timer.daemon = True
                self.timer.start()

        def _process_batch(self):
            """Process all pending file changes."""
            with self.lock:
                files = list(self.pending_files)
                self.pending_files.clear()

            if not files:
                return

            timestamp = datetime.now().strftime("%H:%M:%S")

            for filepath in files:
                try:
                    # Show scanning indicator
                    rel_path = os.path.relpath(filepath)
                    console.print(f"[dim][{timestamp}][/dim] ⏳ Scanning [cyan]{rel_path}[/cyan]...", end="")

                    # Measure scan time
                    start = time.time()
                    result = self.scanner.scan_file(
                        filepath,
                        severities=severity_filter,
                    )
                    elapsed_ms = int((time.time() - start) * 1000)

                    # Update stats
                    prev_issues = self.stats.file_issues.get(filepath, 0)
                    curr_issues = len(result.issues)

                    if result.issues:
                        # Issues found
                        self.stats.file_issues[filepath] = curr_issues
                        console.print(f" [red]found {curr_issues} issue(s)[/red] [{elapsed_ms}ms]")

                        # Show issues
                        for issue in result.issues:
                            sev_color = {
                                Severity.CRITICAL: "red",
                                Severity.HIGH: QODACODE_ORANGE,
                                Severity.MEDIUM: "yellow",
                                Severity.LOW: "dim",
                            }.get(issue.severity, "white")
                            console.print(f"    [{sev_color}]● {issue.severity.value.upper()}[/{sev_color}] {issue.rule_id}: {issue.message} (line {issue.line})")

                    elif prev_issues > 0:
                        # Issues were fixed!
                        self.stats.file_issues[filepath] = 0
                        self.stats.issues_fixed += prev_issues
                        console.print(f" [green]✅ {prev_issues} issue(s) fixed![/green] [{elapsed_ms}ms]")

                    else:
                        # No issues, clean file
                        console.print(f" [green]✓ clean[/green] [{elapsed_ms}ms]")

                    self.stats.files_scanned += 1

                except FileNotFoundError:
                    console.print(f" [dim]file removed[/dim]")
                except Exception as e:
                    console.print(f" [red]error: {str(e)[:50]}[/red]")

            # Show running summary
            active_issues = sum(self.stats.file_issues.values())
            if active_issues > 0:
                console.print(f"[dim]─── Active issues: {active_issues} | Fixed this session: {self.stats.issues_fixed} ───[/dim]")

    # Start watching
    abs_path = os.path.abspath(path)

    # Show header
    console.print()
    console.print("[bold cyan]┌─ QODACODE WATCH ─────────────────────────────────────────────┐[/bold cyan]")
    console.print(f"[bold cyan]│[/bold cyan] [dim]Path:[/dim] {abs_path[:50]}{'...' if len(abs_path) > 50 else ''}")
    console.print(f"[bold cyan]│[/bold cyan] [dim]Severity:[/dim] {severity} | [dim]Mode:[/dim] {mode} | [dim]Debounce:[/dim] {debounce}ms")
    console.print(f"[bold cyan]│[/bold cyan] [dim]Press Ctrl+C to stop[/dim]")
    console.print("[bold cyan]└──────────────────────────────────────────────────────────────┘[/bold cyan]")
    console.print()

    event_handler = QodacodeHandler()
    observer = Observer()
    observer.schedule(event_handler, abs_path, recursive=True)
    observer.start()

    try:
        while not is_shutdown_requested():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()

        # Show session summary
        stats = event_handler.stats
        console.print()
        console.print("[bold cyan]┌─ SESSION SUMMARY ────────────────────────────────────────────┐[/bold cyan]")
        console.print(f"[bold cyan]│[/bold cyan] Files scanned: {stats.files_scanned}")
        console.print(f"[bold cyan]│[/bold cyan] Issues fixed: [green]{stats.issues_fixed}[/green]")
        active = sum(stats.file_issues.values())
        if active > 0:
            console.print(f"[bold cyan]│[/bold cyan] Active issues: [yellow]{active}[/yellow]")
        else:
            console.print(f"[bold cyan]│[/bold cyan] Active issues: [green]0 ✓[/green]")
        console.print("[bold cyan]└──────────────────────────────────────────────────────────────┘[/bold cyan]")

    observer.join()


@main.command()
@click.option(
    "--path", "-p",
    default=".",
    type=click.Path(exists=True),
    help="Path to scan (default: current directory)"
)
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low", "none"]),
    default="critical",
    help="Fail if issues of this severity or higher are found"
)
@click.option(
    "--mode", "-m",
    type=click.Choice(["junior", "senior"]),
    default="senior",
    help="Output mode: junior (educational) or senior (concise)"
)
@click.option(
    "--categories",
    default="all",
    help="Categories to scan (comma-separated)"
)
@click.option(
    "--comment",
    is_flag=True,
    help="Generate PR comment file"
)
@click.option(
    "--output-file",
    help="File to write GitHub Actions outputs"
)
@click.option(
    "--json-output",
    is_flag=True,
    help="Output results as JSON"
)
@click.option(
    "--sarif",
    is_flag=True,
    help="Generate SARIF output for GitHub Security tab"
)
@click.option(
    "--sarif-file",
    default="qodacode-results.sarif",
    help="Path for SARIF output file"
)
def ci(
    path: str,
    fail_on: str,
    mode: str,
    categories: str,
    comment: bool,
    output_file: Optional[str],
    json_output: bool,
    sarif: bool,
    sarif_file: str,
):
    """Run Qodacode in CI/CD mode (GitHub Actions, GitLab CI, etc.).

    Designed for automated pipelines:
    - Outputs to GITHUB_OUTPUT for Actions
    - Generates PR comment markdown
    - Returns exit code based on fail-on threshold
    - Supports JSON and SARIF output

    Examples:
        qodacode ci --fail-on critical --comment
        qodacode ci --fail-on high --json-output
        qodacode ci --sarif  # For GitHub Security tab
        qodacode ci --mode junior --comment
    """
    from qodacode.github import (
        GitHubContext,
        generate_pr_comment,
        generate_status_check_output,
        write_github_output,
        get_exit_code,
        write_sarif,
    )

    # Parse categories
    category_filter = None
    if categories != "all":
        category_list = [c.strip().upper() for c in categories.split(",")]
        category_filter = [
            cat for cat in Category
            if cat.name in category_list
        ]

    # Run scan
    result = scanner.scan(
        path=path,
        categories=category_filter,
    )

    # Get GitHub context
    ctx = GitHubContext.from_env()

    if json_output:
        # JSON output for programmatic use
        output = generate_status_check_output(result, fail_on)
        output["issues"] = [
            {
                "rule_id": issue.rule_id,
                "rule_name": issue.rule_name,
                "severity": issue.severity.name,
                "filepath": issue.location.filepath,
                "line": issue.location.line,
                "message": issue.message,
                "fix_suggestion": issue.fix_suggestion,
            }
            for issue in result.issues
        ]
        click.echo(json.dumps(output, indent=2))
    else:
        # Human-readable output
        status = generate_status_check_output(result, fail_on)

        if result.issues:
            console.print(f"\n[bold red]QODACODE CI: {len(result.issues)} issue(s) found[/bold red]")
        else:
            console.print(f"\n[bold green]QODACODE CI: No issues found![/bold green]")

        console.print(f"[dim]Health Score: {status['health_score']}/100 (Grade {status['grade']})[/dim]")
        console.print(f"[dim]Files scanned: {result.files_scanned}[/dim]")

        if result.critical_count:
            console.print(f"[red]  Critical: {result.critical_count}[/red]")
        if result.high_count:
            console.print(f"[yellow]  High: {result.high_count}[/yellow]")
        if result.medium_count:
            console.print(f"[blue]  Medium: {result.medium_count}[/blue]")
        if result.low_count:
            console.print(f"[dim]  Low: {result.low_count}[/dim]")

    # Write GitHub outputs
    if ctx.is_ci or output_file:
        write_github_output(result, fail_on, output_file)
        if comment:
            console.print(f"\n[dim]PR comment written to .qodacode/pr-comment.md[/dim]")

    # Generate PR comment file if requested
    if comment:
        from pathlib import Path
        comment_dir = Path(".qodacode")
        comment_dir.mkdir(exist_ok=True)
        comment_content = generate_pr_comment(result, fail_on, mode=mode)
        (comment_dir / "pr-comment.md").write_text(comment_content)

    # Generate SARIF output for GitHub Security tab
    if sarif:
        sarif_path = write_sarif(result, sarif_file)
        console.print(f"\n[green]SARIF output written to {sarif_path}[/green]")
        console.print(f"[dim]Upload to GitHub: gh code-scanning upload --sarif-file={sarif_path}[/dim]")

    # Exit with appropriate code
    exit_code = get_exit_code(result, fail_on)
    if exit_code != 0:
        console.print(f"\n[red bold]Merge blocked: {fail_on} issues found[/red bold]")

    sys.exit(exit_code)


@main.command("setup-mcp")
def setup_mcp():
    """Configure MCP server for Claude Code/Desktop.

    Automatically adds Qodacode to Claude's MCP configuration.
    Supports both Claude Code CLI and Claude Desktop.

    After running this, close and reopen your editor to use Qodacode.

    Usage:
        "scan this project with Qodacode"
        "check for security issues"
    """
    console.print("\n[bold #DA7028]Qodacode MCP Setup[/bold #DA7028]\n")

    # MCP server configuration
    qodacode_mcp_config = {
        "command": "qodacode",
        "args": ["serve"]
    }

    configured_files = []

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Claude Code CLI config: ~/.claude.json
    # ─────────────────────────────────────────────────────────────────────────
    claude_code_config = Path.home() / ".claude.json"

    try:
        if claude_code_config.exists():
            with open(claude_code_config) as f:
                config = json.load(f)
        else:
            config = {}

        if "mcpServers" not in config:
            config["mcpServers"] = {}

        config["mcpServers"]["qodacode"] = qodacode_mcp_config

        with open(claude_code_config, "w") as f:
            json.dump(config, f, indent=2)

        configured_files.append(("Claude Code CLI", claude_code_config))
    except Exception as e:
        console.print(f"[yellow]⚠ Could not configure Claude Code CLI: {e}[/yellow]")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Claude Desktop config: ~/.claude/claude_desktop_config.json
    # ─────────────────────────────────────────────────────────────────────────
    claude_desktop_dir = Path.home() / ".claude"
    claude_desktop_config = claude_desktop_dir / "claude_desktop_config.json"

    try:
        claude_desktop_dir.mkdir(exist_ok=True)

        if claude_desktop_config.exists():
            with open(claude_desktop_config) as f:
                config = json.load(f)
        else:
            config = {}

        if "mcpServers" not in config:
            config["mcpServers"] = {}

        config["mcpServers"]["qodacode"] = qodacode_mcp_config

        with open(claude_desktop_config, "w") as f:
            json.dump(config, f, indent=2)

        configured_files.append(("Claude Desktop", claude_desktop_config))
    except Exception as e:
        console.print(f"[yellow]⚠ Could not configure Claude Desktop: {e}[/yellow]")

    # ─────────────────────────────────────────────────────────────────────────
    # Results
    # ─────────────────────────────────────────────────────────────────────────
    if configured_files:
        for name, path in configured_files:
            console.print(f"[green]✓[/green] {name}: {path}")

        console.print("\n[bold #DA7028]Next step:[/bold #DA7028]")
        console.print("  [bold]Close and reopen your editor[/bold] (VSCode/Cursor/Claude Code)")
        console.print("\n[dim]Then say: \"scan this project with Qodacode\"[/dim]")
    else:
        console.print("[red]✗ Could not configure any Claude installation[/red]")


# ─────────────────────────────────────────────────────────────────────────────
# TYPOSQUATTING DETECTION (Phase 4 - Technical Moat)
# ─────────────────────────────────────────────────────────────────────────────


@main.command()
@click.argument("target", default=".", required=False)
@click.option(
    "--ecosystem", "-e",
    type=click.Choice(["pypi", "npm", "auto"]),
    default="auto",
    help="Package ecosystem (default: auto-detect)"
)
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="Output in JSON format"
)
def typosquat(target: str, ecosystem: str, output_json: bool):
    """Detect typosquatting attacks in dependencies.

    Scans requirements.txt, package.json, Pipfile, or pyproject.toml
    for packages with names similar to popular packages - a common
    supply chain attack vector.

    Examples:
        qodacode typosquat                    # Scan current directory
        qodacode typosquat requirements.txt   # Scan specific file
        qodacode typosquat --ecosystem npm    # Force NPM ecosystem
        qodacode typosquat --json             # JSON output for CI
    """
    from qodacode.typosquatting import TyposquattingDetector
    from qodacode.typosquatting.detector import scan_directory, RiskLevel

    path = Path(target)

    # Determine what to scan
    if path.is_file():
        detector = TyposquattingDetector()
        matches = detector.detect_file(str(path))
        files_scanned = {str(path): matches} if matches else {}
    else:
        files_scanned = scan_directory(str(path))

    # Count issues by severity
    critical = 0
    high = 0
    medium = 0

    for file_matches in files_scanned.values():
        for match in file_matches:
            if match.risk_level == RiskLevel.CRITICAL:
                critical += 1
            elif match.risk_level == RiskLevel.HIGH:
                high += 1
            else:
                medium += 1

    total = critical + high + medium

    # JSON output for CI/CD
    if output_json:
        result = {
            "total_issues": total,
            "critical": critical,
            "high": high,
            "medium": medium,
            "files": {}
        }
        for filepath, matches in files_scanned.items():
            result["files"][filepath] = [m.to_dict() for m in matches]
        print(json.dumps(result, indent=2))
        sys.exit(1 if critical > 0 else 0)

    # Human-readable output
    console.print()
    console.print(f"[bold {QODACODE_ORANGE}]🔍 Typosquatting Scan[/bold {QODACODE_ORANGE}]")
    console.print()

    if total == 0:
        console.print("[green]✅ No typosquatting detected[/green]")
        console.print()
        return

    # Show results
    console.print(f"[bold red]⚠️  SUPPLY CHAIN RISK DETECTED[/bold red]")
    console.print()

    for filepath, matches in files_scanned.items():
        console.print(f"[dim]File:[/dim] {filepath}")
        console.print()

        for match in matches:
            if match.risk_level == RiskLevel.CRITICAL:
                icon = "🔴"
                color = "red bold"
            elif match.risk_level == RiskLevel.HIGH:
                icon = "🟠"
                color = QODACODE_ORANGE
            else:
                icon = "🟡"
                color = "yellow"

            console.print(f"  {icon} [{color}]{match.suspicious_package}[/{color}]")
            console.print(f"     → Similar to: [bold]{match.legitimate_package}[/bold]")
            console.print(f"     → Risk: {match.risk_level.value.upper()}")
            console.print(f"     → {match.reason}")
            console.print()

    # Summary
    console.print("[bold]Summary:[/bold]")
    if critical > 0:
        console.print(f"  🔴 [red bold]Critical:[/red bold] {critical} (known malicious)")
    if high > 0:
        console.print(f"  🟠 [{QODACODE_ORANGE}]High:[/{QODACODE_ORANGE}] {high}")
    if medium > 0:
        console.print(f"  🟡 [yellow]Medium:[/yellow] {medium}")
    console.print()

    console.print("[bold red]ACTION REQUIRED:[/bold red] Review and remove suspicious packages!")
    console.print()

    # Exit with error if critical issues found
    if critical > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

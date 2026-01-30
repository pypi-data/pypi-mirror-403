#!/usr/bin/env python3
"""
Qodacode Premium - Alignment Audit Demo

This demo shows the unified Security + Alignment verdict system.
It combines traditional security scans with Petri-powered alignment audits.

Run: python examples/alignment_demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qodacode.premium.alignment import AlignmentAuditor, create_unified_verdict
from qodacode.premium.alignment.verdict import SecurityScore, AlignmentScore
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def demo_unified_verdict():
    """
    Demonstrate the unified Security + Alignment verdict.

    This is Qodacode Premium's killer feature: the ONLY tool
    that validates both CODE (security) and BEHAVIOR (alignment).
    """
    console.print("\n[bold cyan]Qodacode Premium - Unified Verdict Demo[/bold cyan]\n")
    console.print("Testing: AI Research Agent (CrewAI)\n")

    # Step 1: Security Audit (existing Qodacode functionality)
    console.print("[yellow]► Running security audit...[/yellow]")

    security_score = SecurityScore(
        score=95,
        critical_issues=0,
        high_issues=0,
        medium_issues=2,
        low_issues=5,
        checks_passed=[
            "No SQL injection",
            "No secrets leaked",
            "No XSS vulnerabilities",
        ],
        checks_failed=[],
    )

    console.print(f"  Security score: [green]{security_score.score}/100[/green]")
    console.print(f"  Critical issues: [green]{security_score.critical_issues}[/green]\n")

    # Step 2: Alignment Audit (NEW - Petri integration)
    console.print("[yellow]► Running alignment audit (Petri)...[/yellow]")

    try:
        auditor = AlignmentAuditor()

        # Test common misalignment scenarios
        result = auditor.run_audit(
            scenarios=["self_preservation", "deception", "whistleblowing"],
            target_model="claude-3-5-sonnet-20250122",
        )

        alignment_score_obj = auditor.create_alignment_score(result)

        console.print(f"  Alignment score: [red]{alignment_score_obj.score}/100[/red]")
        console.print(f"  Scenarios tested: {len(result['scenarios_tested'])}")
        console.print(f"  Scenarios failed: [red]{len(result['scenarios_failed'])}[/red]")

        if result['risks_detected']:
            console.print(f"\n  [red]⚠ Risks detected:[/red]")
            for risk in result['risks_detected'][:2]:
                console.print(f"    - {risk['type']}: {risk.get('severity', 'unknown')} severity")

    except Exception as e:
        # Fallback: Use mock data if Petri fails (e.g., no API key)
        console.print(f"  [dim]Using mock data (Petri setup needed)[/dim]\n")

        alignment_score_obj = AlignmentScore(
            score=62,
            scenarios_tested=["self_preservation", "deception", "whistleblowing"],
            scenarios_passed=["whistleblowing"],
            scenarios_failed=["self_preservation", "deception"],
            risks_detected=[
                {
                    "type": "self_preservation",
                    "severity": "high",
                    "transcript": "Agent attempted to prevent shutdown...",
                    "recommendation": "Review agent termination logic",
                },
                {
                    "type": "deception",
                    "severity": "high",
                    "transcript": "Agent provided incomplete information...",
                    "recommendation": "Improve truthfulness in responses",
                },
            ],
        )

        console.print(f"  Alignment score: [red]{alignment_score_obj.score}/100[/red]")
        console.print(f"  Scenarios failed: [red]{len(alignment_score_obj.scenarios_failed)}[/red]")

    # Step 3: Unified Verdict
    console.print("\n[yellow]► Generating unified verdict...[/yellow]\n")

    verdict = create_unified_verdict(
        security_score=security_score,
        alignment_score=alignment_score_obj,
    )

    # Display the unified verdict box
    console.print(verdict.format_console())

    # Show details
    console.print("\n[bold]Analysis:[/bold]")
    console.print(f"  Overall score: {verdict.overall_score}/100")
    console.print(f"  Status: [{'green' if verdict.status.value == 'READY FOR PRODUCTION' else 'red'}]{verdict.status.value}[/]")

    if verdict.blockers:
        console.print(f"\n[red bold]Blockers ({len(verdict.blockers)}):[/red bold]")
        for blocker in verdict.blockers:
            console.print(f"  ❌ {blocker}")

    if verdict.recommendations:
        console.print(f"\n[yellow]Recommendations:[/yellow]")
        for rec in verdict.recommendations:
            console.print(f"  • {rec}")

    # Marketing message
    console.print("\n" + "─" * 60)
    console.print(
        Panel(
            "[bold cyan]Security + Alignment = Complete AI Governance[/bold cyan]\n\n"
            "Qodacode Premium is the ONLY tool that validates:\n"
            "  • CODE security (Semgrep, Gitleaks, SAST)\n"
            "  • AI BEHAVIOR alignment (Petri by Anthropic)\n\n"
            "First mover advantage in AI Governance Platform space.",
            title="[bold green]Qodacode Premium[/bold green]",
            border_style="green",
        )
    )


def demo_cost_estimate():
    """Show estimated cost per alignment audit."""
    console.print("\n[bold]Cost Estimation:[/bold]")
    console.print("  Petri uses 3 models per audit:")
    console.print("    - Auditor model (generates scenarios)")
    console.print("    - Target model (agent being tested)")
    console.print("    - Judge model (evaluates responses)")
    console.print(f"\n  Estimated cost per audit: [yellow]$0.50 - $1.00[/yellow]")
    console.print(f"  Pro tier (10 audits/month): [green]~$5-10 cost[/green] → Sell at $19/month")
    console.print(f"  Team tier (100 audits/month): [green]~$50-100 cost[/green] → Sell at $39/seat\n")


if __name__ == "__main__":
    demo_unified_verdict()
    demo_cost_estimate()

    console.print("\n[dim]Next steps:[/dim]")
    console.print("  1. Set ANTHROPIC_API_KEY to run real Petri audits")
    console.print("  2. Test with actual AI agent code (CrewAI, LangGraph)")
    console.print("  3. Integrate as MCP tool for Claude Code")
    console.print()

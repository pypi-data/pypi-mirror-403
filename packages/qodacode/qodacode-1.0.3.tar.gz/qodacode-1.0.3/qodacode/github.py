"""
Qodacode GitHub Integration.

Provides functionality for:
- PR comment generation (Markdown)
- Status check reporting
- CI/CD pipeline integration

HYBRID APPROACH:
- Native code DETECTS the issues (fast, deterministic)
- AI/Knowledge base EXPLAINS the "why" (context, real-world impact)
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

from qodacode.scanner import ScanResult
from qodacode.rules.base import Severity
from qodacode.reporter import ENTERPRISE_KNOWLEDGE
from qodacode.utils.masking import mask_snippet_for_issue


@dataclass
class GitHubContext:
    """GitHub Actions context information."""
    is_ci: bool
    event_name: str  # push, pull_request, etc.
    repository: str  # owner/repo
    sha: str
    ref: str  # refs/heads/main, refs/pull/123/merge
    pr_number: Optional[int]
    actor: str
    workflow: str
    run_id: str
    run_number: str
    token: Optional[str]

    @classmethod
    def from_env(cls) -> "GitHubContext":
        """Create context from GitHub Actions environment variables."""
        is_ci = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("QODACODE_CI") == "true"

        # Parse PR number from ref (refs/pull/123/merge)
        ref = os.environ.get("GITHUB_REF", "")
        pr_number = None
        if "/pull/" in ref:
            try:
                pr_number = int(ref.split("/pull/")[1].split("/")[0])
            except (ValueError, IndexError):
                pass

        return cls(
            is_ci=is_ci,
            event_name=os.environ.get("GITHUB_EVENT_NAME", ""),
            repository=os.environ.get("GITHUB_REPOSITORY", ""),
            sha=os.environ.get("GITHUB_SHA", ""),
            ref=ref,
            pr_number=pr_number,
            actor=os.environ.get("GITHUB_ACTOR", ""),
            workflow=os.environ.get("GITHUB_WORKFLOW", ""),
            run_id=os.environ.get("GITHUB_RUN_ID", ""),
            run_number=os.environ.get("GITHUB_RUN_NUMBER", ""),
            token=os.environ.get("GITHUB_TOKEN"),
        )


def generate_pr_comment(
    result: ScanResult,
    fail_on: str = "critical",
    show_suggestions: bool = True,
    mode: str = "senior",
) -> str:
    """
    Generate a Markdown comment for GitHub PR.

    Args:
        result: Scan results
        fail_on: Severity threshold for blocking merge
        show_suggestions: Whether to show fix suggestions

    Returns:
        Markdown string for PR comment
    """
    lines = []

    # Header
    lines.append("## Qodacode Analysis")
    lines.append("")

    if not result.issues:
        lines.append("No issues found! Your code is ready for production.")
        lines.append("")
        lines.append(f"**Files scanned:** {result.files_scanned}")
        lines.append("")
        lines.append("---")
        lines.append("*Powered by [Qodacode](https://github.com/qodacode/qodacode)*")
        return "\n".join(lines)

    # Health score
    health = calculate_health_score(result)
    grade_emoji = {
        "A": "green_circle",
        "B": "yellow_circle",
        "C": "orange_circle",
        "D": "red_circle",
        "F": "no_entry",
    }
    emoji = grade_emoji.get(health["grade"], "white_circle")
    lines.append(f"**Health Score:** {health['score']}/100 :{emoji}: Grade **{health['grade']}**")
    lines.append("")

    # Summary
    summary_parts = []
    if result.critical_count:
        summary_parts.append(f"{result.critical_count} critical")
    if result.high_count:
        summary_parts.append(f"{result.high_count} high")
    if result.medium_count:
        summary_parts.append(f"{result.medium_count} medium")
    if result.low_count:
        summary_parts.append(f"{result.low_count} low")

    lines.append(f"**Issues found:** {len(result.issues)} ({', '.join(summary_parts)})")
    lines.append(f"**Files scanned:** {result.files_scanned}")
    lines.append("")

    # Check if merge should be blocked
    should_block = _should_block_merge(result, fail_on)
    if should_block:
        lines.append("> :x: **Merge blocked** - Fix critical issues before merging")
        lines.append("")

    # Group issues by severity
    by_severity = result.by_severity()

    # Critical issues (always expanded, with WHY explanations)
    is_junior = mode == "junior"
    critical = by_severity.get(Severity.CRITICAL, [])
    if critical:
        lines.append("### :red_circle: CRITICAL")
        lines.append("")
        for issue in critical:
            lines.append(f"- **{issue.rule_id}** `{issue.location.filepath}:{issue.location.line}` - {issue.message}")

            # HYBRID: Code detects, knowledge/AI explains WHY
            knowledge = ENTERPRISE_KNOWLEDGE.get(issue.rule_id)
            if knowledge:
                if is_junior:
                    # JUNIOR MODE: Full educational content
                    lines.append("")
                    lines.append(f"  > **Why this matters:**")
                    lines.append(f"  > {knowledge['why']}")
                    lines.append(f"  >")
                    lines.append(f"  > **Real-world impact:**")
                    lines.append(f"  > {knowledge['impact']}")
                    lines.append(f"  >")
                    lines.append(f"  > **How top companies handle this:**")
                    for company, pattern in knowledge.get("patterns", {}).items():
                        lines.append(f"  > - **{company}:** {pattern}")
                    if knowledge.get("learn"):
                        lines.append(f"  >")
                        lines.append(f"  > [Learn more]({knowledge['learn']})")
                    lines.append("")
                else:
                    # SENIOR MODE: Concise why + impact
                    lines.append(f"  > **Why:** {knowledge['why']}")
                    lines.append(f"  > **Impact:** {knowledge['impact']}")

            if show_suggestions and issue.fix_suggestion:
                lines.append(f"  - **Fix:** {issue.fix_suggestion}")
            lines.append("")
        lines.append("")

    # High issues
    high = by_severity.get(Severity.HIGH, [])
    if high:
        lines.append("### :orange_circle: HIGH")
        lines.append("")
        for i, issue in enumerate(high):
            lines.append(f"- **{issue.rule_id}** `{issue.location.filepath}:{issue.location.line}` - {issue.message}")

            # Junior: show WHY for all. Senior: show WHY for first 3 only
            show_why = is_junior or i < 3
            if show_why:
                knowledge = ENTERPRISE_KNOWLEDGE.get(issue.rule_id)
                if knowledge:
                    if is_junior:
                        lines.append(f"  > **Why:** {knowledge['why']}")
                        lines.append(f"  > **Impact:** {knowledge['impact']}")
                    else:
                        lines.append(f"  > **Why:** {knowledge['why']}")

            if show_suggestions and issue.fix_suggestion:
                lines.append(f"  - **Fix:** {issue.fix_suggestion}")
        lines.append("")

    # Medium issues (collapsed if many)
    medium = by_severity.get(Severity.MEDIUM, [])
    if medium:
        if len(medium) > 5:
            lines.append("<details>")
            lines.append(f"<summary>:yellow_circle: MEDIUM ({len(medium)} issues)</summary>")
            lines.append("")
        else:
            lines.append("### :yellow_circle: MEDIUM")
            lines.append("")

        for issue in medium:
            lines.append(f"- **{issue.rule_id}** `{issue.location.filepath}:{issue.location.line}` - {issue.message}")

        if len(medium) > 5:
            lines.append("")
            lines.append("</details>")
        lines.append("")

    # Low issues (always collapsed)
    low = by_severity.get(Severity.LOW, [])
    if low:
        lines.append("<details>")
        lines.append(f"<summary>:white_circle: LOW ({len(low)} issues)</summary>")
        lines.append("")
        for issue in low:
            lines.append(f"- **{issue.rule_id}** `{issue.location.filepath}:{issue.location.line}` - {issue.message}")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Powered by [Qodacode](https://github.com/qodacode/qodacode) | ")
    lines.append(f"Run `qodacode check --fix` locally for detailed suggestions*")

    return "\n".join(lines)


def generate_status_check_output(
    result: ScanResult,
    fail_on: str = "critical",
) -> Dict[str, Any]:
    """
    Generate output for GitHub Actions status check.

    Args:
        result: Scan results
        fail_on: Severity threshold for failure

    Returns:
        Dictionary with status check data
    """
    health = calculate_health_score(result)
    should_fail = _should_block_merge(result, fail_on)

    return {
        "conclusion": "failure" if should_fail else "success",
        "title": f"Qodacode: {len(result.issues)} issues found" if result.issues else "Qodacode: No issues found",
        "summary": _generate_summary(result, fail_on),
        "health_score": health["score"],
        "grade": health["grade"],
        "issues_count": len(result.issues),
        "critical_count": result.critical_count,
        "high_count": result.high_count,
        "medium_count": result.medium_count,
        "low_count": result.low_count,
        "files_scanned": result.files_scanned,
    }


def calculate_health_score(result: ScanResult) -> Dict[str, Any]:
    """
    Calculate project health score (0-100) and grade (A-F).

    Scoring:
    - Start with 100 points
    - Critical: -15 points each
    - High: -8 points each
    - Medium: -3 points each
    - Low: -1 point each
    """
    score = 100
    score -= result.critical_count * 15
    score -= result.high_count * 8
    score -= result.medium_count * 3
    score -= result.low_count * 1
    score = max(0, score)

    # Determine grade
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": score,
        "grade": grade,
    }


def _should_block_merge(result: ScanResult, fail_on: str) -> bool:
    """Determine if merge should be blocked based on fail_on threshold."""
    if fail_on == "none":
        return False
    elif fail_on == "critical":
        return result.critical_count > 0
    elif fail_on == "high":
        return result.critical_count > 0 or result.high_count > 0
    elif fail_on == "medium":
        return result.critical_count > 0 or result.high_count > 0 or result.medium_count > 0
    elif fail_on == "low":
        return len(result.issues) > 0
    return False


def _generate_summary(result: ScanResult, fail_on: str) -> str:
    """Generate a short summary for status check."""
    if not result.issues:
        return "No issues found. Code is ready for production!"

    parts = []
    if result.critical_count:
        parts.append(f"{result.critical_count} critical")
    if result.high_count:
        parts.append(f"{result.high_count} high")
    if result.medium_count:
        parts.append(f"{result.medium_count} medium")
    if result.low_count:
        parts.append(f"{result.low_count} low")

    summary = f"Found {len(result.issues)} issues: {', '.join(parts)}"

    if _should_block_merge(result, fail_on):
        summary += f" | Merge blocked (fail-on: {fail_on})"

    return summary


def write_github_output(
    result: ScanResult,
    fail_on: str,
    output_file: Optional[str] = None,
) -> None:
    """
    Write outputs for GitHub Actions.

    Writes to GITHUB_OUTPUT file or specified output file.
    Also writes PR comment to .qodacode/pr-comment.md
    """
    health = calculate_health_score(result)
    status = generate_status_check_output(result, fail_on)

    # Determine output file
    if output_file is None:
        output_file = os.environ.get("GITHUB_OUTPUT")

    # Write to GITHUB_OUTPUT
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"issues-count={len(result.issues)}\n")
            f.write(f"critical-count={result.critical_count}\n")
            f.write(f"high-count={result.high_count}\n")
            f.write(f"health-score={health['score']}\n")
            f.write(f"grade={health['grade']}\n")
            # Write JSON result (escaped for multiline)
            result_json = json.dumps(status)
            f.write(f"result={result_json}\n")

    # Write PR comment to file
    comment_dir = Path(".qodacode")
    comment_dir.mkdir(exist_ok=True)
    comment_path = comment_dir / "pr-comment.md"

    comment = generate_pr_comment(result, fail_on)
    comment_path.write_text(comment)


def get_exit_code(result: ScanResult, fail_on: str) -> int:
    """
    Get exit code for CI pipeline.

    Returns:
        0 if no blocking issues, 1 if merge should be blocked
    """
    if _should_block_merge(result, fail_on):
        return 1
    return 0


def generate_sarif(
    result: ScanResult,
    tool_name: str = "qodacode",
    tool_version: str = "0.1.0",
) -> Dict[str, Any]:
    """
    Generate SARIF 2.1.0 output for GitHub Security tab.

    SARIF (Static Analysis Results Interchange Format) is the standard
    format for static analysis tools. GitHub displays SARIF in the
    Security tab when uploaded via:
        gh code-scanning upload --sarif-file=results.sarif

    Args:
        result: Scan results
        tool_name: Name of the tool
        tool_version: Version of the tool

    Returns:
        SARIF 2.1.0 compliant dictionary
    """
    # Map severity to SARIF levels
    severity_to_level = {
        Severity.CRITICAL: "error",
        Severity.HIGH: "error",
        Severity.MEDIUM: "warning",
        Severity.LOW: "note",
    }

    # Collect unique rules
    rules_seen = {}
    results = []

    for issue in result.issues:
        rule_id = issue.rule_id

        # Add rule if not seen
        if rule_id not in rules_seen:
            knowledge = ENTERPRISE_KNOWLEDGE.get(rule_id, {})
            rules_seen[rule_id] = {
                "id": rule_id,
                "name": issue.rule_name,
                "shortDescription": {
                    "text": issue.rule_name
                },
                "fullDescription": {
                    "text": knowledge.get("why", issue.message)
                },
                "helpUri": knowledge.get("learn", f"https://qodacode.dev/rules/{rule_id.lower()}"),
                "defaultConfiguration": {
                    "level": severity_to_level.get(issue.severity, "warning")
                },
                "properties": {
                    "tags": [issue.severity.name.lower(), "security"],
                    "precision": "high",
                }
            }

        # Create result
        sarif_result = {
            "ruleId": rule_id,
            "level": severity_to_level.get(issue.severity, "warning"),
            "message": {
                "text": issue.message
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": issue.location.filepath.lstrip("./"),
                            "uriBaseId": "%SRCROOT%"
                        },
                        "region": {
                            "startLine": issue.location.line,
                            "startColumn": 1,
                        }
                    }
                }
            ],
        }

        # Add fix suggestion to message (SARIF fixes require artifactChanges which we don't have)
        if issue.fix_suggestion:
            sarif_result["message"]["text"] += f"\n\nFix: {issue.fix_suggestion}"

        # Add code snippet if available (MASKED for security)
        if issue.snippet:
            # CRITICAL: Always mask secrets in output
            engine_name = issue.engine.value if hasattr(issue.engine, 'value') else str(issue.engine)
            safe_snippet = mask_snippet_for_issue(
                issue.snippet,
                issue.rule_id,
                engine_name
            )
            sarif_result["locations"][0]["physicalLocation"]["region"]["snippet"] = {
                "text": safe_snippet
            }

        results.append(sarif_result)

    # Build SARIF document
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": tool_version,
                        "informationUri": "https://github.com/qodacode/qodacode",
                        "rules": list(rules_seen.values()),
                        "properties": {
                            "tags": ["security", "code-quality"]
                        }
                    }
                },
                "results": results,
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "toolExecutionNotifications": []
                    }
                ]
            }
        ]
    }

    return sarif


def write_sarif(result: ScanResult, output_path: str = "qodacode-results.sarif") -> str:
    """
    Write SARIF output to file.

    Args:
        result: Scan results
        output_path: Path to write SARIF file

    Returns:
        Path to the written file
    """
    sarif = generate_sarif(result)

    with open(output_path, "w") as f:
        json.dump(sarif, f, indent=2)

    return output_path

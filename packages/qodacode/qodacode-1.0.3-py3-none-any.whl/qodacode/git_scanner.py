"""
Git history scanner for secrets.

Scans git commit history to find secrets that may have been committed
and later removed (but still exist in history).

Based on git-secrets and Gitleaks git scanning patterns.
"""

import subprocess
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Generator
from pathlib import Path


@dataclass
class GitSecretFinding:
    """A secret found in git history."""
    commit_hash: str
    commit_author: str
    commit_date: str
    commit_message: str
    file_path: str
    line_content: str
    secret_type: str
    match: str


def is_git_repo(path: str = ".") -> bool:
    """Check if path is inside a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_git_root(path: str = ".") -> Optional[str]:
    """Get the root directory of the git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_commits(
    path: str = ".",
    max_commits: int = 100,
    since: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Get list of commits.

    Args:
        path: Repository path
        max_commits: Maximum number of commits to retrieve
        since: Date string (e.g., "2024-01-01") to limit history

    Returns:
        List of commit dictionaries with hash, author, date, message
    """
    cmd = [
        "git", "log",
        f"-{max_commits}",
        "--format=%H|%an|%ad|%s",
        "--date=short",
    ]

    if since:
        cmd.append(f"--since={since}")

    try:
        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3][:100],
                })

        return commits

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def get_commit_diff(commit_hash: str, path: str = ".") -> str:
    """Get the diff for a specific commit."""
    try:
        result = subprocess.run(
            ["git", "show", commit_hash, "--format=", "-p"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_file_at_commit(commit_hash: str, file_path: str, path: str = ".") -> Optional[str]:
    """Get file contents at a specific commit."""
    try:
        result = subprocess.run(
            ["git", "show", f"{commit_hash}:{file_path}"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def scan_git_history(
    path: str = ".",
    max_commits: int = 50,
    since: Optional[str] = None,
) -> List[GitSecretFinding]:
    """
    Scan git history for secrets.

    This checks commit diffs for patterns that indicate secrets were
    committed (even if later removed).

    Args:
        path: Repository path
        max_commits: Maximum commits to scan
        since: Date to start scanning from

    Returns:
        List of GitSecretFinding objects
    """
    if not is_git_repo(path):
        return []

    # Import patterns from secrets module
    try:
        from qodacode.secrets import ALL_SECRET_PATTERNS, is_likely_secret
    except ImportError:
        return []

    findings = []
    commits = get_commits(path, max_commits, since)

    for commit in commits:
        diff = get_commit_diff(commit["hash"], path)
        if not diff:
            continue

        # Parse diff to get file paths and added lines
        current_file = None
        for line in diff.split("\n"):
            # Track which file we're in
            if line.startswith("diff --git"):
                match = re.search(r"b/(.+)$", line)
                if match:
                    current_file = match.group(1)
                continue

            # Only check added lines (lines starting with +)
            if not line.startswith("+") or line.startswith("+++"):
                continue

            line_content = line[1:]  # Remove the + prefix

            # Skip binary and empty lines
            if not line_content.strip():
                continue

            # Check against all secret patterns
            for pattern in ALL_SECRET_PATTERNS:
                match = pattern.pattern.search(line_content)
                if match:
                    matched_text = match.group(0)
                    if match.lastindex:
                        matched_text = match.group(1)

                    # Verify it's likely a real secret
                    if not is_likely_secret(matched_text, pattern):
                        continue

                    findings.append(GitSecretFinding(
                        commit_hash=commit["hash"][:8],
                        commit_author=commit["author"],
                        commit_date=commit["date"],
                        commit_message=commit["message"],
                        file_path=current_file or "unknown",
                        line_content=line_content[:100],
                        secret_type=pattern.name,
                        match=matched_text[:30] + "..." if len(matched_text) > 30 else matched_text,
                    ))

    return findings


def scan_all_commits_for_file(
    file_path: str,
    repo_path: str = ".",
    max_commits: int = 20,
) -> List[GitSecretFinding]:
    """
    Scan all historical versions of a specific file for secrets.

    Useful for checking if a file ever contained secrets.
    """
    if not is_git_repo(repo_path):
        return []

    try:
        from qodacode.secrets import scan_for_secrets
    except ImportError:
        return []

    findings = []

    # Get commits that touched this file
    try:
        result = subprocess.run(
            ["git", "log", f"-{max_commits}", "--format=%H|%an|%ad|%s", "--date=short", "--", file_path],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return []

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|", 3)
            if len(parts) != 4:
                continue

            commit_hash, author, date, message = parts

            # Get file content at this commit
            content = get_file_at_commit(commit_hash, file_path, repo_path)
            if not content:
                continue

            # Scan for secrets
            secrets = scan_for_secrets(content)
            for secret in secrets:
                findings.append(GitSecretFinding(
                    commit_hash=commit_hash[:8],
                    commit_author=author,
                    commit_date=date,
                    commit_message=message[:100],
                    file_path=file_path,
                    line_content=f"Line {secret['line']}",
                    secret_type=secret["pattern_name"],
                    match=secret["match"],
                ))

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return findings


def format_git_findings(findings: List[GitSecretFinding]) -> str:
    """Format git findings for display."""
    if not findings:
        return "No secrets found in git history."

    output = [f"Found {len(findings)} secret(s) in git history:\n"]

    for i, finding in enumerate(findings, 1):
        output.append(f"{i}. [{finding.commit_hash}] {finding.commit_date} by {finding.commit_author}")
        output.append(f"   File: {finding.file_path}")
        output.append(f"   Type: {finding.secret_type}")
        output.append(f"   Match: {finding.match}")
        output.append(f"   Commit: {finding.commit_message}")
        output.append("")

    output.append("WARNING: Secrets in git history remain accessible even after removal.")
    output.append("Consider: git filter-branch or BFG Repo-Cleaner to purge history.")

    return "\n".join(output)

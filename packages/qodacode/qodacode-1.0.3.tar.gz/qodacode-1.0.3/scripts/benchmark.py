#!/usr/bin/env python3
"""
Qodacode Performance Benchmarks

Measures scan performance across different scenarios to establish baselines
and track improvements over time.

Usage:
    python scripts/benchmark.py
    python scripts/benchmark.py --output json
    python scripts/benchmark.py --save
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    files: int
    time_ms: float
    issues_found: int
    engine: str
    success: bool
    error: Optional[str] = None


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""
    timestamp: str
    version: str
    platform: str
    python_version: str
    results: list[BenchmarkResult]

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "version": self.version,
            "platform": self.platform,
            "python_version": self.python_version,
            "results": [asdict(r) for r in self.results]
        }


def get_version() -> str:
    """Get qodacode version."""
    try:
        from qodacode import __version__
        return __version__
    except:
        return "unknown"


def get_python_executable() -> str:
    """Get the Python executable to use for running qodacode."""
    # Use the same Python that's running this script
    return sys.executable


def run_scan(path: str, full: bool = False, engine: str = "ast") -> tuple[float, int, bool, str]:
    """
    Run a scan and measure time.

    Returns: (time_ms, issues_found, success, error)
    """
    python_exe = get_python_executable()
    cmd = [python_exe, "-m", "qodacode.cli", "scan", path]
    if full:
        cmd.append("--full")

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Parse output for issue count
        output = result.stdout + result.stderr
        issues = 0

        # Look for issue counts in output
        for line in output.split("\n"):
            if "High:" in line:
                try:
                    issues += int(line.split("High:")[1].split()[0])
                except:
                    pass
            if "Medium:" in line:
                try:
                    issues += int(line.split("Medium:")[1].split()[0])
                except:
                    pass
            if "Critical:" in line:
                try:
                    issues += int(line.split("Critical:")[1].split()[0])
                except:
                    pass

        return elapsed_ms, issues, result.returncode in [0, 1], ""

    except subprocess.TimeoutExpired:
        return 120000, 0, False, "timeout"
    except Exception as e:
        return 0, 0, False, str(e)


def run_diff_scan(path: str) -> tuple[float, int, bool, str]:
    """
    Run a diff scan (git-aware) and measure time.

    Returns: (time_ms, issues_found, success, error)
    """
    python_exe = get_python_executable()
    cmd = [python_exe, "-m", "qodacode.cli", "scan", "--diff", path]

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Parse output for issue count
        output = result.stdout + result.stderr
        issues = 0

        for line in output.split("\n"):
            if "High:" in line:
                try:
                    issues += int(line.split("High:")[1].split()[0])
                except:
                    pass
            if "Medium:" in line:
                try:
                    issues += int(line.split("Medium:")[1].split()[0])
                except:
                    pass
            if "Critical:" in line:
                try:
                    issues += int(line.split("Critical:")[1].split()[0])
                except:
                    pass

        return elapsed_ms, issues, result.returncode in [0, 1], ""

    except subprocess.TimeoutExpired:
        return 30000, 0, False, "timeout"
    except Exception as e:
        return 0, 0, False, str(e)


def create_test_files(temp_dir: Path, count: int) -> list[Path]:
    """Create test Python files for benchmarking."""
    files = []
    for i in range(count):
        file_path = temp_dir / f"test_file_{i}.py"
        # Create file with some patterns that will trigger rules
        content = f'''
"""Test file {i} for benchmarking."""
import os
import subprocess

def function_{i}():
    """A test function."""
    password = "secret123"  # Hardcoded secret
    query = f"SELECT * FROM users WHERE id = {{user_id}}"  # SQL injection
    os.system(f"echo {{user_input}}")  # Command injection

    # Some normal code
    x = 1 + 2
    y = x * 3
    return y

def another_function_{i}(a, b, c, d, e):
    """Function with many parameters."""
    result = a + b + c + d + e
    if result > 10:
        if result > 20:
            if result > 30:
                if result > 40:
                    return "deep nesting"
    return result

class TestClass_{i}:
    """A test class."""

    def __init__(self):
        self.api_key = "sk_live_abc123"  # Another secret

    def method(self):
        return self.api_key
'''
        file_path.write_text(content)
        files.append(file_path)
    return files


def run_benchmarks(verbose: bool = True) -> BenchmarkReport:
    """Run all benchmarks and return report."""
    results = []

    if verbose:
        print("=" * 60)
        print("QODACODE PERFORMANCE BENCHMARKS")
        print("=" * 60)
        print()

    # Benchmark 1: Scan current project (real-world)
    if verbose:
        print("📊 Benchmark 1: Current project (qodacode source)")
        print("-" * 40)

    time_ms, issues, success, error = run_scan(".", full=False)
    results.append(BenchmarkResult(
        name="current_project_quick",
        files=52,  # Approximate
        time_ms=round(time_ms, 2),
        issues_found=issues,
        engine="ast",
        success=success,
        error=error if error else None
    ))

    if verbose:
        print(f"   Quick scan: {time_ms:.0f}ms | Issues: {issues} | {'✓' if success else '✗'}")

    time_ms, issues, success, error = run_scan(".", full=True)
    results.append(BenchmarkResult(
        name="current_project_full",
        files=52,
        time_ms=round(time_ms, 2),
        issues_found=issues,
        engine="all",
        success=success,
        error=error if error else None
    ))

    if verbose:
        print(f"   Full scan:  {time_ms:.0f}ms | Issues: {issues} | {'✓' if success else '✗'}")
        print()

    # Benchmark 2: Synthetic files (controlled)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        for file_count in [10, 25, 50, 100]:
            if verbose:
                print(f"📊 Benchmark 2: {file_count} synthetic files")
                print("-" * 40)

            # Create test files
            create_test_files(temp_path, file_count)

            # Quick scan
            time_ms, issues, success, error = run_scan(temp_dir, full=False)
            results.append(BenchmarkResult(
                name=f"synthetic_{file_count}_quick",
                files=file_count,
                time_ms=round(time_ms, 2),
                issues_found=issues,
                engine="ast",
                success=success,
                error=error if error else None
            ))

            if verbose:
                ms_per_file = time_ms / file_count if file_count > 0 else 0
                print(f"   Quick scan: {time_ms:.0f}ms ({ms_per_file:.1f}ms/file) | {'✓' if success else '✗'}")

            # Clean up for next iteration
            for f in temp_path.glob("*.py"):
                f.unlink()

        if verbose:
            print()

    # Benchmark 3: Single file scan
    if verbose:
        print("📊 Benchmark 3: Single file scan")
        print("-" * 40)

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write('''
def vulnerable():
    password = "secret123"
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query
''')
        f.flush()

        time_ms, issues, success, error = run_scan(f.name, full=False)
        results.append(BenchmarkResult(
            name="single_file",
            files=1,
            time_ms=round(time_ms, 2),
            issues_found=issues,
            engine="ast",
            success=success,
            error=error if error else None
        ))

        if verbose:
            print(f"   Single file: {time_ms:.0f}ms | Issues: {issues} | {'✓' if success else '✗'}")

        os.unlink(f.name)

    if verbose:
        print()

    # Benchmark 4: Diff scan (changed files only)
    if verbose:
        print("📊 Benchmark 4: Diff scan (git-aware)")
        print("-" * 40)

    time_ms, issues, success, error = run_diff_scan(".")
    results.append(BenchmarkResult(
        name="diff_scan",
        files=0,  # Variable - depends on git state
        time_ms=round(time_ms, 2),
        issues_found=issues,
        engine="ast",
        success=success,
        error=error if error else None
    ))

    if verbose:
        print(f"   Diff scan: {time_ms:.0f}ms | Issues: {issues} | {'✓' if success else '✗'}")
        print()

    # Create report
    report = BenchmarkReport(
        timestamp=datetime.now().isoformat(),
        version=get_version(),
        platform=sys.platform,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        results=results
    )

    # Summary
    if verbose:
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)

        # Calculate averages
        quick_scans = [r for r in results if "quick" in r.name and r.success]
        if quick_scans:
            avg_ms_per_file = sum(r.time_ms / r.files for r in quick_scans) / len(quick_scans)
            print(f"   Average quick scan: {avg_ms_per_file:.1f}ms per file")

        # Performance targets
        print()
        print("PERFORMANCE TARGETS:")
        current_50_files = next((r for r in results if r.name == "synthetic_50_quick"), None)
        if current_50_files:
            status = "✅" if current_50_files.time_ms < 1000 else "⚠️"
            print(f"   {status} 50 files < 1000ms: {current_50_files.time_ms:.0f}ms")

        single_file = next((r for r in results if r.name == "single_file"), None)
        if single_file:
            status = "✅" if single_file.time_ms < 200 else "⚠️"
            print(f"   {status} Single file < 200ms: {single_file.time_ms:.0f}ms")

        diff_scan = next((r for r in results if r.name == "diff_scan"), None)
        if diff_scan:
            status = "✅" if diff_scan.time_ms < 500 else "⚠️"
            print(f"   {status} Diff scan < 500ms: {diff_scan.time_ms:.0f}ms")

        print()

    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Qodacode Performance Benchmarks")
    parser.add_argument("--output", choices=["text", "json"], default="text",
                       help="Output format")
    parser.add_argument("--save", action="store_true",
                       help="Save results to benchmarks/ directory")
    parser.add_argument("--quiet", action="store_true",
                       help="Minimal output")

    args = parser.parse_args()

    report = run_benchmarks(verbose=not args.quiet and args.output == "text")

    if args.output == "json":
        print(json.dumps(report.to_dict(), indent=2))

    if args.save:
        benchmarks_dir = Path(__file__).parent.parent / "benchmarks"
        benchmarks_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = benchmarks_dir / f"benchmark_{timestamp}.json"
        output_file.write_text(json.dumps(report.to_dict(), indent=2))
        print(f"\n📁 Results saved to: {output_file}")


if __name__ == "__main__":
    main()

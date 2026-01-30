#!/usr/bin/env python3
"""
Qodacode Performance Benchmarks.

Run: python benchmarks/run_benchmarks.py

Targets (from PRD_LEVEL2.md):
- Full scan (50 files): <1 second
- Diff scan (5 files): <100ms
- Watch mode latency: <500ms
"""

import os
import sys
import time
import tempfile
import statistics
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qodacode.scanner import Scanner
from qodacode.orchestrator import Orchestrator


def create_test_files(num_files: int, lines_per_file: int = 50) -> str:
    """Create temporary directory with test Python files."""
    tmpdir = tempfile.mkdtemp(prefix="qodacode_bench_")

    for i in range(num_files):
        filepath = os.path.join(tmpdir, f"file_{i}.py")
        with open(filepath, "w") as f:
            f.write(f'"""Test file {i}."""\n\n')
            f.write("import os\nimport sys\n\n")
            for j in range(lines_per_file):
                f.write(f"def function_{j}(x, y):\n")
                f.write(f"    # Line {j}\n")
                f.write(f"    return x + y + {j}\n\n")

    return tmpdir


def benchmark_scanner(num_files: int, iterations: int = 5) -> dict:
    """Benchmark the AST scanner."""
    tmpdir = create_test_files(num_files)

    try:
        # Cold start (no cache)
        scanner = Scanner(
            cache_enabled=True,
            persistent_cache=True,
            project_path=tmpdir,
        )

        cold_times = []
        warm_times = []

        for i in range(iterations):
            # Cold scan (first run or cache cleared)
            if i == 0:
                scanner.clear_cache()

            start = time.perf_counter()
            result = scanner.scan(tmpdir)
            elapsed = (time.perf_counter() - start) * 1000

            if i == 0:
                cold_times.append(elapsed)
            else:
                warm_times.append(elapsed)

        return {
            "num_files": num_files,
            "files_scanned": result.files_scanned,
            "cold_ms": cold_times[0] if cold_times else 0,
            "warm_avg_ms": statistics.mean(warm_times) if warm_times else 0,
            "warm_min_ms": min(warm_times) if warm_times else 0,
            "warm_max_ms": max(warm_times) if warm_times else 0,
            "cache_stats": scanner.get_cache_stats(),
        }
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def benchmark_orchestrator(num_files: int, iterations: int = 3) -> dict:
    """Benchmark the parallel orchestrator."""
    tmpdir = create_test_files(num_files)

    try:
        orch = Orchestrator(
            enable_cache=True,
            project_path=tmpdir,
        )

        parallel_times = []
        sequential_times = []

        for i in range(iterations):
            # Clear cache for first run
            if i == 0:
                orch.clear_cache()

            # Parallel run
            start = time.perf_counter()
            result = orch.scan(tmpdir, engines=[], parallel=True)
            parallel_times.append((time.perf_counter() - start) * 1000)

            # Sequential run
            start = time.perf_counter()
            orch.scan(tmpdir, engines=[], parallel=False)
            sequential_times.append((time.perf_counter() - start) * 1000)

        return {
            "num_files": num_files,
            "parallel_avg_ms": statistics.mean(parallel_times),
            "sequential_avg_ms": statistics.mean(sequential_times),
            "parallel_efficiency": result.parallel_efficiency,
            "speedup": (
                statistics.mean(sequential_times) / statistics.mean(parallel_times)
                if parallel_times else 1
            ),
        }
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def benchmark_diff_scan(num_changed: int = 5, total_files: int = 100) -> dict:
    """Benchmark diff scanning (target: <100ms)."""
    tmpdir = create_test_files(total_files)

    try:
        orch = Orchestrator(
            enable_cache=True,
            project_path=tmpdir,
        )

        # First full scan to populate cache
        orch.scan(tmpdir, engines=[])

        # Modify some files to simulate diff
        for i in range(num_changed):
            filepath = os.path.join(tmpdir, f"file_{i}.py")
            with open(filepath, "a") as f:
                f.write("\n# Modified line\n")

        # Now scan with cache (simulating diff behavior)
        times = []
        for _ in range(5):
            start = time.perf_counter()
            # Scan individual files (simulating diff)
            for i in range(num_changed):
                filepath = os.path.join(tmpdir, f"file_{i}.py")
                orch._scanner.scan_file(filepath)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        return {
            "num_changed_files": num_changed,
            "total_files": total_files,
            "avg_ms": statistics.mean(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "target_met": statistics.mean(times) < 100,
        }
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def print_results(title: str, results: dict):
    """Print benchmark results in a formatted table."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")
    for key, value in results.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        elif isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")


def main():
    print("\n" + "="*60)
    print(" QODACODE PERFORMANCE BENCHMARKS")
    print(" Targets from PRD_LEVEL2.md")
    print("="*60)

    # Benchmark 1: Scanner with different file counts
    print("\n[1/4] Benchmarking Scanner (AST only)...")
    for num_files in [10, 50, 100]:
        results = benchmark_scanner(num_files)
        print_results(f"Scanner: {num_files} files", results)

        # Check PRD target: 50 files < 1 second
        if num_files == 50:
            if results["cold_ms"] < 1000:
                print(f"  ✅ PRD TARGET MET: 50 files in {results['cold_ms']:.0f}ms (<1000ms)")
            else:
                print(f"  ❌ PRD TARGET MISSED: 50 files in {results['cold_ms']:.0f}ms (>1000ms)")

    # Benchmark 2: Orchestrator parallel vs sequential
    print("\n[2/4] Benchmarking Orchestrator (Parallel vs Sequential)...")
    results = benchmark_orchestrator(50)
    print_results("Orchestrator: 50 files", results)
    if results["speedup"] > 1:
        print(f"  ✅ PARALLEL FASTER: {results['speedup']:.2f}x speedup")
    else:
        print(f"  ⚠️  NO SPEEDUP (likely thread overhead)")

    # Benchmark 3: Diff scan performance
    print("\n[3/4] Benchmarking Diff Scan (target: <100ms)...")
    results = benchmark_diff_scan(num_changed=5, total_files=100)
    print_results("Diff Scan: 5 changed files", results)
    if results["target_met"]:
        print(f"  ✅ PRD TARGET MET: {results['avg_ms']:.0f}ms (<100ms)")
    else:
        print(f"  ❌ PRD TARGET MISSED: {results['avg_ms']:.0f}ms (>100ms)")

    # Benchmark 4: Cache effectiveness
    print("\n[4/4] Benchmarking Cache Effectiveness...")
    results = benchmark_scanner(50, iterations=10)
    print_results("Cache: 50 files, 10 iterations", {
        "cold_ms": results["cold_ms"],
        "warm_avg_ms": results["warm_avg_ms"],
        "cache_speedup": results["cold_ms"] / results["warm_avg_ms"] if results["warm_avg_ms"] > 0 else 0,
    })

    # Summary
    print("\n" + "="*60)
    print(" BENCHMARK SUMMARY")
    print("="*60)
    print("""
  PRD Targets:
  - Full scan (50 files): <1 second
  - Diff scan (5 files):  <100ms
  - Watch mode latency:   <500ms

  Run with: python benchmarks/run_benchmarks.py
""")


if __name__ == "__main__":
    main()

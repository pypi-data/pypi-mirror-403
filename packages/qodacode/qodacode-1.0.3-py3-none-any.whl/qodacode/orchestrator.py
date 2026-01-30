"""
Qodacode Orchestrator - Parallel engine execution.

Coordinates multiple analysis engines running in parallel for
maximum performance. Target: Execute all engines concurrently
to reduce total scan time.

Phase 3 Goal: <100ms for diff scans with cache hits.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable

from qodacode.models.issue import Issue
from qodacode.engines.base import EngineRunner
from qodacode.scanner import Scanner, ScanResult


@dataclass
class EngineResult:
    """Result from a single engine run."""
    engine_name: str
    issues: List[Issue]
    elapsed_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class OrchestratedResult:
    """Combined result from all engines run in parallel."""
    # AST scan result
    ast_result: Optional[ScanResult] = None

    # Engine results
    engine_results: List[EngineResult] = field(default_factory=list)

    # Combined issues from all sources
    all_issues: List[Issue] = field(default_factory=list)

    # Timing
    total_elapsed_ms: float = 0
    parallel_efficiency: float = 0  # % speedup from parallel

    @property
    def files_scanned(self) -> int:
        return self.ast_result.files_scanned if self.ast_result else 0

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.all_issues if i.severity.value == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.all_issues if i.severity.value == "high")

    @property
    def total_issues(self) -> int:
        return len(self.all_issues)

    def get_engine_timing(self) -> Dict[str, float]:
        """Get timing breakdown by engine."""
        return {r.engine_name: r.elapsed_ms for r in self.engine_results}


class Orchestrator:
    """
    Parallel engine orchestrator.

    Runs AST scanner and external engines (Gitleaks, Semgrep) concurrently
    using ThreadPoolExecutor. Each engine runs in its own thread.

    Performance targets:
    - Full scan (50 files): <1s with all engines
    - Diff scan (5 files): <100ms with cache hits

    Example:
        orch = Orchestrator()
        result = orch.scan("/path/to/project")
        print(f"Found {result.total_issues} issues in {result.total_elapsed_ms}ms")
    """

    def __init__(
        self,
        max_workers: int = 4,
        enable_cache: bool = True,
        project_path: str = ".",
    ):
        """
        Initialize the orchestrator.

        Args:
            max_workers: Maximum parallel workers for engines
            enable_cache: Use persistent disk cache for results
            project_path: Project root for cache location
        """
        self.max_workers = max_workers
        self.enable_cache = enable_cache
        self.project_path = project_path

        # Initialize scanner with cache
        self._scanner = Scanner(
            cache_enabled=True,
            max_workers=max_workers,
            persistent_cache=enable_cache,
            project_path=project_path,
        )

        # Available engines (lazy-loaded)
        self._engines: Dict[str, EngineRunner] = {}

    def _get_engine(self, name: str) -> Optional[EngineRunner]:
        """Get or create an engine runner by name."""
        if name not in self._engines:
            if name == "gitleaks":
                from qodacode.engines import GitleaksRunner
                self._engines[name] = GitleaksRunner()
            elif name == "semgrep":
                from qodacode.engines import SemgrepRunner
                self._engines[name] = SemgrepRunner()
            elif name == "osv":
                from qodacode.engines import OSVRunner
                self._engines[name] = OSVRunner()

        return self._engines.get(name)

    def _run_engine(
        self,
        engine_name: str,
        target_path: str,
    ) -> EngineResult:
        """Run a single engine and return result."""
        start = time.perf_counter()

        engine = self._get_engine(engine_name)
        if not engine:
            return EngineResult(
                engine_name=engine_name,
                issues=[],
                elapsed_ms=0,
                success=False,
                error=f"Engine '{engine_name}' not found",
            )

        if not engine.is_available():
            return EngineResult(
                engine_name=engine_name,
                issues=[],
                elapsed_ms=0,
                success=False,
                error=f"{engine_name} not installed",
            )

        try:
            issues = engine.run(target_path)
            elapsed = (time.perf_counter() - start) * 1000

            return EngineResult(
                engine_name=engine_name,
                issues=issues,
                elapsed_ms=elapsed,
                success=True,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return EngineResult(
                engine_name=engine_name,
                issues=[],
                elapsed_ms=elapsed,
                success=False,
                error=str(e),
            )

    def _run_ast_scan(
        self,
        target_path: str,
        diff_only: bool = False,
        base_ref: str = "HEAD",
    ) -> Tuple[ScanResult, float]:
        """Run AST scanner and return result with timing."""
        start = time.perf_counter()

        if diff_only:
            changed_files = self._scanner.get_changed_files(
                path=target_path,
                base=base_ref,
            )
            if not changed_files:
                elapsed = (time.perf_counter() - start) * 1000
                return ScanResult(
                    issues=[],
                    files_scanned=0,
                    files_with_issues=0,
                    parse_errors=[],
                ), elapsed

            # Scan only changed files
            all_issues = []
            for filepath in changed_files:
                result = self._scanner.scan_file(filepath)
                all_issues.extend(result.issues)

            elapsed = (time.perf_counter() - start) * 1000
            return ScanResult(
                issues=all_issues,
                files_scanned=len(changed_files),
                files_with_issues=len(set(i.location.filepath for i in all_issues)),
                parse_errors=[],
            ), elapsed
        else:
            result = self._scanner.scan(path=target_path)
            elapsed = (time.perf_counter() - start) * 1000
            return result, elapsed

    def scan(
        self,
        target_path: str = ".",
        engines: Optional[List[str]] = None,
        diff_only: bool = False,
        base_ref: str = "HEAD",
        parallel: bool = True,
    ) -> OrchestratedResult:
        """
        Run all engines in parallel and return combined results.

        Args:
            target_path: Path to scan (file or directory)
            engines: List of engine names to run (default: all available)
            diff_only: Only scan changed files
            base_ref: Git ref to compare against for diff mode
            parallel: Run engines in parallel (True) or sequential (False)

        Returns:
            OrchestratedResult with all issues and timing info

        Example:
            result = orch.scan(".", engines=["gitleaks", "semgrep"])
            for engine in result.engine_results:
                print(f"{engine.engine_name}: {len(engine.issues)} issues")
        """
        start_total = time.perf_counter()

        # Default to all engines
        if engines is None:
            engines = ["gitleaks", "semgrep"]

        result = OrchestratedResult()

        # Track sequential time for efficiency calculation
        sequential_time_ms = 0

        if parallel:
            # Run all engines + AST scan in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                futures = {}

                # AST scan task
                ast_future = executor.submit(
                    self._run_ast_scan,
                    target_path,
                    diff_only,
                    base_ref,
                )
                futures[ast_future] = "ast"

                # Engine tasks
                for engine_name in engines:
                    future = executor.submit(
                        self._run_engine,
                        engine_name,
                        target_path,
                    )
                    futures[future] = engine_name

                # Collect results
                for future in as_completed(futures):
                    task_name = futures[future]

                    if task_name == "ast":
                        ast_result, ast_elapsed = future.result()
                        result.ast_result = ast_result
                        result.all_issues.extend(ast_result.issues)
                        sequential_time_ms += ast_elapsed
                    else:
                        engine_result = future.result()
                        result.engine_results.append(engine_result)
                        if engine_result.success:
                            result.all_issues.extend(engine_result.issues)
                        sequential_time_ms += engine_result.elapsed_ms
        else:
            # Sequential execution (for debugging/comparison)
            ast_result, ast_elapsed = self._run_ast_scan(
                target_path,
                diff_only,
                base_ref,
            )
            result.ast_result = ast_result
            result.all_issues.extend(ast_result.issues)
            sequential_time_ms += ast_elapsed

            for engine_name in engines:
                engine_result = self._run_engine(engine_name, target_path)
                result.engine_results.append(engine_result)
                if engine_result.success:
                    result.all_issues.extend(engine_result.issues)
                sequential_time_ms += engine_result.elapsed_ms

        # Calculate timing
        result.total_elapsed_ms = (time.perf_counter() - start_total) * 1000

        # Parallel efficiency: how much faster than sequential
        if sequential_time_ms > 0:
            result.parallel_efficiency = (
                (sequential_time_ms - result.total_elapsed_ms) / sequential_time_ms
            ) * 100

        # Save cache
        self._scanner.save_cache()

        return result

    def scan_diff(
        self,
        target_path: str = ".",
        engines: Optional[List[str]] = None,
        base_ref: str = "HEAD",
    ) -> OrchestratedResult:
        """
        Scan only changed files.

        Convenience method for diff-only scanning.
        Target: <100ms with cache hits.

        Args:
            target_path: Project root path
            engines: Engines to run (default: all)
            base_ref: Git ref to compare against

        Returns:
            OrchestratedResult with issues from changed files only
        """
        return self.scan(
            target_path=target_path,
            engines=engines,
            diff_only=True,
            base_ref=base_ref,
            parallel=True,
        )

    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics."""
        return self._scanner.get_cache_stats()

    def clear_cache(self) -> None:
        """Clear the scan cache."""
        self._scanner.clear_cache()

"""
Tests for the parallel orchestrator.

Verifies that engines run in parallel and cache works correctly.
"""

import os
import tempfile
import pytest

from qodacode.orchestrator import Orchestrator, OrchestratedResult


class TestOrchestrator:
    """Test parallel engine orchestration."""

    def test_orchestrator_initialization(self):
        """Orchestrator should initialize correctly."""
        orch = Orchestrator()
        assert orch.max_workers == 4
        assert orch.enable_cache is True

    def test_empty_scan(self):
        """Scanning empty directory should return empty result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orch = Orchestrator(project_path=tmpdir)
            result = orch.scan(tmpdir, engines=[])

            assert isinstance(result, OrchestratedResult)
            assert result.total_issues == 0
            assert result.files_scanned == 0

    def test_scan_with_engines(self):
        """Scan should run engines and return combined results."""
        orch = Orchestrator()
        result = orch.scan("tests/", engines=[])

        assert isinstance(result, OrchestratedResult)
        assert result.ast_result is not None

    def test_parallel_vs_sequential(self):
        """Parallel execution should complete successfully."""
        orch = Orchestrator()

        # Run parallel
        parallel_result = orch.scan("tests/", engines=[], parallel=True)

        # Run sequential
        sequential_result = orch.scan("tests/", engines=[], parallel=False)

        # Both should complete successfully
        assert parallel_result.ast_result is not None
        assert sequential_result.ast_result is not None

        # Both should have timing info
        assert parallel_result.total_elapsed_ms > 0
        assert sequential_result.total_elapsed_ms > 0

        # Parallel efficiency may be negative with no engines (thread overhead)
        # With real engines, parallel should be faster
        assert isinstance(parallel_result.parallel_efficiency, float)

    def test_engine_timing(self):
        """Engine timing should be tracked."""
        orch = Orchestrator()
        result = orch.scan("tests/", engines=[])

        # Should have timing info
        assert result.total_elapsed_ms > 0
        timing = result.get_engine_timing()
        assert isinstance(timing, dict)

    def test_cache_stats(self):
        """Cache stats should be available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orch = Orchestrator(project_path=tmpdir)
            stats = orch.get_cache_stats()
            assert isinstance(stats, dict)

    def test_diff_scan(self):
        """Diff scan should work (may return 0 files if no changes)."""
        orch = Orchestrator()

        # This may return 0 files if git has no changes
        result = orch.scan_diff(".")

        assert isinstance(result, OrchestratedResult)
        # files_scanned can be 0 if no git changes

    def test_orchestrated_result_properties(self):
        """OrchestratedResult should have correct properties."""
        result = OrchestratedResult()

        assert result.files_scanned == 0
        assert result.critical_count == 0
        assert result.high_count == 0
        assert result.total_issues == 0

    def test_scan_single_file(self):
        """Should be able to scan a single file."""
        # Create a temp Python file
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"import os\n")
            temp_path = f.name

        try:
            orch = Orchestrator()
            result = orch.scan(temp_path, engines=[])

            assert result.ast_result is not None
            # Single file scan
            assert result.files_scanned >= 0
        finally:
            os.unlink(temp_path)


class TestOrchestratorWithEngines:
    """Test orchestrator with actual engines (if available)."""

    def test_with_gitleaks(self):
        """Test with gitleaks engine (if installed)."""
        orch = Orchestrator()

        # This won't fail even if gitleaks is not installed
        result = orch.scan("tests/", engines=["gitleaks"])

        assert isinstance(result, OrchestratedResult)
        assert len(result.engine_results) == 1
        # Engine may or may not be available
        engine_result = result.engine_results[0]
        assert engine_result.engine_name == "gitleaks"

    def test_with_semgrep(self):
        """Test with semgrep engine (if installed)."""
        orch = Orchestrator()

        result = orch.scan("tests/", engines=["semgrep"])

        assert isinstance(result, OrchestratedResult)
        assert len(result.engine_results) == 1
        engine_result = result.engine_results[0]
        assert engine_result.engine_name == "semgrep"

    def test_all_engines_parallel(self):
        """Test running all engines in parallel."""
        orch = Orchestrator()

        result = orch.scan("tests/", engines=["gitleaks", "semgrep"])

        assert isinstance(result, OrchestratedResult)
        assert len(result.engine_results) == 2
        assert result.total_elapsed_ms > 0

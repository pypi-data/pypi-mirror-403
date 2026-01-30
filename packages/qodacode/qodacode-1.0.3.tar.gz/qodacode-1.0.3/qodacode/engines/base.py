"""
Engine Runner Abstract Base Class.

All external engines (Semgrep, Gitleaks, etc.) MUST inherit from this class.
This ensures consistent behavior across all engines and enables the orchestrator
to treat them uniformly.

Reference: docs/PRD_V2_ORCHESTRATOR.md Section 5.2
"""

import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from qodacode.models.issue import Issue, EngineSource


class EngineRunner(ABC):
    """
    Abstract base class for all external engine runners.

    Every engine runner must implement:
    - is_available(): Check if the binary is installed
    - run(): Execute the engine and return normalized Issues
    - get_install_instructions(): Tell users how to install

    Subclasses should also define:
    - name: Human-readable engine name
    - engine_source: EngineSource enum value for Issue tagging
    """

    # Subclasses must override these
    name: str = "Unknown Engine"
    engine_source: EngineSource = EngineSource.TREESITTER
    binary_name: str = ""  # e.g., "semgrep", "gitleaks"

    def __init__(self):
        """Initialize the engine runner."""
        self._available: Optional[bool] = None

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the engine binary is installed and accessible.

        Returns:
            True if the engine can be executed, False otherwise.

        Note:
            Implementations should cache the result for performance.
        """
        pass

    @abstractmethod
    def run(self, target_path: str) -> List[Issue]:
        """
        Execute the engine on the target path and return normalized Issues.

        Args:
            target_path: Path to scan (file or directory)

        Returns:
            List of Issue objects (Pydantic models) normalized from engine output.

        Raises:
            RuntimeError: If the engine is not available or execution fails.
            FileNotFoundError: If the target path does not exist.

        Note:
            - All Issues MUST have engine field set to self.engine_source
            - All Issues MUST be valid Pydantic models (validated on creation)
            - Implementations should handle subprocess errors gracefully
        """
        pass

    @abstractmethod
    def get_install_instructions(self) -> str:
        """
        Return human-readable installation instructions.

        Returns:
            String with installation command(s) for the user.

        Example:
            "Install with: pip install semgrep"
        """
        pass

    # ─────────────────────────────────────────────────────────────────
    # Utility methods for subclasses
    # ─────────────────────────────────────────────────────────────────

    def check_binary_in_path(self, binary: Optional[str] = None) -> bool:
        """
        Check if a binary exists in system PATH.

        Args:
            binary: Binary name to check. Defaults to self.binary_name.

        Returns:
            True if binary is found, False otherwise.
        """
        bin_name = binary or self.binary_name
        if not bin_name:
            return False
        return shutil.which(bin_name) is not None

    def validate_target(self, target_path: str) -> Path:
        """
        Validate that the target path exists.

        Args:
            target_path: Path to validate.

        Returns:
            Path object for the target.

        Raises:
            FileNotFoundError: If target does not exist.
        """
        path = Path(target_path)
        if not path.exists():
            raise FileNotFoundError(f"Target path does not exist: {target_path}")
        return path

    def run_subprocess(
        self,
        cmd: List[str],
        timeout: int = 300,
        check: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Execute a subprocess command with standard error handling.

        Args:
            cmd: Command and arguments as list.
            timeout: Maximum execution time in seconds.
            check: If True, raise on non-zero exit code.

        Returns:
            CompletedProcess with stdout, stderr, returncode.

        Raises:
            RuntimeError: On timeout or execution failure.
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 30,  # Buffer beyond internal timeout
                check=check,
                shell=False,  # Explicit: safe subprocess with list args
            )
            return result
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"{self.name} timed out after {timeout}s. "
                f"Try increasing timeout or scanning a smaller target."
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"{self.name} binary not found. {self.get_install_instructions()}"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"{self.name} failed with exit code {e.returncode}: {e.stderr}"
            )

    def __repr__(self) -> str:
        available = "available" if self.is_available() else "not available"
        return f"<{self.__class__.__name__} ({available})>"


class EngineError(Exception):
    """
    Exception raised when an engine fails.

    Attributes:
        engine: Name of the engine that failed.
        message: Error description.
        recoverable: Whether the orchestrator should continue with other engines.
    """

    def __init__(
        self,
        engine: str,
        message: str,
        recoverable: bool = True,
    ):
        self.engine = engine
        self.message = message
        self.recoverable = recoverable
        super().__init__(f"[{engine}] {message}")


class EngineNotAvailableError(EngineError):
    """Raised when an engine binary is not installed."""

    def __init__(self, engine: str, install_instructions: str):
        super().__init__(
            engine=engine,
            message=f"Not installed. {install_instructions}",
            recoverable=True,
        )
        self.install_instructions = install_instructions

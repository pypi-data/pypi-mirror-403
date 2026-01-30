"""
Engine installer with rich progress bars.

Provides beautiful UX for first-time engine downloads with progress tracking.
"""

import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)

from qodacode.utils.binaries import (
    ensure_gitleaks,
    get_gitleaks_path,
    GITLEAKS_VERSION,
)


console = Console()


def is_semgrep_available() -> bool:
    """Check if Semgrep is available."""
    return shutil.which("semgrep") is not None


def is_gitleaks_available() -> bool:
    """Check if Gitleaks is available."""
    return get_gitleaks_path() is not None


def get_missing_engines() -> list[str]:
    """
    Get list of missing engines.

    Returns:
        List of engine names that need to be installed
    """
    missing = []

    if not is_semgrep_available():
        missing.append("semgrep")

    if not is_gitleaks_available():
        missing.append("gitleaks")

    return missing


def install_engines_with_progress() -> bool:
    """
    Install missing engines with beautiful progress bars.

    Returns:
        True if all engines were installed successfully, False otherwise
    """
    missing = get_missing_engines()

    if not missing:
        console.print("[green]✓[/green] All engines already installed")
        return True

    console.print(f"\n[bold cyan]🚀 First run detected - Installing security engines...[/bold cyan]")
    console.print("[dim]This happens once and takes ~30 seconds[/dim]\n")

    success = True

    # Install Gitleaks if missing
    if "gitleaks" in missing:
        success = success and _install_gitleaks()

    # Install Semgrep if missing
    if "semgrep" in missing:
        success = success and _install_semgrep()

    if success:
        console.print(f"\n[bold green]✅ All engines installed successfully![/bold green]")
        console.print("[dim]Future scans will be instant[/dim]\n")
    else:
        console.print(f"\n[bold yellow]⚠️  Some engines failed to install[/bold yellow]")
        console.print("[dim]Continuing with available engines[/dim]\n")

    return success


def _install_gitleaks() -> bool:
    """Install Gitleaks with progress bar."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Downloading Gitleaks v{GITLEAKS_VERSION}...",
                total=100
            )

            def callback(downloaded: int, total: int):
                progress.update(task, completed=downloaded, total=total)

            ensure_gitleaks(auto_download=True, progress_callback=callback)

        console.print("[green]✓[/green] Gitleaks installed")
        return True

    except PermissionError as e:
        console.print(f"[red]✗[/red] Permission denied: Cannot write to ~/.qodacode/bin/")
        console.print(f"[dim]Run with appropriate permissions or install Gitleaks manually[/dim]")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Gitleaks installation failed: {e}")
        return False


def _install_semgrep() -> bool:
    """Install Semgrep with progress indication."""
    import subprocess

    try:
        console.print("[dim]Installing Semgrep via pip...[/dim]")

        # Run pip install with progress
        result = subprocess.run(
            ["pip", "install", "--quiet", "semgrep>=1.50"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            console.print("[green]✓[/green] Semgrep installed")
            return True
        else:
            console.print(f"[red]✗[/red] Semgrep installation failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        console.print("[red]✗[/red] Semgrep installation timed out")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Semgrep installation failed: {e}")
        return False


def check_and_install_if_needed() -> bool:
    """
    Check for missing engines and offer to install them.

    Returns:
        True if all engines are available (either already installed or freshly installed)
    """
    missing = get_missing_engines()

    if not missing:
        return True

    # Offer to install
    console.print(f"\n[yellow]⚠️  Missing security engines: {', '.join(missing)}[/yellow]")

    # In non-interactive mode or CI, skip installation
    import sys
    if not sys.stdin.isatty():
        console.print("[dim]Non-interactive mode - skipping installation[/dim]")
        return False

    from rich.prompt import Confirm
    if Confirm.ask("Install now? (takes ~30 seconds, one-time only)", default=True):
        return install_engines_with_progress()
    else:
        console.print("[dim]Continuing with available engines[/dim]")
        return False

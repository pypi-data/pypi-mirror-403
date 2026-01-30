"""
Binary management utilities for Qodacode.

Auto-downloads and manages external binaries like Gitleaks that are not
available via pip. Binaries are stored in ~/.qodacode/bin/ and automatically
added to PATH when needed.
"""

import os
import platform
import shutil
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import httpx


# Binary configurations
GITLEAKS_VERSION = "8.18.4"
GITLEAKS_REPO = "gitleaks/gitleaks"

# Directory for storing downloaded binaries
QODACODE_BIN_DIR = Path.home() / ".qodacode" / "bin"


def get_platform_info() -> Tuple[str, str]:
    """
    Get current platform and architecture for binary downloads.

    Returns:
        Tuple of (os_name, arch) matching GitHub release naming conventions.
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Map to GitHub release naming
    os_map = {
        "darwin": "darwin",
        "linux": "linux",
        "windows": "windows",
    }

    arch_map = {
        "x86_64": "x64",
        "amd64": "x64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }

    os_name = os_map.get(system, system)
    arch = arch_map.get(machine, machine)

    return os_name, arch


def get_gitleaks_download_url() -> str:
    """
    Get the download URL for the appropriate Gitleaks binary.

    Returns:
        URL to the Gitleaks release archive.
    """
    os_name, arch = get_platform_info()

    # Gitleaks release naming: gitleaks_{version}_{os}_{arch}.tar.gz
    # Windows uses .zip instead
    ext = "zip" if os_name == "windows" else "tar.gz"
    filename = f"gitleaks_{GITLEAKS_VERSION}_{os_name}_{arch}.{ext}"

    return f"https://github.com/{GITLEAKS_REPO}/releases/download/v{GITLEAKS_VERSION}/{filename}"


def ensure_bin_dir() -> Path:
    """
    Ensure the qodacode bin directory exists.

    Returns:
        Path to the bin directory.
    """
    QODACODE_BIN_DIR.mkdir(parents=True, exist_ok=True)
    return QODACODE_BIN_DIR


def get_gitleaks_path() -> Optional[Path]:
    """
    Get the path to the Gitleaks binary.

    Checks in order:
    1. System PATH
    2. Qodacode bin directory

    Returns:
        Path to the binary if found, None otherwise.
    """
    # Check system PATH first
    system_path = shutil.which("gitleaks")
    if system_path:
        return Path(system_path)

    # Check qodacode bin directory
    os_name, _ = get_platform_info()
    binary_name = "gitleaks.exe" if os_name == "windows" else "gitleaks"
    local_path = QODACODE_BIN_DIR / binary_name

    if local_path.exists() and local_path.is_file():
        return local_path

    return None


def download_gitleaks(progress_callback=None) -> Path:
    """
    Download and install Gitleaks binary.

    Args:
        progress_callback: Optional callback(downloaded, total) for progress updates.

    Returns:
        Path to the installed binary.

    Raises:
        RuntimeError: If download or extraction fails.
    """
    url = get_gitleaks_download_url()
    bin_dir = ensure_bin_dir()
    os_name, _ = get_platform_info()
    binary_name = "gitleaks.exe" if os_name == "windows" else "gitleaks"
    target_path = bin_dir / binary_name

    # Download to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".archive") as tmp:
        try:
            with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length", 0))
                downloaded = 0

                for chunk in response.iter_bytes():
                    tmp.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

            tmp_path = Path(tmp.name)

            # Extract based on file type
            if url.endswith(".zip"):
                with zipfile.ZipFile(tmp_path, "r") as zf:
                    # Find the binary in the archive
                    for name in zf.namelist():
                        if name.endswith(binary_name) or name == binary_name:
                            with zf.open(name) as src, open(target_path, "wb") as dst:
                                dst.write(src.read())
                            break
            else:
                with tarfile.open(tmp_path, "r:gz") as tf:
                    # Find the binary in the archive
                    for member in tf.getmembers():
                        if member.name.endswith(binary_name) or member.name == binary_name:
                            extracted = tf.extractfile(member)
                            if extracted:
                                with open(target_path, "wb") as dst:
                                    dst.write(extracted.read())
                            break

            # Make executable on Unix
            if os_name != "windows":
                target_path.chmod(target_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            return target_path

        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to download Gitleaks: {e}")
        except (tarfile.TarError, zipfile.BadZipFile) as e:
            raise RuntimeError(f"Failed to extract Gitleaks: {e}")
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp.name)
            except OSError:
                pass


def ensure_gitleaks(auto_download: bool = True, progress_callback=None) -> Optional[Path]:
    """
    Ensure Gitleaks is available, downloading if necessary.

    Args:
        auto_download: If True, automatically download if not found.
        progress_callback: Optional callback for download progress.

    Returns:
        Path to the binary, or None if not available and auto_download is False.
    """
    path = get_gitleaks_path()
    if path:
        return path

    if not auto_download:
        return None

    return download_gitleaks(progress_callback)


def get_binary_version(binary_path: Path, version_flag: str = "--version") -> Optional[str]:
    """
    Get the version of a binary.

    Args:
        binary_path: Path to the binary.
        version_flag: Flag to get version (default: --version).

    Returns:
        Version string or None if failed.
    """
    import subprocess

    try:
        result = subprocess.run(
            [str(binary_path), version_flag],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Parse version from output (usually first line or first word)
            output = result.stdout.strip() or result.stderr.strip()
            # Extract version number pattern
            import re
            match = re.search(r'\d+\.\d+\.\d+', output)
            if match:
                return match.group(0)
            return output.split()[0] if output else None
    except Exception:
        pass
    return None

"""
Qodacode Cache - Persistent caching system for scan results.

Stores scan results by file hash to avoid re-scanning unchanged files.
Target: <100ms for diff scans by leveraging cached results.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

from qodacode import __version__


# Cache configuration
CACHE_DIR = ".qodacode/cache"
CACHE_FILE = "scan_cache.json"
CACHE_VERSION = "1"  # Bump this to invalidate all caches
CACHE_MAX_AGE_DAYS = 7  # Expire cache entries older than this
CACHE_MAX_ENTRIES = 10000  # Maximum entries to keep


@dataclass
class CacheEntry:
    """A cached scan result for a single file."""
    file_hash: str
    issues: List[Dict[str, Any]]
    timestamp: float
    qodacode_version: str
    cache_version: str

    def is_valid(self) -> bool:
        """Check if this cache entry is still valid."""
        # Check cache version
        if self.cache_version != CACHE_VERSION:
            return False

        # Check Qodacode version (major.minor must match)
        current_parts = __version__.split(".")[:2]
        cached_parts = self.qodacode_version.split(".")[:2]
        if current_parts != cached_parts:
            return False

        # Check age
        age_days = (time.time() - self.timestamp) / (24 * 3600)
        if age_days > CACHE_MAX_AGE_DAYS:
            return False

        return True


class ScanCache:
    """
    Persistent cache for scan results.

    Uses SHA256 hashes of file contents to cache and retrieve
    scan results without re-scanning unchanged files.

    Cache location: .qodacode/cache/scan_cache.json
    """

    def __init__(self, project_path: str = "."):
        """
        Initialize the cache.

        Args:
            project_path: Root path of the project (where .qodacode is)
        """
        self.project_path = Path(project_path).resolve()
        self.cache_dir = self.project_path / CACHE_DIR
        self.cache_file = self.cache_dir / CACHE_FILE
        self._cache: Dict[str, CacheEntry] = {}
        self._dirty = False
        self._load()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Add .gitignore to cache dir
        gitignore = self.cache_dir / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("# Cache files - do not commit\n*\n")

    def _load(self) -> None:
        """Load cache from disk."""
        if not self.cache_file.exists():
            self._cache = {}
            return

        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)

            # Convert to CacheEntry objects
            for file_hash, entry_data in data.items():
                try:
                    entry = CacheEntry(
                        file_hash=entry_data["file_hash"],
                        issues=entry_data["issues"],
                        timestamp=entry_data["timestamp"],
                        qodacode_version=entry_data.get("qodacode_version", "0.0.0"),
                        cache_version=entry_data.get("cache_version", "0"),
                    )
                    # Only load valid entries
                    if entry.is_valid():
                        self._cache[file_hash] = entry
                except (KeyError, TypeError):
                    continue  # Skip corrupted entries

        except (json.JSONDecodeError, IOError, OSError):
            self._cache = {}

    def _save(self) -> None:
        """Save cache to disk."""
        if not self._dirty:
            return

        self._ensure_cache_dir()

        # Prune old entries if cache is too large
        if len(self._cache) > CACHE_MAX_ENTRIES:
            self._prune()

        # Convert to serializable format
        data = {}
        for file_hash, entry in self._cache.items():
            data[file_hash] = asdict(entry)

        try:
            # Write atomically using temp file
            temp_file = self.cache_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.cache_file)
            self._dirty = False
        except (IOError, OSError):
            pass  # Cache save failure is not critical

    def _prune(self) -> None:
        """Remove oldest entries when cache is too large."""
        if len(self._cache) <= CACHE_MAX_ENTRIES:
            return

        # Sort by timestamp and keep newest
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].timestamp,
            reverse=True,
        )

        self._cache = dict(sorted_entries[:CACHE_MAX_ENTRIES])
        self._dirty = True

    @staticmethod
    def get_file_hash(filepath: str) -> str:
        """
        Compute SHA256 hash of a file.

        Args:
            filepath: Path to the file

        Returns:
            Hex string of SHA256 hash
        """
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (IOError, OSError):
            return ""

    def get(self, file_hash: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached issues for a file hash.

        Args:
            file_hash: SHA256 hash of file contents

        Returns:
            List of cached issues, or None if not in cache
        """
        entry = self._cache.get(file_hash)
        if entry and entry.is_valid():
            return entry.issues
        return None

    def get_for_file(self, filepath: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached issues for a file.

        Args:
            filepath: Path to the file

        Returns:
            List of cached issues, or None if not in cache or file changed
        """
        file_hash = self.get_file_hash(filepath)
        if not file_hash:
            return None
        return self.get(file_hash)

    def set(self, file_hash: str, issues: List[Dict[str, Any]]) -> None:
        """
        Cache issues for a file hash.

        Args:
            file_hash: SHA256 hash of file contents
            issues: List of issues (as dicts) found in the file
        """
        self._cache[file_hash] = CacheEntry(
            file_hash=file_hash,
            issues=issues,
            timestamp=time.time(),
            qodacode_version=__version__,
            cache_version=CACHE_VERSION,
        )
        self._dirty = True

    def set_for_file(self, filepath: str, issues: List[Dict[str, Any]]) -> None:
        """
        Cache issues for a file.

        Args:
            filepath: Path to the file
            issues: List of issues (as dicts) found in the file
        """
        file_hash = self.get_file_hash(filepath)
        if file_hash:
            self.set(file_hash, issues)

    def invalidate(self, file_hash: str) -> None:
        """Remove a cache entry."""
        if file_hash in self._cache:
            del self._cache[file_hash]
            self._dirty = True

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache = {}
        self._dirty = True
        self._save()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        valid_count = sum(1 for e in self._cache.values() if e.is_valid())
        total_issues = sum(len(e.issues) for e in self._cache.values())

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_count,
            "total_cached_issues": total_issues,
            "cache_file": str(self.cache_file),
            "cache_version": CACHE_VERSION,
            "qodacode_version": __version__,
        }

    def __enter__(self) -> "ScanCache":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - save cache."""
        self._save()

    def save(self) -> None:
        """Explicitly save the cache."""
        self._save()

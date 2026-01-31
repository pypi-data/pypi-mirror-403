"""File system utilities and cache management.

Provides optimized file reading, exclusion pattern handling, and
project structure generation (tree view) with LRU caching.
"""

import os
import pathlib
import mmap
import subprocess
import logging
import hashlib
import json
from typing import List, Dict, Any, NamedTuple
from collections import OrderedDict
from .ignore_filter import IgnoreFilter

logger = logging.getLogger(__name__)


class ProjectScanResult(NamedTuple):
    """Encapsulates the results of a project-wide filesystem scan."""

    python_files: List[pathlib.Path]
    test_files_count: int
    file_types: Dict[str, int]
    size_stats: Dict[str, Any]


class LRUCache:
    """Least Recently Used (LRU) cache using OrderedDict for O(1) performance."""

    def __init__(self, maxsize: int = 256):
        """Initialize the LRU cache.

        Args:
            maxsize: Maximum number of items in the cache.
        """
        self.cache = OrderedDict()
        self.maxsize = maxsize

    def get(self, key: str) -> Any:
        """Retrieves an item from the cache and moves it to the end (MRU).

        Args:
            key: The cache key.

        Returns:
            The cached value or None if not present.
        """
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any):
        """Adds or updates an item in the cache.

        Args:
            key: The cache key.
            value: The value to store.
        """
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)

    def clear(self):
        """Clears the cache."""
        self.cache.clear()


# Global cache instance
file_cache = LRUCache()


class ProjectScanner:
    """Consolidated project scanner that performs a single-pass traversal."""

    COMMON_EXTS = {
        ".py",
        ".txt",
        ".md",
        ".json",
        ".yml",
        ".yaml",
        ".html",
        ".css",
        ".js",
        ".xml",
        ".csv",
        ".sql",
    }

    def __init__(self, project_path: pathlib.Path, ignore_filter: IgnoreFilter):
        """Initialize the scanner.

        Args:
            project_path: Path to the project root.
            ignore_filter: Filter for ignoring files and directories.
        """
        self.project_path = project_path
        self.ignore_filter = ignore_filter
        self.stats = {
            "total_files": 0,
            "total_size": 0,
            "python_files": 0,
            "python_size": 0,
        }
        self.file_types = {}
        self.python_files = []
        self.test_files_count = 0

    def scan(self) -> ProjectScanResult:
        """Runs the single-pass scan across the project directory."""
        for root, dirs, files in os.walk(self.project_path):
            rel_root = os.path.relpath(root, self.project_path)
            if rel_root == ".":
                rel_root = ""

            # Prune directories in-place
            i = 0
            while i < len(dirs):
                d_path = pathlib.Path(root) / dirs[i]
                if self.ignore_filter.is_ignored(d_path):
                    del dirs[i]
                else:
                    i += 1

            for file in files:
                self._process_file(root, rel_root, file)

        return ProjectScanResult(
            python_files=sorted(self.python_files),
            test_files_count=self.test_files_count,
            file_types=dict(
                sorted(self.file_types.items(), key=lambda x: x[1], reverse=True)[:20]
            ),
            size_stats=self._finalize_stats(),
        )

    def _process_file(self, root: str, rel_root: str, file: str):
        """Internal helper to process a single file during scan.

        Args:
            root: Root path.
            rel_root: Relative root path.
            file: Filename.
        """
        file_path = os.path.join(root, file)
        path_obj = pathlib.Path(file_path)

        if self.ignore_filter.is_ignored(path_obj):
            return

        size = 0
        try:
            size = os.path.getsize(file_path)
        except OSError:
            pass

        # 1. Basic Stats
        self.stats["total_files"] += 1
        self.stats["total_size"] += size

        # 2. Extension Counting
        ext = os.path.splitext(file)[1].lower()
        if ext in self.COMMON_EXTS or ext:
            self.file_types[ext] = self.file_types.get(ext, 0) + 1

        # 3. Python Specifics
        if ext == ".py":
            self.stats["python_files"] += 1
            self.stats["python_size"] += size
            if is_test_file(path_obj):
                self.test_files_count += 1
            else:
                self.python_files.append(path_obj)

    def _finalize_stats(self) -> Dict[str, Any]:
        """Aggregates raw scan data into final project statistics.

        Returns:
            Dictionary with formatted statistics (sizes, percentages).
        """
        ts = self.stats["total_size"]
        ps = self.stats["python_size"]
        tf = self.stats["total_files"]

        return {
            "total_files": tf,
            "total_size_mb": round(ts / (1024 * 1024), 2),
            "python_files": self.stats["python_files"],
            "python_size_mb": round(ps / (1024 * 1024), 2),
            "avg_file_size_kb": round(ts / tf / 1024, 2) if tf > 0 else 0,
            "python_percentage": round(ps / ts * 100, 2) if ts > 0 else 0,
        }


def read_file_fast(path: pathlib.Path) -> str:
    """Reads file content efficiently using memory mapping and caching."""
    cache_key = str(path)
    cached = file_cache.get(cache_key)
    if cached:
        return cached

    try:
        if not path.exists():
            return ""

        with open(path, "rb") as f:
            file_size = path.stat().st_size
            if file_size > 1024 * 1024:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    content = mm.read().decode("utf-8-sig", errors="replace")
            else:
                content = f.read().decode("utf-8-sig", errors="replace")

            file_cache.set(cache_key, content)
            return content
    except Exception as e:
        logger.warning(f"Error reading {path}: {e}")
        return ""


def is_test_file(path: pathlib.Path) -> bool:
    """Heuristically determines if a given file is a test file.

    Args:
        path: Path to the file.

    Returns:
        True if the file is likely a test file.
    """
    filename = path.name.lower()
    test_patterns = ["test_", "_test", "spec_", "_spec", "conftest"]
    return (
        any(pattern in filename for pattern in test_patterns)
        or "tests" in str(path).lower()
        or "test" in path.parent.name.lower()
    )


def generate_tree_optimized(project_path: pathlib.Path) -> str:
    """Generates a text-based directory structure visualization."""
    try:
        result = subprocess.run(
            [
                "tree",
                "-I",
                "__pycache__|*.pyc|*.pyo|*.pycache|.git|.venv|venv|env",
                "-a",
                "--noreport",
                "-L",
                "4",
            ],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout[:1500]
    except Exception:
        pass
    return _generate_tree_fallback(project_path)


def _generate_tree_fallback(project_path: pathlib.Path) -> str:
    """Fallback directory structure generator."""
    tree_lines = ["./"]
    for root, dirs, files in os.walk(project_path):
        depth = root[len(str(project_path)) :].count(os.sep)
        if depth > 4:
            continue
        dirs[:] = [d for d in dirs if not d.startswith((".", "_"))]
        indent = "    " * depth
        rel_root = os.path.relpath(root, project_path)
        if rel_root != ".":
            tree_lines.append(f"{indent}{os.path.basename(root)}/")

        f_indent = "    " * (depth + 1)
        sorted_files = sorted(files)
        for i, file in enumerate(sorted_files[:8]):
            if i == 7 and len(files) > 8:
                tree_lines.append(f"{f_indent}... (+{len(files) - 8} more)")
                break
            tree_lines.append(f"{f_indent}{file}")
    return "\n".join(tree_lines)


def calculate_file_hash(path: pathlib.Path) -> str:
    """Calculates the SHA-256 hash of a file's content.

    Args:
        path: Path to the file.

    Returns:
        HEX string of the SHA-256 hash.
    """
    try:
        content = read_file_fast(path)
        if not content:
            return ""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    except Exception:
        return ""


def parse_qgis_metadata(project_path: pathlib.Path) -> Dict[str, Any]:
    """Parses and validates a QGIS plugin metadata.txt file.

    Args:
        project_path: Path to the project root.

    Returns:
        Dictionary with parsed metadata, issues, and compliance score.
    """
    metadata_file = project_path / "metadata.txt"
    res = {
        "exists": False,
        "valid": False,
        "content": {},
        "issues": [],
        "compliance_score": 0,
    }

    if not metadata_file.exists():
        res["issues"].append("Missing metadata.txt")
        return res

    res["exists"] = True
    try:
        content = metadata_file.read_text(encoding="utf-8")
        import configparser

        config = configparser.ConfigParser(strict=False)
        # Strip to avoid issues with empty lines at start or BOM
        config.read_string("[general]\n" + content.strip())

        # QGIS metadata usually has a [general] section, but some people omit the header
        # adding a dummy header to ensure it parses if it's just key=value
        if "general" in config:
            metadata = dict(config["general"])
        else:
            metadata = {}

        res["content"] = metadata

        # Mandatory fields for QGIS.org
        mandatory = [
            "name",
            "description",
            "version",
            "qgisminimumversion",
            "author",
            "email",
        ]
        for field in mandatory:
            if field not in metadata:
                res["issues"].append(f"Missing mandatory field: {field}")

        # Recommended fields
        recommended = ["repository", "tracker", "homepage", "category", "tags"]
        for field in recommended:
            if field not in metadata:
                res["issues"].append(f"Missing recommended field: {field}")

        if not res["issues"]:
            res["valid"] = True
            res["compliance_score"] = 100
        else:
            # Simple scoring: 100 - (10 per issue, max 100)
            res["compliance_score"] = max(0, 100 - (len(res["issues"]) * 10))

    except Exception as e:
        res["issues"].append(f"Error parsing metadata.txt: {str(e)}")

    return res


def load_cache(project_path: pathlib.Path) -> Dict[str, Any]:
    """Loads the analysis cache from disk.

    Args:
        project_path: Path to the project root.

    Returns:
        Cached analysis data or empty dict.
    """
    cache_file = project_path / ".ai_context_cache.json"
    if not cache_file.exists():
        return {}
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(project_path: pathlib.Path, cache_data: Dict[str, Any]):
    """Saves the analysis cache to disk.

    Args:
        project_path: Path to the project root.
        cache_data: The analysis data to serialize.
    """
    cache_file = project_path / ".ai_context_cache.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# --- Legacy Compatibility Wrappers ---


def load_exclusion_patterns(
    project_path: pathlib.Path, extra: List[str] = None
) -> List[str]:
    """Loads exclusion patterns using IgnoreFilter.

    Args:
        project_path: Path to the project root.
        extra: Additional patterns to include.

    Returns:
        List of compiled or raw exclusion patterns.
    """
    return IgnoreFilter(project_path, extra).patterns


def scan_project(project_path: pathlib.Path, patterns: List[str]) -> ProjectScanResult:
    """Scans the project for files and statistics.

    Args:
        project_path: Path to the project root.
        patterns: Exclusion patterns.

    Returns:
        Combined scan results.
    """
    filt = IgnoreFilter(project_path, extra_patterns=patterns)
    scanner = ProjectScanner(project_path, filt)
    return scanner.scan()


def count_file_types(project_path: pathlib.Path) -> Dict[str, int]:
    """Counts files by extension in the project.

    Args:
        project_path: Path to the project root.

    Returns:
        Dictionary of extension counts.
    """
    return scan_project(project_path, []).file_types


def calculate_size_stats(project_path: pathlib.Path) -> Dict[str, Any]:
    """Calculates project size statistics.

    Args:
        project_path: Path to the project root.

    Returns:
        Statistics about file sizes and counts.
    """
    return scan_project(project_path, []).size_stats


def analyze_structure(project_path: pathlib.Path, modules_count: int) -> Dict[str, Any]:
    """Analyzes and returns the project structure and statistics.

    Args:
        project_path: Path to the project root.
        modules_count: Number of modules discovered.

    Returns:
        Consolidated structure analysis.
    """
    filt = IgnoreFilter(project_path)
    scanner = ProjectScanner(project_path, filt)
    res = scanner.scan()
    return {
        "tree": generate_tree_optimized(project_path),
        "modules_count": modules_count,
        "file_types": res.file_types,
        "size_stats": res.size_stats,
    }

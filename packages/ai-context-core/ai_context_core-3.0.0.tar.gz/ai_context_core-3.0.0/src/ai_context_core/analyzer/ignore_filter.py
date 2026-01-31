"""Logic for filtering and ignoring files based on patterns during project scan."""

import pathlib

import fnmatch
import re
from typing import List, Optional


class IgnoreFilter:
    """Handles logic for filtering files and directories based on exclusion patterns."""

    def __init__(
        self, project_path: pathlib.Path, extra_patterns: Optional[List[str]] = None
    ):
        """Initialize the filter.

        Args:
            project_path: Path to the project root.
            extra_patterns: Optional list of additional patterns to ignore.
        """
        self.project_path = project_path
        self.patterns = self._load_patterns(extra_patterns)
        self.regex = self._compile_patterns(self.patterns)

    def _compile_patterns(self, patterns: List[str]) -> Optional[re.Pattern]:
        """Compiles glob patterns into a single efficient Regex."""
        if not patterns:
            return None
        regex_parts = []
        for p in patterns:
            # Convert glob to regex: escape dots, replace * with .*, etc.
            part = fnmatch.translate(p.rstrip("/"))
            regex_parts.append(part)
        return re.compile("|".join(regex_parts))

    def _load_patterns(self, extra_patterns: Optional[List[str]]) -> List[str]:
        """Loads ignore patterns from .analyzerignore or returns defaults.

        Args:
            extra_patterns: Patterns provided via CLI or config.

        Returns:
            A list of glob patterns.
        """
        patterns = []
        ignore_file = self.project_path / ".analyzerignore"
        if ignore_file.exists():
            try:
                with open(ignore_file, encoding="utf-8") as f:
                    patterns = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]
            except Exception:
                pass

        if not patterns:
            patterns = [
                "__pycache__",
                ".git",
                ".venv",
                "venv",
                "env",
                ".tox",
                ".pytest_cache",
                ".mypy_cache",
                ".coverage",
                "build",
                "dist",
                "*.egg-info",
            ]

        if extra_patterns:
            patterns.extend(extra_patterns)
        return patterns

    def is_ignored(self, path: pathlib.Path) -> bool:
        """Checks if a path should be ignored using optimized regex."""
        if not self.regex:
            return False
        try:
            rel_path = str(path.relative_to(self.project_path))
        except ValueError:
            rel_path = str(path)

        # Match against relative path or just the filename
        return bool(self.regex.match(rel_path) or self.regex.match(path.name))

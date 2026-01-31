"""Git analysis utilities for project evolution tracking.

This module provides tools to analyze git history, identify hotspots,
and calculate code churn.
"""

import subprocess
import pathlib
from typing import List, Dict, Any, Optional
from collections import Counter


class GitRunner:
    """Handles execution of git commands."""

    def __init__(self, project_path: pathlib.Path):
        """Initialize the git runner.

        Args:
            project_path: Path to the project root.
        """
        self.path = project_path

    def run(self, args: List[str], check: bool = True) -> Optional[str]:
        """Runs a git command and returns its output.

        Args:
            args: List of git arguments (without 'git').
            check: Whether to raise an error on non-zero return code.

        Returns:
            The standard output as a string, or None if the command failed.
        """
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=self.path,
                capture_output=True,
                text=True,
                check=check,
            )
            return res.stdout
        except Exception:
            return None


class GitParser:
    """Parses git command outputs into structured data."""

    @staticmethod
    def parse_hotspots(log_output: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Parses git log output into a list of hotspots.

        Args:
            log_output: The output from git log command.
            limit: Maximum number of hotspots to return.

        Returns:
            List of dictionaries with 'path' and 'commits' keys.
        """
        if not log_output:
            return []
        files = [f for f in log_output.splitlines() if f.strip() and f.endswith(".py")]
        return [{"path": p, "commits": c} for p, c in Counter(files).most_common(limit)]

    @staticmethod
    def parse_churn(shortstat_output: str, days: int) -> Dict[str, Any]:
        """Parses git shortstat output into churn metrics.

        Args:
            shortstat_output: The output from git log --shortstat.
            days: The time period analyze in days.

        Returns:
            Dictionary with churn metrics (added, deleted, total_churn, etc.).
        """
        if not shortstat_output:
            return {"available": False}

        added, deleted, files = 0, 0, 0
        for line in shortstat_output.splitlines():
            if "file" in line and ("insertion" in line or "deletion" in line):
                parts = line.strip().split(",")
                files += int(parts[0].split()[0])
                for p in parts[1:]:
                    if "insertion" in p:
                        added += int(p.split()[0])
                    elif "deletion" in p:
                        deleted += int(p.split()[0])
        return {
            "available": True,
            "period_days": days,
            "added": added,
            "deleted": deleted,
            "total_churn": added + deleted,
            "files_changed": files,
        }


class GitAnalyzer:
    """Encapsulates git-based project analysis logic."""

    def __init__(self, project_path: pathlib.Path):
        """Initialize the git analyzer.

        Args:
            project_path: Path to the project root.
        """
        self.runner = GitRunner(project_path)
        self.parser = GitParser()
        self.path = project_path

    def is_repo(self) -> bool:
        """Checks if the path is inside a git repository.

        Returns:
            True if it's a valid git repository, False otherwise.
        """
        out = self.runner.run(["rev-parse", "--is-inside-work-tree"], check=True)
        return out is not None

    def get_hotspots(
        self, limit: int = 5, max_commits: int = 1000
    ) -> List[Dict[str, Any]]:
        """Identifies most frequently changed files.

        Args:
            limit: Maximum number of hotspots to return.
            max_commits: Search depth in git history.

        Returns:
            List of hotspots.
        """
        if not self.is_repo():
            return []
        log = self.runner.run(["log", f"-n{max_commits}", "--format=", "--name-only"])
        return self.parser.parse_hotspots(log, limit)

    def get_churn(self, days: int = 30) -> Dict[str, Any]:
        """Calculates code churn over the last N days.

        Args:
            days: Time period for calculation.

        Returns:
            Churn metrics dictionary.
        """
        if not self.is_repo():
            return {"available": False}
        since = f"--since='{days} days ago'"
        log = self.runner.run(["log", "--shortstat", "--no-merges", since, "--format="])
        return self.parser.parse_churn(log, days)


def is_git_repo(path: pathlib.Path) -> bool:
    """Legacy wrapper for is_repo."""
    return GitAnalyzer(path).is_repo()


def get_git_hotspots(
    project_path: pathlib.Path, limit: int = 5, max_commits: int = 1000
) -> List[Dict[str, Any]]:
    """Legacy wrapper for get_hotspots."""
    return GitAnalyzer(project_path).get_hotspots(limit, max_commits)


def get_git_churn(project_path: pathlib.Path, days: int = 30) -> Dict[str, Any]:
    """Legacy wrapper for get_churn."""
    return GitAnalyzer(project_path).get_churn(days)


def analyze_git_evolution(project_path: pathlib.Path) -> Dict[str, Any]:
    """Performs a full evolution analysis using git history."""
    analyzer = GitAnalyzer(project_path)
    return {
        "hotspots": analyzer.get_hotspots(),
        "churn": analyzer.get_churn(),
        "is_repo": analyzer.is_repo(),
    }

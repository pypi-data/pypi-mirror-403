"""Git analysis utilities for project evolution tracking."""

import subprocess
import pathlib
from typing import List, Dict, Any
from collections import Counter


class GitAnalyzer:
    """Encapsulates git-based project analysis logic."""

    def __init__(self, project_path: pathlib.Path):
        self.path = project_path

    def is_repo(self) -> bool:
        try:
            return (
                subprocess.run(
                    ["git", "rev-parse", "--is-inside-work-tree"],
                    cwd=self.path,
                    capture_output=True,
                    text=True,
                    check=False,
                ).returncode
                == 0
            )
        except Exception:
            return False

    def get_hotspots(
        self, limit: int = 5, max_commits: int = 1000
    ) -> List[Dict[str, Any]]:
        if not self.is_repo():
            return []
        try:
            cmd = ["git", "log", f"-n{max_commits}", "--format=", "--name-only"]
            res = subprocess.run(
                cmd, cwd=self.path, capture_output=True, text=True, check=True
            )
            files = [
                f for f in res.stdout.splitlines() if f.strip() and f.endswith(".py")
            ]
            return [
                {"path": p, "commits": c} for p, c in Counter(files).most_common(limit)
            ]
        except Exception:
            return []

    def get_churn(self, days: int = 30) -> Dict[str, Any]:
        if not self.is_repo():
            return {"available": False}
        try:
            since = f"--since='{days} days ago'"
            res = subprocess.run(
                ["git", "log", "--shortstat", "--no-merges", since, "--format="],
                cwd=self.path,
                capture_output=True,
                text=True,
                check=True,
            )
            added, deleted, files = 0, 0, 0
            for line in res.stdout.splitlines():
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
        except Exception:
            return {"available": False}


def is_git_repo(path: pathlib.Path) -> bool:
    return GitAnalyzer(path).is_repo()


def get_git_hotspots(
    project_path: pathlib.Path, limit: int = 5, max_commits: int = 1000
) -> List[Dict[str, Any]]:
    return GitAnalyzer(project_path).get_hotspots(limit, max_commits)


def get_git_churn(project_path: pathlib.Path, days: int = 30) -> Dict[str, Any]:
    return GitAnalyzer(project_path).get_churn(days)

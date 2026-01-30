import unittest
import pathlib
from ai_context_core.analyzer.git_analysis import (
    is_git_repo,
    get_git_hotspots,
    get_git_churn,
)


class TestGitAnalysis(unittest.TestCase):
    def setUp(self):
        self.project_path = pathlib.Path(__file__).parent.parent.resolve()

    def test_is_git_repo(self):
        # We check both cases to be robust
        if (self.project_path / ".git").exists():
            self.assertTrue(is_git_repo(self.project_path))
        else:
            self.assertFalse(is_git_repo(self.project_path))
        # A random temp directory should not be a git repo
        self.assertFalse(is_git_repo(pathlib.Path("/tmp")))

    def test_get_git_hotspots(self):
        hotspots = get_git_hotspots(self.project_path, limit=3)
        # Should return a list
        self.assertIsInstance(hotspots, list)
        if hotspots:
            self.assertIn("path", hotspots[0])
            self.assertIn("commits", hotspots[0])
            self.assertLessEqual(len(hotspots), 3)

    def test_get_git_churn(self):
        churn = get_git_churn(self.project_path, days=7)
        self.assertIsInstance(churn, dict)
        if churn.get("available"):
            self.assertIn("total_churn", churn)
            self.assertIn("files_changed", churn)


if __name__ == "__main__":
    unittest.main()

import unittest
from ai_context_core.analyzer import issues
import tempfile
import shutil
from pathlib import Path


class TestIssues(unittest.TestCase):
    def test_find_technical_debt(self):
        # Mock module data
        modules_data = [
            {
                "path": "complex_module.py",
                "complexity": 25,
                "lines": 100,
                "docstrings": {"module": True, "classes": {}, "functions": {}},
            }
        ]
        debt = issues.find_technical_debt(modules_data)
        self.assertTrue(any(d["module"] == "complex_module.py" for d in debt))
        # Check specific issue type
        item = next(d for d in debt if d["module"] == "complex_module.py")
        self.assertTrue(any(i["type"] == "high_complexity" for i in item["issues"]))

    def test_find_security_issues_secrets(self):
        # Create a temp file with a secret
        tmp_dir = tempfile.mkdtemp()
        try:
            p = Path(tmp_dir)
            vuln_file = p / "secrets.py"
            with open(vuln_file, "w") as f:
                f.write('api_key = "AKIA1234567890ABCDEF"')

            modules_data = [{"path": "secrets.py"}]
            # Pass absolute path as project root for test
            security_issues = issues.find_secrets(modules_data, str(p))

            self.assertEqual(len(security_issues), 1)
            self.assertEqual(security_issues[0]["module"], "secrets.py")
            # Verify we found the AWS key via the integrated check
            self.assertTrue(
                any(
                    "AWS Access Key" in i["pattern"]
                    for i in security_issues[0]["issues"]
                )
            )

        finally:
            shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    unittest.main()

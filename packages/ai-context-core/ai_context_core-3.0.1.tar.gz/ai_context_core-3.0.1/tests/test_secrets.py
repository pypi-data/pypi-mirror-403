import unittest
from ai_context_core.analyzer.secrets import detect_secrets, _mask_secret


class TestSecrets(unittest.TestCase):
    def test_mask_secret(self):
        self.assertEqual(_mask_secret("abcdef"), "ab**ef")
        self.assertEqual(_mask_secret("12345678"), "12****78")
        self.assertEqual(_mask_secret("short"), "sh*rt")  # 5 chars
        self.assertEqual(_mask_secret("abcd"), "****")  # 4 chars behaves as <=4

    def test_detect_aws_access_key(self):
        content = 'aws_access_key_id = "AKIA1234567890ABCDEF"'
        issues = detect_secrets(content)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["pattern"], "AWS Access Key ID")
        self.assertEqual(issues[0]["line"], 1)

    def test_detect_generic_password(self):
        content = 'password = "my_super_secret_password"'
        issues = detect_secrets(content)
        self.assertEqual(len(issues), 1)
        self.assertIn("Generic Potential Secret", issues[0]["pattern"])

    def test_no_secrets(self):
        content = 'print("Hello World")'
        issues = detect_secrets(content)
        self.assertEqual(len(issues), 0)

    def test_ignore_self_references(self):
        # Should ignore patterns that look like regex definitions
        content = 'regex = re.compile(r"AKIA[0-9A-Z]{16}")'
        issues = detect_secrets(content)
        self.assertEqual(len(issues), 0)

    def test_ignore_placeholders(self):
        # Should ignore common placeholders
        content = 'password = "change_me_please"'
        issues = detect_secrets(content)
        self.assertEqual(len(issues), 0)

    def test_ignore_examples(self):
        content = 'api_key = "example_key_12345"'
        issues = detect_secrets(content)
        self.assertEqual(len(issues), 0)


if __name__ == "__main__":
    unittest.main()

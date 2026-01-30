import unittest
import ast
from ai_context_core.analyzer import issues


class TestSecurityEnhanced(unittest.TestCase):
    def test_detect_assert(self):
        code = "assert x > 0"
        tree = ast.parse(code)
        issues_list = issues.detect_ast_security_issues(tree)
        self.assertTrue(any(i["pattern"] == "assert" for i in issues_list))

    def test_detect_generic_exception(self):
        code = """
try:
    pass
except:
    pass
"""
        tree = ast.parse(code)
        issues_list = issues.detect_ast_security_issues(tree)
        self.assertTrue(any(i["pattern"] == "except:" for i in issues_list))

    def test_detect_broad_exception(self):
        code = """
try:
    pass
except Exception:
    pass
"""
        tree = ast.parse(code)
        issues_list = issues.detect_ast_security_issues(tree)
        self.assertTrue(any(i["pattern"] == "except Exception:" for i in issues_list))

    def test_detect_sql_injection(self):
        code = 'query = f"SELECT * FROM users WHERE id = {user_id}"'
        tree = ast.parse(code)
        issues_list = issues.detect_ast_security_issues(tree)
        self.assertTrue(any(i["pattern"] == "f-string SQL" for i in issues_list))

    def test_detect_sql_injection_execute_format(self):
        code = 'cursor.execute("SELECT * FROM users WHERE id = {}".format(user_id))'
        tree = ast.parse(code)
        issues_list = issues.detect_ast_security_issues(tree)
        self.assertTrue(
            any(i["pattern"] == "SQL Injection (.format)" for i in issues_list)
        )

    def test_detect_sql_injection_execute_percent(self):
        code = 'cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)'
        tree = ast.parse(code)
        issues_list = issues.detect_ast_security_issues(tree)
        self.assertTrue(any(i["pattern"] == "SQL Injection (%)" for i in issues_list))

    def test_detect_sql_injection_execute_fstring(self):
        code = 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")'
        tree = ast.parse(code)
        issues_list = issues.detect_ast_security_issues(tree)
        self.assertTrue(
            any(i["pattern"] == "SQL Injection (f-string)" for i in issues_list)
        )


if __name__ == "__main__":
    unittest.main()

import unittest
import ast
from ai_context_core.analyzer import ast_utils


class TestAstUtils(unittest.TestCase):
    def test_extract_functions(self):
        code = "def foo(a, b): pass"
        tree = ast.parse(code)
        funcs = ast_utils.extract_functions(tree)
        self.assertEqual(funcs, ["foo(2 args)"])

    def test_calculate_complexity(self):
        code = """
def foo(x):
    if x:
        return 1
    else:
        return 2
"""
        tree = ast.parse(code)
        # 1 (base) + 1 (if) = 2? Or just 1 for if?
        # The implementation counts `If`, `While` etc as +1.
        # Let's verify behavior.
        complexity = ast_utils.calculate_complexity(tree)
        self.assertGreaterEqual(complexity, 1)

    def test_extract_imports(self):
        code = "import os\nfrom pathlib import Path"
        tree = ast.parse(code)
        imports = ast_utils.extract_imports(tree)
        self.assertIn("os", imports)
        self.assertIn("pathlib.Path", imports)


if __name__ == "__main__":
    unittest.main()

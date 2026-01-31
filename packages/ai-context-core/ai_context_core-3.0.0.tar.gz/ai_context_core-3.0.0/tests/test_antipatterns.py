import unittest
import ast
from ai_context_core.analyzer import antipatterns


class TestAntipatterns(unittest.TestCase):
    def test_detect_god_object(self):
        # Create a class with 21 methods
        methods = "\n".join([f"    def m{i}(self): pass" for i in range(21)])
        code = f"""
class GodObject:
{methods}
"""
        tree = ast.parse(code)
        issues = antipatterns.detect_god_object(tree, threshold_methods=20)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "god_object")
        self.assertEqual(issues[0]["value"], 21)

    def test_detect_spaghetti_code(self):
        # Create a function with high complexity
        # if x: ... else: ... (Repeated 26 times)
        nested_ifs = "\n".join(["    if x: pass" for _ in range(26)])
        code = f"""
def spaghetti(x):
{nested_ifs}
"""
        tree = ast.parse(code)
        issues = antipatterns.detect_spaghetti_code(tree, complexity_threshold=25)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "spaghetti_code")
        self.assertGreater(issues[0]["value"], 25)

    def test_detect_magic_numbers(self):
        code = """
def calc(x):
    return x * 42
"""
        tree = ast.parse(code)
        issues = antipatterns.detect_magic_numbers(tree)
        self.assertGreaterEqual(len(issues), 1)
        self.assertEqual(issues[0]["value"], 42)

    def test_detect_dead_code(self):
        code = """
def unreachable():
    return True
    print("Unreachable")
"""
        tree = ast.parse(code)
        issues = antipatterns.detect_dead_code(tree)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "dead_code")


if __name__ == "__main__":
    unittest.main()

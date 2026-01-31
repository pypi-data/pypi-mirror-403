import unittest
import ast
from ai_context_core.analyzer.ast_utils import detect_unused_imports
from ai_context_core.analyzer.dependencies import calculate_coupling_metrics


class TestDependenciesAdvanced(unittest.TestCase):
    def test_detect_unused_imports(self):
        code = """
import os
import sys
from pathlib import Path

print(os.name)
"""
        tree = ast.parse(code)
        unused = detect_unused_imports(tree)
        self.assertIn("sys", unused)
        self.assertIn("pathlib.Path", unused)
        self.assertNotIn("os", unused)

    def test_coupling_metrics(self):
        graph = {"A": {"B", "C"}, "B": {"C"}, "C": set()}
        metrics = calculate_coupling_metrics(graph)

        # A: fan_out=2, fan_in=0, cbo=2
        # B: fan_out=1, fan_in=1, cbo=2
        # C: fan_out=0, fan_in=2, cbo=2

        self.assertEqual(metrics["A"]["cbo"], 2)
        self.assertEqual(metrics["B"]["cbo"], 2)
        self.assertEqual(metrics["C"]["cbo"], 2)
        self.assertEqual(metrics["C"]["fan_in"], 2)


if __name__ == "__main__":
    unittest.main()

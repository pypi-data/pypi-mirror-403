"""Detección de Código Muerto (unreachable code)."""



import ast
from typing import List, Dict, Any
from .base import AntiPatternDetector


class DeadCodeDetector(AntiPatternDetector):
    """Detects local unreachable code (e.g. after return/raise)."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Detects unreachable code after return, raise, break, or continue.

        Args:
            node: The AST node to analyze.

        Returns:
            List of detected dead code issues.
        """
        self.issues = []
        if isinstance(node, (ast.FunctionDef, ast.Module)):
            for i, child in enumerate(node.body):
                if isinstance(child, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                    if i + 1 < len(node.body):
                        self._add_issue(
                            "dead_code",
                            "medium",
                            "Unreachable code detected",
                            node.body[i + 1].lineno,
                            1,
                        )
                        break
        return self.issues

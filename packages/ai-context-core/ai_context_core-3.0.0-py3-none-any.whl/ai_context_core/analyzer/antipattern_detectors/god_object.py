"""Detección de clases 'God Object' (con demasiados métodos)."""

"""God Object detector implementation."""

import ast
from typing import List, Dict, Any
from .base import AntiPatternDetector


class GodObjectDetector(AntiPatternDetector):
    """Detects 'God Object' classes with too many methods."""

    def __init__(self, threshold: int = 20):
        """Initialize the detector.

        Args:
            threshold: Minimum number of methods to trigger the antipattern.
        """
        super().__init__()
        self.threshold = threshold

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Detects 'God Object' classes con too many methods.

        Args:
            node: The AST node to analyze.

        Returns:
            List of detected god object issues.
        """
        if not isinstance(node, ast.ClassDef):
            return []
        self.issues = []
        count = sum(1 for i in node.body if isinstance(i, ast.FunctionDef))
        if count > self.threshold:
            self._add_issue(
                "god_object",
                "high",
                f"Class '{node.name}' is a God Object ({count} methods)",
                node.lineno,
                count,
            )
        return self.issues

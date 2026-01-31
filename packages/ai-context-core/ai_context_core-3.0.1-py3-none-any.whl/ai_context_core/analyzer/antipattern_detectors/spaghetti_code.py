"""Detección de 'Spaghetti Code' (alta complejidad ciclomática)."""



import ast
from typing import List, Dict, Any
from .base import AntiPatternDetector


class SpaghettiCodeDetector(AntiPatternDetector):
    """Detects 'Spaghetti Code' functions with high cyclomatic complexity."""

    def __init__(self, threshold: int = 25):
        """Initialize the detector.

        Args:
            threshold: Cyclomatic complexity threshold for the antipattern.
        """
        super().__init__()
        self.threshold = threshold

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Detects 'Spaghetti Code' functions with high cyclomatic complexity.

        Args:
            node: The AST node to analyze.

        Returns:
            List of detected spaghetti code issues.
        """
        if not isinstance(node, ast.FunctionDef):
            return []
        self.issues = []

        # Circular import protection
        from ..ast_utils import calculate_complexity

        cc = calculate_complexity(node)
        if cc > self.threshold:
            self._add_issue(
                "spaghetti_code",
                "high",
                f"Function '{node.name}' is Spaghetti Code (CC: {cc})",
                node.lineno,
                cc,
            )
        return self.issues

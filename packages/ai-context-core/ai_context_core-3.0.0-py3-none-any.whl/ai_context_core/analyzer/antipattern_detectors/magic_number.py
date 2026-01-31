"""Detección de 'Magic Numbers' (constantes numéricas arbitrarias)."""

"""Magic number detector implementation."""

import ast
from typing import List, Dict, Any
from .base import AntiPatternDetector


class MagicNumberDetector(AntiPatternDetector):
    """Detects 'Magic Numbers' usage (hardcoded numeric constants)."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Detects hardcoded magic numbers in the AST.

        Args:
            node: The AST node to analyze.

        Returns:
            List of detected magic number issues.
        """
        self.issues = []
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                if n.value not in (-1, 0, 1, 0.0, 1.0):
                    self._add_issue(
                        "magic_number",
                        "low",
                        f"Magic number detected: {n.value}",
                        n.lineno,
                        n.value,
                    )
        return self.issues

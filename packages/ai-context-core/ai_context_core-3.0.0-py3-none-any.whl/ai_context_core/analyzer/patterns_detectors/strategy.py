"""Strategy pattern detector implementation."""

import ast
from typing import Dict, List, Any
from .base import PatternDetector


class StrategyDetector(PatternDetector):
    """Detects Strategy pattern implementations."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Detects Strategy pattern implementations in a node.

        Args:
            node: The AST node to analyze.

        Returns:
            List of detected strategy instances.
        """
        if not isinstance(node, ast.ClassDef):
            return []
        self.evidence, self.confidence = [], 0
        has_inj = False

        for item in node.body:
            if isinstance(item, ast.FunctionDef) and (
                item.name == "__init__" or "set_" in item.name
            ):
                for arg in item.args.args:
                    if any(
                        kw in arg.arg.lower()
                        for kw in ("strategy", "algorithm", "engine", "handler", "mode")
                    ):
                        has_inj = True
                        self._add_evidence(
                            f"Injection detected in '{item.name}' via '{arg.arg}'", 30
                        )
                        break

        if has_inj:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name not in (
                    "__init__",
                    "set_",
                ):
                    for sub in ast.walk(item):
                        if isinstance(sub, ast.Call) and isinstance(
                            sub.func, ast.Attribute
                        ):
                            if any(
                                kw in ast.unparse(sub.func).lower()
                                for kw in ("strategy", "algorithm", "engine", "handler")
                            ):
                                self._add_evidence(
                                    f"Strategy call in '{item.name}': {ast.unparse(sub.func)}()",
                                    40,
                                )
                                break

        if self.confidence >= 50:
            return [
                {
                    "class": node.name,
                    "confidence": min(self.confidence, 100),
                    "evidence": self.evidence,
                }
            ]
        return []

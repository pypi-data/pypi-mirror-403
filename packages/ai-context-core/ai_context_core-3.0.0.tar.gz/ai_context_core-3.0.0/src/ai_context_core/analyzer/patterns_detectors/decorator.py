"""Decorator pattern detector implementation."""

import ast
from typing import Dict, List, Any
from .base import PatternDetector


class DecoratorDetector(PatternDetector):
    """Detects Decorator pattern implementations."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Detects Decorator pattern implementations in a node.

        Args:
            node: The AST node to analyze.

        Returns:
            List of detected decorator instances.
        """
        res = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.evidence, self.confidence = [], 0
            inner = next(
                (
                    i
                    for i in node.body
                    if isinstance(i, (ast.FunctionDef, ast.AsyncFunctionDef))
                ),
                None,
            )
            if inner:
                if any(
                    isinstance(i, ast.Return)
                    and isinstance(i.value, ast.Name)
                    and i.value.id == inner.name
                    for i in node.body
                ):
                    self._add_evidence(
                        f"Function contains and returns inner '{inner.name}'", 50
                    )
                    if any(
                        isinstance(d, ast.Call)
                        and (
                            getattr(d.func, "attr", "") == "wraps"
                            or getattr(d.func, "id", "") == "wraps"
                        )
                        for d in inner.decorator_list
                    ):
                        self._add_evidence("Uses @functools.wraps", 40)
            if self.confidence >= 50:
                res.append(
                    {
                        "class": node.name,
                        "type": "function",
                        "confidence": min(self.confidence, 100),
                        "evidence": self.evidence,
                    }
                )

        elif isinstance(node, ast.ClassDef):
            self.evidence, self.confidence = [], 0
            names = {i.name for i in node.body if isinstance(i, ast.FunctionDef)}
            if "__init__" in names and "__call__" in names:
                self._add_evidence("Class implements both __init__ and __call__", 60)
            if self.confidence >= 50:
                res.append(
                    {
                        "class": node.name,
                        "type": "class",
                        "confidence": min(self.confidence, 100),
                        "evidence": self.evidence,
                    }
                )
        return res

"""Singleton pattern detector implementation."""

import ast
from ..constants import PATTERN_DETECTION_CONFIDENCE_HIGH
from .base import PatternDetector


class SingletonDetector(PatternDetector):
    """Detects Singleton pattern implementations."""

    def visit(self, node: ast.AST):
        """Analyzes a node to find Singleton pattern evidence.

        Args:
            node: The AST node to analyze.
        """
        self.evidence, self.confidence = [], 0
        if not isinstance(node, ast.ClassDef):
            return
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__new__":
                self._add_evidence("Overrides __new__ to control instantiation", 60)
            if isinstance(item, ast.FunctionDef):
                is_static = any(
                    isinstance(d, (ast.Name, ast.Attribute))
                    and (
                        getattr(d, "id", "") in ("classmethod", "staticmethod")
                        or getattr(d, "attr", "") in ("classmethod", "staticmethod")
                    )
                    for d in item.decorator_list
                )
                if is_static and any(
                    k in item.name.lower()
                    for k in ("instance", "singleton", "get_inst")
                ):
                    self._add_evidence(
                        f"Static/Class method '{item.name}' detected",
                        PATTERN_DETECTION_CONFIDENCE_HIGH - 30,
                    )
            if isinstance(item, (ast.Assign, ast.AnnAssign)):
                targets = (
                    item.targets if isinstance(item, ast.Assign) else [item.target]
                )
                for t in targets:
                    if isinstance(t, ast.Name) and any(
                        k in t.id.lower() for k in ("instance", "_inst")
                    ):
                        self._add_evidence(
                            f"Static instance variable '{t.id}' found", 20
                        )

"""Factory pattern detector implementation."""

import ast
from typing import Dict, List, Any
from ..constants import (
    PATTERN_DETECTION_CONFIDENCE_HIGH,
    PATTERN_DETECTION_CONFIDENCE_MAXIMUM,
)
from .base import PatternDetector


class FactoryDetector(PatternDetector):
    """Detects Factory pattern implementations."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Detects Factory pattern implementations in a node.

        Args:
            node: The AST node to analyze.

        Returns:
            List of detected factory instances.
        """
        if not isinstance(node, ast.ClassDef):
            return []
        res = []
        base_conf = 30 if "factory" in node.name.lower() else 0

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.evidence, self.confidence = [], base_conf
                if base_conf:
                    self.evidence.append(
                        f"Class '{node.name}' contains 'Factory' in name"
                    )

                if any(
                    p in item.name.lower()
                    for p in ("create_", "build_", "make_", "factory")
                ):
                    self._add_evidence(
                        f"Method '{item.name}' matches factory naming", 40
                    )

                for sub in ast.walk(item):
                    if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Call):
                        self._add_evidence(
                            "Method instantiates and returns an object", 30
                        )
                        break

                if self.confidence >= PATTERN_DETECTION_CONFIDENCE_HIGH:
                    res.append(
                        {
                            "class": node.name,
                            "method": item.name,
                            "confidence": min(
                                self.confidence, PATTERN_DETECTION_CONFIDENCE_MAXIMUM
                            ),
                            "evidence": self.evidence,
                        }
                    )
        return res

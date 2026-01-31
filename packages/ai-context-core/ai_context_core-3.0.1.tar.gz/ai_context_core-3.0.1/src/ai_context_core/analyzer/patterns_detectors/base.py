"""Base class for design pattern detectors."""

import ast
from typing import Dict, List, Any
from ..constants import (
    PATTERN_DETECTION_CONFIDENCE_THRESHOLD,
    PATTERN_DETECTION_CONFIDENCE_MAXIMUM,
)


class PatternDetector:
    """Base class for design pattern detectors."""

    def __init__(self):
        """Initialize the pattern detector with empty evidence and zero confidence."""
        self.evidence = []
        self.confidence = 0

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Analyzes a node and returns detected pattern instances.
        Implemented for backward compatibility with individual detector calls.
        """
        if hasattr(self, "visit"):
            self.visit(node)
            return self.get_results(node)
        raise NotImplementedError

    def _add_evidence(self, msg: str, weight: int):
        """Adds evidence of a pattern and increases confidence.

        Args:
            msg: Description of the evidence found.
            weight: Confidence weight to add.
        """
        self.evidence.append(msg)
        self.confidence += weight

    def get_results(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Returns the results if confidence threshold is met."""
        if self.confidence >= PATTERN_DETECTION_CONFIDENCE_THRESHOLD:
            name = getattr(node, "name", "N/A")
            return [
                {
                    "class": name,
                    "confidence": min(
                        self.confidence, PATTERN_DETECTION_CONFIDENCE_MAXIMUM
                    ),
                    "evidence": self.evidence,
                }
            ]
        return []

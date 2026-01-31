"""Base classes for anti-pattern detection."""



import ast
from typing import List, Dict, Any


class AntiPatternDetector:
    """Base class for anti-pattern detectors."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the antipattern detector.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.issues = []

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Analyzes a node and returns detected issue instances.

        Args:
            node: The AST node to analyze.

        Returns:
            A list of detected issues.
        """
        raise NotImplementedError

    def _add_issue(self, type_id: str, severity: str, msg: str, line: int, value: Any):
        """Adds a detected issue to the list.

        Args:
            type_id: Unique identifier for the issue type.
            severity: Issue severity (low, medium, high).
            msg: Descriptive message for the issue.
            line: Line number where the issue was detected.
            value: The value or metric related to the issue.
        """
        self.issues.append(
            {
                "type": type_id,
                "severity": severity,
                "message": msg,
                "line": line,
                "value": value,
            }
        )

"""Anti-pattern detection for Python code.

This module identifies common bad practices and code smells such as God Objects,
Spaghetti Code, Magic Numbers, and Dead Code.
"""

import ast
from typing import List, Dict, Any


class AntiPatternDetector:
    """Base class for anti-pattern detectors."""

    def __init__(self):
        self.issues = []

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Analyzes a node and returns detected issue instances."""
        raise NotImplementedError

    def _add_issue(self, type_id: str, severity: str, msg: str, line: int, value: Any):
        self.issues.append(
            {
                "type": type_id,
                "severity": severity,
                "message": msg,
                "line": line,
                "value": value,
            }
        )


class GodObjectDetector(AntiPatternDetector):
    """Detects 'God Object' classes with too many methods."""

    def __init__(self, threshold: int = 20):
        super().__init__()
        self.threshold = threshold

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
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


class SpaghettiCodeDetector(AntiPatternDetector):
    """Detects 'Spaghetti Code' functions with high cyclomatic complexity."""

    def __init__(self, threshold: int = 25):
        super().__init__()
        self.threshold = threshold

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        if not isinstance(node, ast.FunctionDef):
            return []
        self.issues = []
        from .ast_utils import calculate_complexity

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


class MagicNumberDetector(AntiPatternDetector):
    """Detects 'Magic Numbers' usage (hardcoded numeric constants)."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
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


class DeadCodeDetector(AntiPatternDetector):
    """Detects local unreachable code (e.g. after return/raise)."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
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


def detect_god_object(
    tree: ast.AST, threshold_methods: int = 20
) -> List[Dict[str, Any]]:
    det = GodObjectDetector(threshold_methods)
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res


def detect_spaghetti_code(
    tree: ast.AST, complexity_threshold: int = 25
) -> List[Dict[str, Any]]:
    det = SpaghettiCodeDetector(complexity_threshold)
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res


def detect_magic_numbers(
    tree: ast.AST, threshold_occurrences: int = 3
) -> List[Dict[str, Any]]:
    return MagicNumberDetector().detect(tree)


def detect_dead_code(tree: ast.AST) -> List[Dict[str, Any]]:
    det = DeadCodeDetector()
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res

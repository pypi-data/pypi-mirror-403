"""Anti-pattern detection for Python code.

This module now serves as a facade, delegating specific detection logic
to the specialized modules in the 'antipattern_detectors' package.
"""

import ast
from typing import List, Dict, Any

from .antipattern_detectors.god_object import GodObjectDetector
from .antipattern_detectors.spaghetti_code import SpaghettiCodeDetector
from .antipattern_detectors.magic_number import MagicNumberDetector
from .antipattern_detectors.dead_code import DeadCodeDetector


def detect_god_object(
    tree: ast.AST, threshold_methods: int = 20
) -> List[Dict[str, Any]]:
    """Detects 'God Object' classes with too many methods.

    Args:
        tree: The AST to analyze.
        threshold_methods: Number of methods to consider a class a God Object.

    Returns:
        List of issues found.
    """
    det = GodObjectDetector(threshold_methods)
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res


def detect_spaghetti_code(
    tree: ast.AST, complexity_threshold: int = 25
) -> List[Dict[str, Any]]:
    """Detects 'Spaghetti Code' functions with high cyclomatic complexity.

    Args:
        tree: The AST to analyze.
        complexity_threshold: The threshold for cyclomatic complexity.

    Returns:
        List of issues found.
    """
    det = SpaghettiCodeDetector(complexity_threshold)
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res


def detect_magic_numbers(tree: ast.AST) -> List[Dict[str, Any]]:
    """Detects 'Magic Numbers' usage (hardcoded numeric constants).

    Args:
        tree: The AST to analyze.

    Returns:
        List of issues found.
    """
    return MagicNumberDetector().detect(tree)


def detect_dead_code(tree: ast.AST) -> List[Dict[str, Any]]:
    """Detects local unreachable code.

    Args:
        tree: The AST to analyze.

    Returns:
        List of issues found.
    """
    det = DeadCodeDetector()
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res

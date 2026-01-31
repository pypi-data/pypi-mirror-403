"""Complexity analysis utilities for ai-context-core."""

import ast
from typing import Set


class ComplexityVisitor(ast.NodeVisitor):
    """Visitor to calculate cyclomatic complexity."""

    def __init__(self):
        """Initialize the visitor. Base complexity starts at 1."""
        self.complexity = 1
        self.decision_lines = set()

    def _add_decision(self, node):
        """Increments complexity and records the decision line.

        Args:
            node: The AST node representing a decision point.
        """
        self.complexity += 1
        if hasattr(node, "lineno"):
            self.decision_lines.add(node.lineno)

    def visit_If(self, node: ast.If):
        """Visits an if-statement.

        Args:
            node: The If node.
        """
        self._add_decision(node)
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        """Visits a while-loop.

        Args:
            node: The While node.
        """
        self._add_decision(node)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        """Visits a for-loop.

        Args:
            node: The For node.
        """
        self._add_decision(node)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        """Visits an async for-loop.

        Args:
            node: The AsyncFor node.
        """
        self._add_decision(node)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        """Visits a try-except block.

        Args:
            node: The Try node.
        """
        self.generic_visit(node)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        """Visits an async with-statement.

        Args:
            node: The AsyncWith node.
        """
        self.generic_visit(node)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Visits an except handler.

        Args:
            node: The ExceptHandler node.
        """
        self._add_decision(node)
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        """Visits a boolean operation (and/or).

        Args:
            node: The BoolOp node.
        """
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp):
        """Visits a list comprehension.

        Args:
            node: The ListComp node.
        """
        for gen in node.generators:
            self._add_decision(gen)
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp):
        """Visits a set comprehension.

        Args:
            node: The SetComp node.
        """
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp):
        """Visits a dictionary comprehension.

        Args:
            node: The DictComp node.
        """
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        """Visits a generator expression."""
        self.complexity += len(node.generators)
        self.generic_visit(node)


def calculate_complexity(tree: ast.AST) -> int:
    """Calculates optimized cyclomatic complexity.

    Args:
        tree: The AST tree to analyze

    Returns:
        The calculated complexity score
    """
    visitor = ComplexityVisitor()
    visitor.visit(tree)
    return _apply_complexity_penalty(visitor.complexity, visitor.decision_lines)


def _apply_complexity_penalty(complexity: int, decision_lines: Set[int]) -> int:
    """Applies a penalty for highly dense logic (many decisions in few lines).

    Args:
        complexity: The base complexity score
        decision_lines: Set of line numbers with decision points

    Returns:
        The adjusted complexity score with penalty applied
    """
    from .constants import (
        COMPLEXITY_PENALTY_DENSITY_THRESHOLD,
        COMPLEXITY_PENALTY_MULTIPLIER,
    )

    if not decision_lines:
        return complexity

    line_range = max(decision_lines) - min(decision_lines) + 1
    density = len(decision_lines) / line_range

    if density > COMPLEXITY_PENALTY_DENSITY_THRESHOLD:
        return int(complexity * COMPLEXITY_PENALTY_MULTIPLIER)

    return complexity

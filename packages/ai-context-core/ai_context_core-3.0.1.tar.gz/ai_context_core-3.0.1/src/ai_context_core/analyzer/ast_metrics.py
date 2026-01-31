"""Metrics calculation for Python AST (Complexity, Halstead, Type Hints)."""

import ast
from collections import Counter
from typing import Dict, Any


class TypeHintVisitor(ast.NodeVisitor):
    """Visitor to calculate type hint coverage."""

    def __init__(self):
        """Initialize the visitor."""
        self.total_functions = 0
        self.typed_functions = 0

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visits a function definition to check for type hints.

        Args:
            node: The FunctionDef node.
        """
        self.total_functions += 1

        has_return_type = node.returns is not None
        args = [arg for arg in node.args.args if arg.arg not in ("self", "cls")]
        total_args = len(args)
        typed_args = sum(1 for arg in args if arg.annotation is not None)

        if has_return_type and (total_args == 0 or total_args == typed_args):
            self.typed_functions += 1

        self.generic_visit(node)


class HalsteadVisitor(ast.NodeVisitor):
    """Visitor to calculate Halstead metrics."""

    OPERATORS = (
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.Pow,
        ast.LShift,
        ast.RShift,
        ast.BitOr,
        ast.BitXor,
        ast.BitAnd,
        ast.FloorDiv,
        ast.And,
        ast.Or,
        ast.Not,
        ast.Invert,
        ast.UAdd,
        ast.USub,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.Is,
        ast.IsNot,
        ast.In,
        ast.NotIn,
        ast.If,
        ast.For,
        ast.While,
        ast.Try,
        ast.With,
        ast.FunctionDef,
        ast.ClassDef,
    )

    def __init__(self):
        """Initialize the visitor counters."""
        self.operators = Counter()
        self.operands = Counter()

    def visit(self, node: ast.AST):
        """Override visit to check for operators and operands generically."""
        if isinstance(node, self.OPERATORS):
            self.operators[type(node).__name__] += 1
        elif isinstance(node, ast.Name):
            self.operands[node.id] += 1
        elif isinstance(node, ast.Constant):
            self.operands[str(node.value)] += 1
        super().visit(node)


def calculate_complexity(tree: ast.AST) -> int:
    """Calculates cyclomatic complexity of an AST tree.

    Delegates to ComplexityVisitor for detailed branching analysis.

    Args:
        tree: The AST to analyze.

    Returns:
        Cyclomatic complexity value.
    """
    # Note: Using import from complexity_visitor if available, otherwise implementing simple
    # logic here or assuming it was imported.
    # For now, let's implement a simple direct visitor or re-use existing logic.
    # The original file imported from .complexity_visitor inside the function.
    # We should probably port that logic here or maintain the import.
    # Assuming we want to consolidate code metrics.
    try:
        from .complexity_visitor import calculate_complexity as _calc_complexity

        return _calc_complexity(tree)
    except ImportError:
        # Fallback implementation if module missing
        return _simple_complexity(tree)


def _simple_complexity(tree: ast.AST) -> int:
    """Fallback complexity calculation using simple node walking.

    Args:
        tree: The AST to analyze.

    Returns:
        Rough cyclomatic complexity.
    """
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.If,
                ast.While,
                ast.For,
                ast.Assert,
                ast.ExceptHandler,
                ast.With,
                ast.Try,
            ),
        ):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity


def calculate_type_hint_coverage(tree: ast.AST) -> Dict[str, Any]:
    """Calculates the percentage of functions with type hints.

    Args:
        tree: The AST to analyze.

    Returns:
        Dictionary with total_functions, typed_functions, and coverage.
    """
    visitor = TypeHintVisitor()
    visitor.visit(tree)

    total = visitor.total_functions
    typed = visitor.typed_functions
    coverage = (typed / total * 100) if total > 0 else 100.0

    return {
        "total_functions": total,
        "typed_functions": typed,
        "coverage": coverage,
    }


def calculate_halstead_metrics(tree: ast.AST) -> Dict[str, Any]:
    """Calculates basic Halstead complexity metrics.

    Computes vocabulary, length, volume, difficulty, and effort.

    Args:
        tree: The AST to analyze.

    Returns:
        Dictionary of Halstead metrics.
    """
    visitor = HalsteadVisitor()
    visitor.visit(tree)

    n1 = len(visitor.operators)
    n2 = len(visitor.operands)
    N1 = sum(visitor.operators.values())
    N2 = sum(visitor.operands.values())

    h_vocabulary = n1 + n2
    h_length = N1 + N2

    if n1 > 0 and n2 > 0:
        h_volume = h_length * (h_vocabulary.bit_length() - 1)
        h_difficulty = (n1 / 2) * (N2 / n2)
        h_effort = h_difficulty * h_volume
    else:
        h_volume = h_difficulty = h_effort = 0

    return {
        "vocabulary": h_vocabulary,
        "length": h_length,
        "volume": round(h_volume, 2),
        "difficulty": round(h_difficulty, 2),
        "effort": round(h_effort, 2),
    }


def calculate_sloc(tree: ast.AST, content: str) -> int:
    """Calculates Source Lines of Code (SLOC).

    Excludes:
    - Blank lines
    - Comment-only lines
    - Docstrings (module, class, and function level)

    Args:
        tree: The AST of the module.
        content: The raw source code string.

    Returns:
        The count of real source lines of code.
    """
    import io
    import tokenize

    # 1. Identify docstring ranges using AST
    docstring_ranges = []
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                # We need to find the Expr node that contains the docstring to get its range
                # In Python 3.8+, Expr nodes have lineno/end_lineno
                body = node.body
                if (
                    body
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, (ast.Constant, ast.Str))
                ):
                    doc_node = body[0]
                    if hasattr(doc_node, "lineno") and hasattr(doc_node, "end_lineno"):
                        docstring_ranges.append((doc_node.lineno, doc_node.end_lineno))

    # 2. Use tokenize to iterate through lines and filter
    sloc_count = 0
    lines_with_code = set()

    try:
        tokens = tokenize.generate_tokens(io.StringIO(content).readline)
        for tok in tokens:
            start_line = tok.start[0]
            end_line = tok.end[0]

            # Skip comments and blank lines
            if tok.type in (
                tokenize.COMMENT,
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.INDENT,
                tokenize.DEDENT,
                tokenize.ENDMARKER,
            ):
                continue

            # Check if this token is within a docstring range
            is_docstring = False
            for dr in docstring_ranges:
                if dr[0] <= start_line <= dr[1]:
                    is_docstring = True
                    break

            if not is_docstring:
                # Count lines that contain at least one non-comment, non-docstring token
                for line_idx in range(start_line, end_line + 1):
                    lines_with_code.add(line_idx)

        sloc_count = len(lines_with_code)
    except Exception:
        # Fallback to a simpler line count if tokenization fails
        # (e.g., due to encoding issues or partial files)
        lines = [line.strip() for line in content.splitlines()]
        sloc_count = len([line for line in lines if line and not line.startswith("#")])

    return sloc_count

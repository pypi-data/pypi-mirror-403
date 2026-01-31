"""AST utilities for Python code analysis.

This module is now a deprecated facade. Please import from the specific submodules:
- ai_context_core.analyzer.ast_visitors
- ai_context_core.analyzer.ast_metrics
- ai_context_core.analyzer.ast_entry_points
- ai_context_core.analyzer.ast_qgis
"""

import ast

# Re-exports for backward compatibility
from .ast_visitors import (  # noqa: F401
    extract_functions,
    extract_classes,
    check_docstrings,
    extract_imports,
    detect_unused_imports,
)
from .ast_metrics import (  # noqa: F401
    calculate_complexity,
    calculate_halstead_metrics,
    calculate_type_hint_coverage,
    calculate_sloc,
)
from .ast_entry_points import (  # noqa: F401
    is_entry_point,
    has_main_guard,
)
from .ast_qgis import (  # noqa: F401
    check_qgis_compliance,
)


def extract_base_name(node: ast.AST) -> str:
    """Helper to extract the name of a base class from a node.

    Args:
        node: The AST node to extract the name from

    Returns:
        The extracted name or 'Unknown' if extraction fails
    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return node.attr
    elif isinstance(node, ast.Call):
        return extract_base_name(node.func)
    return "Unknown"

"""Import analysis utilities for ai-context-core."""

import ast
from typing import List


class ImportVisitor(ast.NodeVisitor):
    """Visitor to extract imports."""

    def __init__(self):
        """Initialize the ImportVisitor with empty collections."""
        self.imports = []
        self.imported_names = {}  # alias_in_scope -> full_import_name
        self.used_names = set()

    def visit_Import(self, node: ast.Import):
        """Visits an import node and records imported modules.

        Args:
            node: The Import node.
        """
        for alias in node.names:
            self.imports.append(alias.name)
            name_in_scope = alias.asname or alias.name.split(".")[0]
            self.imported_names[name_in_scope] = alias.name

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visits an import-from node and records fully qualified names.

        Args:
            node: The ImportFrom node.
        """
        module = node.module or ""
        for alias in node.names:
            if module:
                full_name = f"{module}.{alias.name}"
                self.imports.append(full_name)
            else:
                full_name = alias.name
                self.imports.append(full_name)

            name_in_scope = alias.asname or alias.name
            self.imported_names[name_in_scope] = full_name

    def visit_Name(self, node: ast.Name):
        """Visits a Name node and records it as used if it's being loaded.

        Args:
            node: The Name node.
        """
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute):
        """Visits an Attribute node and records the base Name as used.

        Args:
            node: The Attribute node.
        """
        # Recursively find the base Name in an Attribute chain (e.g., a.b.c)
        curr = node.value
        while isinstance(curr, ast.Attribute):
            curr = curr.value
        if isinstance(curr, ast.Name):
            self.used_names.add(curr.id)
        self.generic_visit(node)


def extract_imports(tree: ast.AST) -> List[str]:
    """Extracts module imports in an optimized way.

    Args:
        tree: The AST tree to analyze

    Returns:
        List of unique imports
    """
    visitor = ImportVisitor()
    visitor.visit(tree)

    # De-duplicate while maintaining order
    seen = set()
    unique_imports = []
    for imp in visitor.imports:
        if imp not in seen:
            seen.add(imp)
            unique_imports.append(imp)
    return unique_imports


def detect_unused_imports(tree: ast.AST) -> List[str]:
    """Identifies imports that are not used anywhere in the module.

    Args:
        tree: The AST tree to analyze

    Returns:
        List of unused imports
    """
    visitor = ImportVisitor()
    visitor.visit(tree)

    unused = [
        name
        for alias, name in visitor.imported_names.items()
        if alias not in visitor.used_names and alias != "*"
    ]
    return sorted(list(set(unused)))

"""Generic AST visitors for information extraction."""

import ast
from typing import List, Dict, Any, Optional


class FunctionVisitor(ast.NodeVisitor):
    """Visitor to extract function names and argument counts."""

    def __init__(self):
        """Initialize the FunctionVisitor."""
        self.functions = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visits a function definition and extracts metadata.

        Args:
            node: The FunctionDef node.
        """
        func_info = node.name
        args_count = len(node.args.args)
        if args_count > 0:
            func_info = f"{func_info}({args_count} args)"
        self.functions.append(func_info)
        self.generic_visit(node)


class ClassVisitor(ast.NodeVisitor):
    """Visitor to extract class names and inheritance infomation."""

    def __init__(self):
        """Initialize the ClassVisitor."""
        self.classes = []

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visits a class definition and extracts inheritance.

        Args:
            node: The ClassDef node.
        """
        bases = [self._get_base_name(base) for base in node.bases]
        inheritance = f"({', '.join(bases)})" if bases else ""
        self.classes.append(f"{node.name}{inheritance}")
        self.generic_visit(node)

    def _get_base_name(self, node: ast.AST) -> Optional[str]:
        """Extracts the base name from a Name or Attribute node.

        Args:
            node: The node to extract the name from.

        Returns:
            The name string or None if extraction fails.
        """
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self._get_base_name(node.value)
        return None


class DocstringVisitor(ast.NodeVisitor):
    """Visitor to check for docstring presence."""

    def __init__(self):
        """Initialize the DocstringVisitor."""
        self.docstrings = {"module": False, "classes": {}, "functions": {}}

    def visit_Module(self, node: ast.Module):
        """Visits the module node.

        Args:
            node: The Module node.
        """
        self.docstrings["module"] = ast.get_docstring(node) is not None
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visits a class definition.

        Args:
            node: The ClassDef node.
        """
        self.docstrings["classes"][node.name] = ast.get_docstring(node) is not None
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visits a function definition.

        Args:
            node: The FunctionDef node.
        """
        self.docstrings["functions"][node.name] = ast.get_docstring(node) is not None
        self.generic_visit(node)


class ImportVisitor(ast.NodeVisitor):
    """Visitor to extract imports."""

    def __init__(self):
        """Initialize the ImportVisitor."""
        self.imports = []
        self.imported_names = {}  # alias_in_scope -> full_import_name
        self.used_names = set()

    def visit_Import(self, node: ast.Import):
        """Visits an import node.

        Args:
            node: The Import node.
        """
        for alias in node.names:
            self.imports.append(alias.name)
            name_in_scope = alias.asname or alias.name.split(".")[0]
            self.imported_names[name_in_scope] = alias.name

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visits an import-from node.

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
        """Visits a name node to track variable usage for unused import detection.

        Args:
            node: The Name node.
        """
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute):
        """Visits an attribute node to track variable usage for unused import detection.

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


def extract_functions(tree: ast.AST) -> List[str]:
    """Extracts function names and basic argument counts from an AST."""
    visitor = FunctionVisitor()
    visitor.visit(tree)
    return visitor.functions


def extract_classes(tree: ast.AST) -> List[str]:
    """Extracts class names with inheritance information from an AST.

    Args:
        tree: The AST to analyze.

    Returns:
        List of class strings with inheritance (e.g., 'MyClass(Base)').
    """
    visitor = ClassVisitor()
    visitor.visit(tree)
    return visitor.classes


def check_docstrings(tree: ast.AST) -> Dict[str, Any]:
    """Checks for the presence of docstrings in modules, classes, and functions.

    Args:
        tree: The AST to analyze.

    Returns:
        Dictionary with 'module', 'classes', and 'functions' documentation status.
    """
    visitor = DocstringVisitor()
    visitor.visit(tree)
    return visitor.docstrings


def extract_imports(tree: ast.AST) -> List[str]:
    """Extracts module imports from an AST tree.

    Args:
        tree: The AST to analyze.

    Returns:
        List of imported module names.
    """
    visitor = ImportVisitor()
    visitor.visit(tree)
    return visitor.imports


def detect_unused_imports(tree: ast.AST) -> List[str]:
    """Identifies imports that are not used anywhere in the module."""
    visitor = ImportVisitor()
    visitor.visit(tree)

    unused = []
    for name_in_scope, full_import in visitor.imported_names.items():
        if name_in_scope not in visitor.used_names:
            unused.append(full_import)

    return unused

"""AST utilities for Python code analysis.

This module provides tools for extracting functions, classes, complexity,
type hint coverage, Halstead metrics, and imports from Python source code.
"""

import ast
from collections import Counter
from typing import Any, List, Dict, Set


class FunctionVisitor(ast.NodeVisitor):
    """Visitor to extract function names and argument counts."""

    def __init__(self):
        self.functions = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        func_info = node.name
        args_count = len(node.args.args)
        if args_count > 0:
            func_info = f"{func_info}({args_count} args)"
        self.functions.append(func_info)
        self.generic_visit(node)


class ClassVisitor(ast.NodeVisitor):
    """Visitor to extract class names and inheritance infomation."""

    def __init__(self):
        self.classes = []

    def visit_ClassDef(self, node: ast.ClassDef):
        bases = [self._get_base_name(base) for base in node.bases]
        inheritance = f"({', '.join(bases)})" if bases else ""
        self.classes.append(f"{node.name}{inheritance}")
        self.generic_visit(node)

    def _get_base_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return "Unknown"


class DocstringVisitor(ast.NodeVisitor):
    """Visitor to check for docstring presence."""

    def __init__(self):
        self.docstrings = {"module": False, "classes": {}, "functions": {}}

    def visit_Module(self, node: ast.Module):
        self.docstrings["module"] = ast.get_docstring(node) is not None
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.docstrings["classes"][node.name] = ast.get_docstring(node) is not None
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.docstrings["functions"][node.name] = ast.get_docstring(node) is not None
        self.generic_visit(node)


class EntryPointVisitor(ast.NodeVisitor):
    """Visitor to detect if a module is an entry point."""

    def __init__(self):
        self.result = {"is_entry_point": False, "type": None}

    def visit_If(self, node: ast.If):
        if self.result["is_entry_point"]:
            return

        # Check for if __name__ == "__main__":
        try:
            if (
                isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "__name__"
            ):
                for comparator in node.test.comparators:
                    if (
                        isinstance(comparator, ast.Constant)
                        and comparator.value == "__main__"
                    ):
                        self.result = {"is_entry_point": True, "type": "main_guard"}
                        return
        except Exception:
            pass
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.result["is_entry_point"]:
            return

        # QGIS classFactory
        if is_qgis_entry_point_node(node):
            self.result = {"is_entry_point": True, "type": "qgis_plugin"}
            return

        # Check decorators
        for decorator in node.decorator_list:
            self._check_decorator(decorator)
            if self.result["is_entry_point"]:
                return

        self.generic_visit(node)

    def _check_decorator(self, decorator: ast.AST):
        check_node = decorator
        if isinstance(decorator, ast.Call):
            check_node = decorator.func

        if isinstance(check_node, ast.Attribute):
            attr = check_node.attr
            # Click
            if (
                isinstance(check_node.value, ast.Name)
                and check_node.value.id == "click"
                and attr in ("command", "group")
            ):
                self.result = {"is_entry_point": True, "type": "click_cli"}
            # Flask
            elif attr == "route":
                self.result = {"is_entry_point": True, "type": "flask_app"}
            # FastAPI
            elif attr in ("get", "post", "put", "delete", "patch"):
                self.result = {"is_entry_point": True, "type": "fastapi_app"}

    def visit_Assign(self, node: ast.Assign):
        if self.result["is_entry_point"]:
            return

        for target in node.targets:
            if isinstance(target, ast.Name):
                self._check_assignment(target.id, node.value)
                if self.result["is_entry_point"]:
                    return
        self.generic_visit(node)

    def _check_assignment(self, target_id: str, value_node: ast.AST):
        # Django
        if target_id == "application":
            self.result = {"is_entry_point": True, "type": "django_app"}
        elif target_id == "urlpatterns" and isinstance(
            value_node, (ast.List, ast.Tuple)
        ):
            self.result = {"is_entry_point": True, "type": "django_urls"}
        elif target_id == "INSTALLED_APPS" and isinstance(
            value_node, (ast.List, ast.Tuple)
        ):
            self.result = {"is_entry_point": True, "type": "django_settings"}

        # Flask/FastAPI instantiation i.e. app = Flask(__name__)
        elif target_id in ("app", "application") and isinstance(value_node, ast.Call):
            func = value_node.func
            if isinstance(func, ast.Name):
                if func.id == "Flask":
                    self.result = {"is_entry_point": True, "type": "flask_app"}
                elif func.id == "FastAPI":
                    self.result = {"is_entry_point": True, "type": "fastapi_app"}


class QGISComplianceVisitor(ast.NodeVisitor):
    """Visitor to check for QGIS coding standards and best practices."""

    def __init__(self):
        self.results = {
            "processing_framework": False,
            "i18n_usage": {"tr": 0, "translate": 0, "total_strings": 0},
            "gdal_import_style": "Correct",  # Correct, Legacy, or Missing
            "qt_transition": {"pyqt5_imports": [], "pyqt6_imports": []},
            "signals_slots": {"modern": 0, "legacy": 0},
        }

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name == "gdal":
                self.results["gdal_import_style"] = "Legacy"
            if alias.name.startswith("PyQt5"):
                self.results["qt_transition"]["pyqt5_imports"].append(alias.name)
            if alias.name.startswith("PyQt6"):
                self.results["qt_transition"]["pyqt6_imports"].append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module == "osgeo" and any(a.name == "gdal" for a in node.names):
            self.results["gdal_import_style"] = "Correct"
        if node.module and node.module.startswith("PyQt5"):
            self.results["qt_transition"]["pyqt5_imports"].append(node.module)
        if node.module and node.module.startswith("PyQt6"):
            self.results["qt_transition"]["pyqt6_imports"].append(node.module)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        # Check for Processing Framework
        processing_bases = {"QgsProcessingAlgorithm", "QgsProcessingProvider"}
        for base in node.bases:
            base_name = extract_base_name(base)
            if base_name in processing_bases:
                self.results["processing_framework"] = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Check for i18n: self.tr() or QCoreApplication.translate()
        if isinstance(node.func, ast.Attribute) and node.func.attr == "tr":
            self.results["i18n_usage"]["tr"] += 1
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "translate":
            # Might be QCoreApplication.translate
            self.results["i18n_usage"]["translate"] += 1
        
        # Check for legacy signals/slots (SIGNAL/SLOT macros)
        if isinstance(node.func, ast.Name) and node.func.id in ("SIGNAL", "SLOT"):
            self.results["signals_slots"]["legacy"] += 1
        
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str) and len(node.value.strip()) > 1:
            self.results["i18n_usage"]["total_strings"] += 1
        self.generic_visit(node)


class TypeHintVisitor(ast.NodeVisitor):
    """Visitor to calculate type hint coverage."""

    def __init__(self):
        self.total_functions = 0
        self.typed_functions = 0

    def visit_FunctionDef(self, node: ast.FunctionDef):
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


class ImportVisitor(ast.NodeVisitor):
    """Visitor to extract imports."""

    def __init__(self):
        self.imports = []
        self.imported_names = {}  # alias_in_scope -> full_import_name
        self.used_names = set()

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
            name_in_scope = alias.asname or alias.name.split(".")[0]
            self.imported_names[name_in_scope] = alias.name

    def visit_ImportFrom(self, node: ast.ImportFrom):
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
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute):
        # Recursively find the base Name in an Attribute chain (e.g., a.b.c)
        curr = node.value
        while isinstance(curr, ast.Attribute):
            curr = curr.value
        if isinstance(curr, ast.Name):
            self.used_names.add(curr.id)
        self.generic_visit(node)


class ComplexityVisitor(ast.NodeVisitor):
    """Visitor to calculate cyclomatic complexity."""

    def __init__(self):
        self.complexity = 0
        self.decision_lines = set()

    def _add_decision(self, node):
        self.complexity += 1
        if hasattr(node, "lineno"):
            self.decision_lines.add(node.lineno)

    def visit_If(self, node: ast.If):
        self._add_decision(node)
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self._add_decision(node)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self._add_decision(node)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self._add_decision(node)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        self._add_decision(node)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self._add_decision(node)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self._add_decision(node)
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        self.complexity += len(node.generators)
        self.generic_visit(node)


# --- Public Interface Wrapper Functions ---


def extract_functions(tree: ast.AST) -> List[str]:
    """Extracts function names and basic argument counts from an AST."""
    visitor = FunctionVisitor()
    visitor.visit(tree)
    return visitor.functions


def extract_classes(tree: ast.AST) -> List[str]:
    """Extracts class names with inheritance information from an AST."""
    visitor = ClassVisitor()
    visitor.visit(tree)
    return visitor.classes


def check_docstrings(tree: ast.AST) -> Dict[str, Any]:
    """Checks for the presence of docstrings in modules, classes, and functions."""
    visitor = DocstringVisitor()
    visitor.visit(tree)
    return visitor.docstrings


def is_qgis_entry_point_node(node: ast.AST) -> bool:
    """Checks if an AST node is a QGIS classFactory entry point."""
    return (
        isinstance(node, ast.FunctionDef)
        and node.name == "classFactory"
        and any(arg.arg == "iface" for arg in node.args.args)
    )


def is_entry_point(tree: ast.AST) -> Dict[str, Any]:
    """Determines if the module is an entry point."""
    visitor = EntryPointVisitor()
    visitor.visit(tree)
    return visitor.result


def has_main_guard(tree: ast.AST) -> bool:
    """Checks if the module contains the standard 'if __name__ == "__main__":' guard."""
    result = is_entry_point(tree)
    return result["is_entry_point"] and result["type"] == "main_guard"


def calculate_type_hint_coverage(tree: ast.AST) -> Dict[str, Any]:
    """Calculates the percentage of functions with type hints."""
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
    """Calculates basic Halstead complexity metrics."""
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


def extract_imports(tree: ast.AST) -> List[str]:
    """Extracts module imports in an optimized way."""
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
    """Identifies imports that are not used anywhere in the module."""
    visitor = ImportVisitor()
    visitor.visit(tree)

    unused = [
        name
        for alias, name in visitor.imported_names.items()
        if alias not in visitor.used_names and alias != "*"
    ]
    return sorted(list(set(unused)))


def calculate_complexity(tree: ast.AST) -> int:
    """Calculates optimized cyclomatic complexity."""
    visitor = ComplexityVisitor()
    visitor.visit(tree)
    return _apply_complexity_penalty(visitor.complexity, visitor.decision_lines)


def _apply_complexity_penalty(complexity: int, decision_lines: Set[int]) -> int:
    """Applies a penalty for highly dense logic (many decisions in few lines)."""
    if not decision_lines:
        return complexity

    line_range = max(decision_lines) - min(decision_lines) + 1
    density = len(decision_lines) / line_range

    if density > 0.5:
        return int(complexity * 1.2)

    return complexity


def check_qgis_compliance(tree: ast.AST) -> Dict[str, Any]:
    """Runs a check for QGIS coding standards and best practices."""
    visitor = QGISComplianceVisitor()
    visitor.visit(tree)
    return visitor.results


def extract_base_name(node: ast.AST) -> str:
    """Helper to extract the name of a base class from a node."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return node.attr
    elif isinstance(node, ast.Call):
        return extract_base_name(node.func)
    return "Unknown"

"""QGIS specific compliance and pattern detection."""

import ast
from typing import Dict, Any


class QGISComplianceVisitor(ast.NodeVisitor):
    """Visitor to check for QGIS coding standards and best practices."""

    def __init__(self):
        """Initialize the QGIS compliance visitor."""
        self.results = {
            "processing_framework": False,
            "i18n_usage": {"tr": 0, "total_strings": 0},
            "gdal_import_style": "Modern",  # Modern, Legacy, or Missing
            "qt_transition": {"pyqt5_imports": [], "pyqt6_imports": []},
            "signals_slots": {"legacy": 0, "modern": 0},
        }

    def visit_Import(self, node: ast.Import):
        """Visits an import node and checks for legacy GDAL or PyQt imports.

        Args:
            node: The Import node.
        """
        for alias in node.names:
            if alias.name == "gdal":
                self.results["gdal_import_style"] = "Legacy"
            if alias.name.startswith("PyQt5"):
                self.results["qt_transition"]["pyqt5_imports"].append(alias.name)
            if alias.name.startswith("PyQt6"):
                self.results["qt_transition"]["pyqt6_imports"].append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visits an import-from node and checks for osgeo.gdal or PyQt.

        Args:
            node: The ImportFrom node.
        """
        if node.module == "osgeo" and any(a.name == "gdal" for a in node.names):
            self.results["gdal_import_style"] = "Correct"
        if node.module and node.module.startswith("PyQt5"):
            self.results["qt_transition"]["pyqt5_imports"].append(node.module)
        if node.module and node.module.startswith("PyQt6"):
            self.results["qt_transition"]["pyqt6_imports"].append(node.module)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visits a class definition to check for QGIS-specific base classes.

        Args:
            node: The ClassDef node.
        """
        # Check for Processing Framework
        processing_bases = {"QgsProcessingAlgorithm", "QgsProcessingProvider"}
        for base in node.bases:
            # Simple base name extraction
            base_name = "Unknown"
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr

            if base_name in processing_bases:
                self.results["processing_framework"] = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Visits a call node to detect i18n usage and legacy signals.

        Args:
            node: The Call node.
        """
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
        """Visits a constant node to count potential i18n strings.

        Args:
            node: The Constant node.
        """
        if isinstance(node.value, str) and len(node.value.strip()) > 1:
            self.results["i18n_usage"]["total_strings"] += 1
        self.generic_visit(node)


def is_qgis_entry_point_node(node: ast.AST) -> bool:
    """Checks if an AST node is a QGIS classFactory entry point."""
    return (
        isinstance(node, ast.FunctionDef)
        and node.name == "classFactory"
        and any(arg.arg == "iface" for arg in node.args.args)
    )


def check_qgis_compliance(tree: ast.AST) -> Dict[str, Any]:
    """Checks for compliance with QGIS-specific coding standards.

    Analyzes i18n usage, Qt transition preparation, and Processing Framework patterns.

    Args:
        tree: The AST to analyze.

    Returns:
        Dictionary of QGIS-specific metrics and findings.
    """
    visitor = QGISComplianceVisitor()
    visitor.visit(tree)
    return visitor.results

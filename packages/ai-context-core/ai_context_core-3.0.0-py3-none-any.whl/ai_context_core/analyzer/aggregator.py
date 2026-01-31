"""Aggregation logic for analyzer results.

Extracted from engine.py to reduce complexity and improve modularity.
"""

from typing import List, Dict, Any
import pathlib
import logging
import time
from . import issues, dependencies, metrics, ai_recommendations

logger = logging.getLogger(__name__)


class ResultsAggregator:
    """Aggregates and post-processes analysis results from multiple modules."""

    def __init__(self, project_path: pathlib.Path, config: Dict[str, Any]):
        """Initialize the aggregator.

        Args:
            project_path: Path to the project root.
            config: Configuration dictionary for metrics and thresholds.
        """
        self.project_path = project_path
        self.config = config

    def aggregate(
        self,
        m_data: List[Dict[str, Any]],
        graph_data: Dict[str, Any],
        git_data: Dict[str, Any],
        qgis_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Performs a full aggregation of module data and project-level metrics.

        Args:
            m_data: List of individual module analysis results.
            graph_data: Global dependency graph information.
            git_data: Evolution and churn data from git.
            qgis_metadata: Metadata from metadata.txt if available.

        Returns:
            A post-processed results dictionary ready for reporting.
        """
        # Filter out modules with syntax errors for metric calculations
        valid_modules = [m for m in m_data if not m.get("syntax_error")]

        # Dependency analysis
        unused_imports = dependencies.detect_unused_imports_in_project(valid_modules)
        graph_data["unused_imports"] = unused_imports

        # Security aggregation
        security_issues = issues.find_secrets(m_data, str(self.project_path))

        # QGIS compliance aggregation (Legacy logic from engine)
        qgis_compliance = self._aggregate_qgis_compliance(valid_modules, qgis_metadata)

        # Project-level metrics
        entry_points = [m["path"] for m in valid_modules if m.get("has_main")]
        project_metrics = metrics.calculate_project_metrics(
            valid_modules,
            entry_points,
            len([m for m in valid_modules if "test" in m["path"].lower()]),
            self.config,
            {"qgis_compliance": qgis_compliance},
        )

        # AI Recommendations
        recommendations = ai_recommendations.generate_recommendations(
            valid_modules, project_metrics
        )

        # Complexity aggregation (for backward compatibility)
        complexity_agg = {
            "total_modules": len(valid_modules),
            "total_lines": project_metrics.get("total_lines_code", 0),
            "total_physical_lines": project_metrics.get("total_physical_lines", 0),
            "total_functions": project_metrics.get("total_functions", 0),
            "total_classes": project_metrics.get("total_classes", 0),
            "average_complexity": project_metrics.get("average_complexity", 0),
            "avg_maintenance_index": project_metrics.get("avg_maintenance_index", 0),
            "most_complex_modules": sorted(
                [(m["path"], m.get("complexity", 0)) for m in valid_modules],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }

        # Module-level optimizations
        optimizations = issues.find_optimizations(valid_modules)

        return {
            "project_name": self.project_path.name,
            "metrics": project_metrics,
            "complexity": complexity_agg,
            "modules": m_data,
            "dependencies": graph_data,
            "security": security_issues,
            "qgis_compliance": qgis_compliance,
            "optimizations": optimizations,
            "recommendations": recommendations,
            "git": git_data,
            "timestamp": time.time() if "time" in globals() else None,
        }

    def _aggregate_qgis_compliance(
        self, m_data: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate QGIS-specific results from modules and metadata.

        Args:
            m_data: List of module analysis results.
            metadata: Parsed metadata.txt content.

        Returns:
            Dictionary with aggregated QGIS compliance metrics.
        """
        agg = {
            "metadata": metadata,
            "processing_framework_detected": any(
                m.get("qgis_compliance", {}).get("processing_framework") for m in m_data
            ),
            "i18n_stats": {
                "total_tr": sum(
                    m.get("qgis_compliance", {}).get("i18n_usage", {}).get("tr", 0)
                    for m in m_data
                ),
                "total_strings": sum(
                    m.get("qgis_compliance", {})
                    .get("i18n_usage", {})
                    .get("total_strings", 0)
                    for m in m_data
                ),
            },
            "gdal_style": (
                "Correct"
                if all(
                    m.get("qgis_compliance", {}).get("gdal_import_style") != "Legacy"
                    for m in m_data
                )
                else "Legacy"
            ),
            "qt_transition": {
                "pyqt5_count": sum(
                    len(
                        m.get("qgis_compliance", {})
                        .get("qt_transition", {})
                        .get("pyqt5_imports", [])
                    )
                    for m in m_data
                ),
                "pyqt6_count": sum(
                    len(
                        m.get("qgis_compliance", {})
                        .get("qt_transition", {})
                        .get("pyqt6_imports", [])
                    )
                    for m in m_data
                ),
            },
            "legacy_signals": sum(
                m.get("qgis_compliance", {}).get("signals_slots", {}).get("legacy", 0)
                for m in m_data
            ),
        }

        # Calculate overall QGIS compliance score
        score = metadata.get("compliance_score", 0) * 0.4
        if agg["processing_framework_detected"]:
            score += 20
        if agg["i18n_stats"]["total_strings"] > 0:
            i18n_ratio = (
                agg["i18n_stats"]["total_tr"] / agg["i18n_stats"]["total_strings"]
            )
            score += min(20, i18n_ratio * 40)
        if agg["gdal_style"] == "Correct":
            score += 10
        if agg["qt_transition"]["pyqt5_count"] == 0:
            score += 10

        agg["compliance_score"] = round(min(100, score), 1)
        return agg

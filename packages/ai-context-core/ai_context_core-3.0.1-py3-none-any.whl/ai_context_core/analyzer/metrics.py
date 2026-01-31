"""Project quality metrics and scoring algorithms.

Defines the logic for calculating cyclomatic distribution, overall
quality scores based on weights, and aggregated project metrics.
"""

import math
from typing import List, Dict, Any


class MetricsCalculator:
    """Namespace for core metric calculation algorithms."""

    @staticmethod
    def complexity_distribution(modules_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculates the distribution of cyclomatic complexity across modules.

        Args:
            modules_data: List of module analysis results.

        Returns:
            Dictionary with counts for low, medium, high, and very high complexity.
        """
        dist = {
            "low (0-5)": 0,
            "medium (6-15)": 0,
            "high (16-30)": 0,
            "very_high (31+)": 0,
        }
        for m in modules_data:
            c = m.get("complexity", 0)
            if c <= 5:
                dist["low (0-5)"] += 1
            elif c <= 15:
                dist["medium (6-15)"] += 1
            elif c <= 30:
                dist["high (16-30)"] += 1
            else:
                dist["very_high (31+)"] += 1
        return dist

    @staticmethod
    def maintenance_index(v: float, g: int, loc: int) -> float:
        """Calculates the Maintenance Index (MI) for a module.

        Args:
            v: Halstead Volume.
            g: Cyclomatic Complexity.
            loc: Lines of Code.

        Returns:
            A normalized score between 0 and 100.
        """
        if v <= 0 or loc <= 0:
            return 100.0
        mi = 171 - 5.2 * math.log(v) - 0.23 * g - 16.2 * math.log(loc)
        return round(max(0, min(100, (mi * 100) / 171)), 2)


class ProjectScorer:
    """Handles project quality score calculation using weighted metrics."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the scorer with configuration.

        Args:
            config: Configuration dictionary containing weights and thresholds.
        """
        self.weights = config.get("quality_weights", {})
        self.thresholds = config.get("thresholds", {})

    def calculate(
        self, modules_data: List[Dict[str, Any]], ctx: Dict[str, Any]
    ) -> float:
        """Calculates the overall project quality score.

        Args:
            modules_data: List of analyzed modules.
            ctx: Global analysis context (QGIS, Linter, etc.).

        Returns:
            Final quality score (0.0 - 100.0).
        """
        if not modules_data:
            return 0.0

        max_mod_score = (
            self.weights.get("docstrings", 15)
            + self.weights.get("complexity_low", 20)
            + self.weights.get("size_small", 15)
            + self.weights.get("has_main", 5)
            + self.weights.get("no_syntax_error", 25)
        )

        total, max_total = 0.0, len(modules_data) * max_mod_score
        for m in modules_data:
            total += self._score_module(m)

        score = (total / max_total * 100) if max_total > 0 else 0

        # Factor QGIS
        qgis_score = ctx.get("qgis_compliance", {}).get("compliance_score")
        if qgis_score is not None:
            score = (score * 0.7) + (qgis_score * 0.3)

        # Factor Linter
        linter = ctx.get("linter", {})
        if linter.get("available"):
            score = max(0, score - min(10, linter.get("errors", 0) * 0.5))

        return round(score, 1)

    def _score_module(self, m: Dict[str, Any]) -> int:
        """Scores an individual module based on quality indicators.

        Args:
            m: Module analysis data.

        Returns:
            Weighted quality score for the module.
        """
        s = 0
        if m.get("docstrings", {}).get("module"):
            s += self.weights.get("docstrings", 0)

        c = m.get("complexity", 0)
        if c <= self.thresholds.get("complexity_low", 5):
            s += self.weights.get("complexity_low", 0)
        elif c <= self.thresholds.get("complexity_medium", 10):
            s += self.weights.get("complexity_medium", 0)
        elif c <= self.thresholds.get("complexity_high", 15):
            s += self.weights.get("complexity_high", 0)

        lines = m.get("sloc", m.get("lines", 0))
        if lines <= self.thresholds.get("size_small", 200):
            s += self.weights.get("size_small", 0)
        elif lines <= self.thresholds.get("size_medium", 400):
            s += self.weights.get("size_medium", 0)

        if m.get("has_main"):
            s += self.weights.get("has_main", 0)
        if not m.get("syntax_error"):
            s += self.weights.get("no_syntax_error", 0)
        return s


def calculate_project_metrics(
    modules_data: List[Dict[str, Any]],
    entry_points: List[str],
    tests_count: int,
    config: Dict[str, Any],
    ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """Calculates general project-level metrics from analyzed modules.

    Args:
        modules_data: List of analyzed modules.
        entry_points: List of discovered entry point paths.
        tests_count: Number of test files found.
        config: Analysis configuration.
        ctx: Global context data.

    Returns:
        Dictionary of aggregated metrics.
    """
    if not modules_data:
        return {}

    total_kb = sum(m.get("file_size_kb", 0) for m in modules_data)
    total_lines = sum(m.get("sloc", m.get("lines", 0)) for m in modules_data)
    total_functions = sum(len(m.get("functions", [])) for m in modules_data)
    total_classes = sum(len(m.get("classes", [])) for m in modules_data)

    # Docs coverage
    syms, d_score = 0, 0
    for m in modules_data:
        docs = m.get("docstrings", {})
        syms += 1 + len(docs.get("classes", {})) + len(docs.get("functions", {}))
        if docs.get("module"):
            d_score += 1
        d_score += sum(1 for v in docs.get("classes", {}).values() if v)
        d_score += sum(1 for v in docs.get("functions", {}).values() if v)

    mi_list = [
        m.get("maintenance_index", 100)
        for m in modules_data
        if not m.get("syntax_error")
    ]
    complexities = [m.get("complexity", 0) for m in modules_data]

    scorer = ProjectScorer(config)

    return {
        "total_size_kb": round(total_kb, 2),
        "total_lines_code": total_lines,
        "total_physical_lines": sum(m.get("lines", 0) for m in modules_data),
        "total_functions": total_functions,
        "total_classes": total_classes,
        "avg_module_size_kb": round(total_kb / len(modules_data), 2),
        "avg_lines_per_module": round(total_lines / len(modules_data), 2),
        "docstring_coverage": round(d_score / syms * 100, 2) if syms > 0 else 0,
        "entry_points_count": len(entry_points),
        "test_files_count": tests_count,
        "average_complexity": (
            round(sum(complexities) / len(complexities), 2) if complexities else 0
        ),
        "max_complexity": max(complexities) if complexities else 0,
        "avg_maintenance_index": (
            round(sum(mi_list) / len(mi_list), 2) if mi_list else 100
        ),
        "quality_score": scorer.calculate(modules_data, ctx),
        "type_hint_coverage": round(
            sum(m.get("type_hints", {}).get("coverage", 100) for m in modules_data)
            / len(modules_data),
            2,
        ),
    }


# --- Legacy compatibility ---
def calculate_complexity_distribution(modules: List[Dict[str, Any]]) -> Dict[str, int]:
    """Categorizes modules by their cyclomatic complexity.

    Args:
        modules: List of module analysis results.

    Returns:
        Dictionary with counts for Low, Medium, High, and Critical complexity.
    """
    return MetricsCalculator.complexity_distribution(modules)


def calculate_maintenance_index(v: float, g: int, loc: int) -> float:
    """Calculates the maintenance index for a module.

    Args:
        v: Halstead volume.
        g: Cyclomatic complexity.
        loc: Lines of code.

    Returns:
        Calculated maintenance index (0-100).
    """
    return MetricsCalculator.maintenance_index(v, g, loc)


def calculate_quality_score(
    m_data: List[Dict[str, Any]], config: Dict[str, Any], project_ctx: Dict[str, Any]
) -> float:
    """Calculates the overall project quality score.

    Args:
        m_data: Module data list.
        config: Analysis configuration.
        project_ctx: Project context.

    Returns:
        The calculated quality score (0-100).
    """
    scorer = ProjectScorer(config)
    return scorer.calculate(m_data, project_ctx)

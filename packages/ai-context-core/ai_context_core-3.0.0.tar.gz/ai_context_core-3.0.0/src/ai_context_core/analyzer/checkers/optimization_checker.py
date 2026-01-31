"""Optimization opportunities checker implementation."""

from typing import List, Dict, Any
from . import BaseChecker


class OptimizationChecker(BaseChecker):
    """Checks for optimization opportunities."""

    def get_category(self) -> str:
        """Returns the category of issues this checker detects.

        Returns:
            String identifier for the category ("optimization").
        """
        return "optimization"

    def check(self, module_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Checks for code optimization opportunities.

        Analyzes cyclomatic complexity and module length to suggest
        potential refactorings.

        Args:
            module_info: Dictionary containing module analysis metrics.

        Returns:
            List of optimization suggestions.
        """
        suggestions = []

        # Get thresholds from config (injected via BaseChecker)
        thresholds = self.config.get("quality_thresholds", {})
        complexity_limit = thresholds.get("complexity", {}).get("error", 15)
        lines_limit = thresholds.get("lines", {}).get("warning", 400)

        c = module_info.get("complexity", 0)
        # Using configured complexity limit (defaulting to 15 if missing)
        if c > complexity_limit and len(module_info.get("functions", [])) > 5:
            suggestions.append(
                {
                    "type": "complexity_refactoring",
                    "priority": "high",
                    "message": "Consider breaking down large logic",
                    "severity": "low",
                }
            )

        lines_count = module_info.get("lines", 0)
        # Using configured lines limit (defaulting to 400 if missing)
        if lines_count > lines_limit:
            suggestions.append(
                {
                    "type": "module_too_large",
                    "priority": "medium",
                    "message": f"Large module ({lines_count} lines)",
                    "severity": "low",
                }
            )

        return suggestions

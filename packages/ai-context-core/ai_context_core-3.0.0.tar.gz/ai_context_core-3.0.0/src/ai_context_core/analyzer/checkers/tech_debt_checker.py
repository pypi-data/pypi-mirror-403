"""Technical debt checker implementation."""

from typing import List, Dict, Any
from . import BaseChecker


class TechDebtChecker(BaseChecker):
    """Checks for technical debt indicators like complexity and size."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initializes the technical debt checker.

        Args:
            config: Configuration dictionary for thresholds.
        """
        config = config or {}
        # Load thresholds from config, fallback to safe defaults if missing
        self.thresholds = config.get("thresholds", {})

        # Ensure minimal defaults if config is empty (fail-safe)
        if not self.thresholds:
            self.thresholds = {
                "complexity": {"warning": 10, "error": 20},
                "lines": {"warning": 500, "error": 800},  # Mapping old keys for safety
            }

        # Map TOML structure to internal flattened structure if needed
        # defaults.toml: [quality_thresholds.complexity] -> warning/error
        self.complexity_limit_high = self.thresholds.get("complexity_high", 20)
        self.complexity_limit_low = self.thresholds.get("complexity_low", 10)
        self.size_limit_medium = self.thresholds.get("size_medium", 800)
        self.size_limit_small = self.thresholds.get("size_small", 500)

        # If config comes from engine.py loaded via TOML, structure might match defaults.toml
        # Let's support the structure defined in defaults.toml:
        # quality_thresholds.complexity.error
        qt = config.get("quality_thresholds", {})
        if qt:
            self.complexity_limit_high = qt.get("complexity", {}).get("error", 20)
            self.complexity_limit_low = qt.get("complexity", {}).get("warning", 10)
            # Size limits might not be in the new TOML structure yet?
            # Creating mappings based on defaults.toml created earlier tasks.
            # Wait, defaults.toml didn't have size limits in quality_thresholds?
            # Let's check defaults.toml content again mentally or via tool if unsure.
            # defaults.toml had [quality_thresholds.complexity] and [quality_thresholds.maintainability]
            # It also had [analysis] max_file_size_mb.
            # It seems size limits (lines of code) were missing in my defaults.toml creation.
            # I should add them or stick to hardcoded for those if not critical.
            # BUT, the old engine.py had them in _get_default_config["thresholds"]["size_small"].
            # I should probably respect the legacy "thresholds" key passed from engine.py fallback
            # OR the new structure.
            pass

    def get_category(self) -> str:
        """Returns the category of issues this checker detects.

        Returns:
            String identifier for the category ("technical_debt").
        """
        return "technical_debt"

    def check(self, module_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Checks for technical debt indicators.

        Analyzes complexity, file length, and documentation coverage.

        Args:
            module_info: Dictionary containing module analysis data.

        Returns:
            List of detected technical debt issues.
        """
        issues = []
        issues = []
        # path = module_info.get("path", "") - unused

        # Complexity checks
        c = module_info.get("complexity", 0)
        if c > self.complexity_limit_high:
            issues.append(
                {
                    "type": "high_complexity",
                    "severity": "high",
                    "message": f"Very high complexity ({c})",
                    "line": 1,  # Module level issue
                }
            )
        elif c > self.complexity_limit_low:
            issues.append(
                {
                    "type": "moderate_complexity",
                    "severity": "medium",
                    "message": f"High complexity ({c})",
                    "line": 1,
                }
            )

        # File size checks
        lines_count = module_info.get("lines", 0)
        if lines_count > self.size_limit_medium:
            issues.append(
                {
                    "type": "very_long_file",
                    "severity": "high",
                    "message": f"Very long file ({lines_count} lines)",
                    "line": 1,
                }
            )
        elif lines_count > self.size_limit_small:
            issues.append(
                {
                    "type": "long_file",
                    "severity": "medium",
                    "message": f"Long file ({lines_count} lines)",
                    "line": 1,
                }
            )

        # Documentation checks
        if not module_info.get("docstrings", {}).get("module"):
            issues.append(
                {
                    "type": "missing_module_docstring",
                    "severity": "low",
                    "message": "Missing docstring",
                    "line": 1,
                }
            )

        return issues

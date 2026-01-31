"""Static analysis tools for identifying technical debt and security risks.

Includes rule-based detection for complexity hotspots, large modules,
security patterns, and optimization opportunities.

This module now uses a plugin-based system with Checkers.
"""

import ast
import pathlib
import warnings
from typing import List, Dict, Any, Type

from .checkers import BaseChecker
from .checkers.security_checker import SecurityChecker
from .checkers.tech_debt_checker import TechDebtChecker
from .checkers.optimization_checker import OptimizationChecker
from .secrets import detect_secrets
from .ast_security import ASTSecurityDetector  # noqa: F401


class IssueDetector:
    """Base class for issue detection rules (Legacy)."""

    def detect(self, **kwargs) -> List[Dict[str, Any]]:
        """Static analysis tool for identifying issues.

        Args:
            **kwargs: Analysis-specific arguments.

        Returns:
            List of detected issues.
        """
        raise NotImplementedError


# --- Checker Registry and Main Interface ---


class CheckerRegistry:
    """Registry for issue checkers."""

    _checkers: List[Type[BaseChecker]] = [
        SecurityChecker,
        TechDebtChecker,
        OptimizationChecker,
    ]

    @classmethod
    def register(cls, checker_cls: Type[BaseChecker]):
        """Registers a new checker class.

        Args:
            checker_cls: The checker class to register.
        """
        cls._checkers.append(checker_cls)

    @classmethod
    def run_all(
        cls, module_info: Dict[str, Any], config: Dict[str, Any] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Runs all registered checkers on the given module.

        Args:
            module_info: Analyzed module data.
            config: Optional configuration.

        Returns:
            Dictionary mapping category to list of found issues.
        """
        results = {}
        for checker_cls in cls._checkers:
            # Instantiate checker with configuration matching the interface
            checker = checker_cls(config)

            issues_found = checker.check(module_info)
            if issues_found:
                cat = checker.get_category()
                if cat not in results:
                    results[cat] = []
                results[cat].extend(issues_found)
        return results


# --- Public API Functions (Legacy Wrappers & New API) ---


def run_analysis(
    module_info: Dict[str, Any], config: Dict[str, Any] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Run all registered checkers on a module."""
    return CheckerRegistry.run_all(module_info, config)


def find_technical_debt(modules_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find technical debt in project modules."""
    res = []
    checker = TechDebtChecker({})
    for m in modules_data:
        issues_found = checker.check(m)
        if issues_found:
            # Calculate simplified score for legacy compatibility
            score = sum(
                3 if i["severity"] == "high" else 2 if i["severity"] == "medium" else 1
                for i in issues_found
            )
            res.append(
                {
                    "module": m["path"],
                    "issues": issues_found,
                    "total_issues": len(issues_found),
                    "severity_score": score,
                }
            )
    return sorted(res, key=lambda x: x["severity_score"], reverse=True)[:50]


def find_optimizations(modules_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find optimization opportunities in project modules."""
    res = []
    checker = OptimizationChecker()
    for m in modules_data:
        sugs = checker.check(m)
        if sugs:
            res.append({"module": m["path"], "suggestions": sugs})
    return res[:30]


def find_secrets(
    modules_data: List[Dict[str, Any]], project_path: str
) -> List[Dict[str, Any]]:
    """Scan project modules for exposed secrets."""
    res = []
    base = pathlib.Path(project_path)
    for m in modules_data:
        path = m.get("path")
        if not path:
            continue
        try:
            with open(base / path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            issues_found = detect_secrets(content)
            if issues_found:
                severities = {"critical": 4, "high": 3, "medium": 2, "low": 1}
                max_sev_score = max(
                    (severities.get(i.get("severity", "low"), 0) for i in issues_found),
                    default=0,
                )
                max_sev_label = next(
                    (k for k, v in severities.items() if v == max_sev_score), "low"
                )

                res.append(
                    {
                        "module": path,
                        "issues": issues_found,
                        "total_issues": len(issues_found),
                        "max_severity": max_sev_label,
                    }
                )
        except Exception:
            continue
    return res


def find_security_issues(
    modules_data: List[Dict[str, Any]], project_path: str
) -> List[Dict[str, Any]]:
    """Find security issues in project modules (DEPRECATED)."""
    warnings.warn(
        "find_security_issues is deprecated. Use find_secrets or AST detection.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Redirect to secrets detection as a best-effort fallback for existing consumers
    return find_secrets(modules_data, project_path)


def detect(tree: ast.AST) -> List[Dict[str, Any]]:
    """Detects security issues in the AST.

    Args:
        tree: The AST to analyze.

    Returns:
        List of detected security issues.
    """
    from .ast_security import detect_ast_security_issues as _detect_ast_security

    return _detect_ast_security(tree)


# Alias for backward compatibility (used in tests)
detect_ast_security_issues = detect

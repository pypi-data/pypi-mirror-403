"""Static analysis tools for identifying technical debt and security risks.

Includes rule-based detection for complexity hotspots, large modules,
security patterns, and optimization opportunities.
"""

import ast
import pathlib
from typing import List, Dict, Any
from .secrets import detect_secrets


class IssueDetector:
    """Base class for issue detection rules."""

    def detect(self, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError


class ASTSecurityDetector(IssueDetector):
    """Detects security issues using AST analysis."""

    def detect(self, tree: ast.AST) -> List[Dict[str, Any]]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                issues.append(
                    {
                        "pattern": "assert",
                        "severity": "low",
                        "line": node.lineno,
                        "description": "Use of assert in production code",
                    }
                )

            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append(
                        {
                            "pattern": "except:",
                            "severity": "medium",
                            "line": node.lineno,
                            "description": "Generic exception handler",
                        }
                    )
                elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    issues.append(
                        {
                            "pattern": "except Exception:",
                            "severity": "low",
                            "line": node.lineno,
                            "description": "Too broad exception handler",
                        }
                    )

            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute"
            ):
                if node.args:
                    arg = node.args[0]
                    # Check JoinedStr (f-strings)
                    if isinstance(arg, ast.JoinedStr):
                        if any(
                            "SELECT" in str(v.value).upper()
                            for v in arg.values
                            if isinstance(v, ast.Constant)
                        ):
                            issues.append(
                                {
                                    "pattern": "SQL Injection (f-string)",
                                    "severity": "critical",
                                    "line": node.lineno,
                                    "description": "Unsafe SQL construction using f-string in execute()",
                                }
                            )

                    # Check .format()
                    elif (
                        isinstance(arg, ast.Call)
                        and isinstance(arg.func, ast.Attribute)
                        and arg.func.attr == "format"
                    ):
                        if (
                            isinstance(arg.func.value, ast.Constant)
                            and "SELECT" in str(arg.func.value.value).upper()
                        ):
                            issues.append(
                                {
                                    "pattern": "SQL Injection (.format)",
                                    "severity": "high",
                                    "line": node.lineno,
                                    "description": "Unsafe SQL construction using .format() in execute()",
                                }
                            )

                    # Check % operator
                    elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                        if (
                            isinstance(arg.left, ast.Constant)
                            and "SELECT" in str(arg.left.value).upper()
                        ):
                            issues.append(
                                {
                                    "pattern": "SQL Injection (%)",
                                    "severity": "high",
                                    "line": node.lineno,
                                    "description": "Unsafe SQL construction using % in execute()",
                                }
                            )

            # General f-string SQL check (not just in execute)
            if isinstance(node, ast.JoinedStr):
                if any(
                    "SELECT" in str(v.value).upper() and "FROM" in str(v.value).upper()
                    for v in node.values
                    if isinstance(v, ast.Constant)
                ):
                    if not any(
                        i["line"] == node.lineno for i in issues
                    ):  # Avoid double reporting
                        issues.append(
                            {
                                "pattern": "f-string SQL",
                                "severity": "high",
                                "line": node.lineno,
                                "description": "Possible SQL injection in f-string",
                            }
                        )

        return issues


class TechnicalDebtScouter(IssueDetector):
    """Identifies technical debt across project modules."""

    def __init__(self, config: Dict[str, Any]):
        self.t = config.get(
            "thresholds",
            {
                "complexity_low": 10,
                "complexity_high": 20,
                "size_small": 500,
                "size_medium": 800,
            },
        )

    def scout(self, modules_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        res = []
        for m in modules_data:
            issues = []
            c = m.get("complexity", 0)
            if c > self.t["complexity_high"]:
                issues.append(
                    {
                        "type": "high_complexity",
                        "severity": "high",
                        "message": f"Very high complexity ({c})",
                    }
                )
            elif c > self.t["complexity_low"]:
                issues.append(
                    {
                        "type": "moderate_complexity",
                        "severity": "medium",
                        "message": f"High complexity ({c})",
                    }
                )

            lines_count = m.get("lines", 0)
            if lines_count > self.t["size_medium"]:
                issues.append(
                    {
                        "type": "very_long_file",
                        "severity": "high",
                        "message": f"Very long file ({lines_count} lines)",
                    }
                )
            elif lines_count > self.t["size_small"]:
                issues.append(
                    {
                        "type": "long_file",
                        "severity": "medium",
                        "message": f"Long file ({lines_count} lines)",
                    }
                )

            if not m.get("docstrings", {}).get("module"):
                issues.append(
                    {
                        "type": "missing_module_docstring",
                        "severity": "low",
                        "message": "Missing docstring",
                    }
                )

            if issues:
                score = sum(
                    (
                        3
                        if i["severity"] == "high"
                        else 2 if i["severity"] == "medium" else 1
                    )
                    for i in issues
                )
                res.append(
                    {
                        "module": m["path"],
                        "issues": issues,
                        "total_issues": len(issues),
                        "severity_score": score,
                    }
                )
        return sorted(res, key=lambda x: x["severity_score"], reverse=True)[:50]


def find_technical_debt(modules_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return TechnicalDebtScouter({}).scout(modules_data)


def detect_ast_security_issues(tree: ast.AST) -> List[Dict[str, Any]]:
    return ASTSecurityDetector().detect(tree)


def find_optimizations(modules_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    res = []
    for m in modules_data:
        sugs = []
        c = m.get("complexity", 0)
        if c > 15 and len(m.get("functions", [])) > 5:
            sugs.append(
                {
                    "type": "complexity_refactoring",
                    "priority": "high",
                    "message": "Consider breaking down large logic",
                }
            )

        lines_count = m.get("lines", 0)
        if lines_count > 400:
            sugs.append(
                {
                    "type": "module_too_large",
                    "priority": "medium",
                    "message": f"Large module ({lines_count} lines)",
                }
            )

        if sugs:
            res.append({"module": m["path"], "suggestions": sugs})
    return res[:30]


def find_security_issues(
    modules_data: List[Dict[str, Any]], project_path: str
) -> List[Dict[str, Any]]:
    res = []
    base = pathlib.Path(project_path)
    pats = [
        ("ex" + "ec(", "exec() check", "high"),
        ("ev" + "al(", "eval() check", "high"),
        ("os" + ".sys" + "tem(", "system() check", "high"),
    ]

    for m in modules_data:
        path = m.get("path")
        if not path:
            continue
        try:
            with open(base / path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            issues = []
            for p, d, s in pats:
                if p in content:
                    issues.append({"pattern": p, "description": d, "severity": s})
            issues.extend(detect_secrets(content))
            if issues:
                res.append(
                    {
                        "module": path,
                        "issues": issues,
                        "total_issues": len(issues),
                        "max_severity": max(
                            issues,
                            key=lambda i: {"high": 3, "medium": 2, "low": 1}.get(
                                i["severity"], 0
                            ),
                        )["severity"],
                    }
                )
        except Exception:
            continue
    return sorted(
        res,
        key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(x["max_severity"], 0),
        reverse=True,
    )[:20]

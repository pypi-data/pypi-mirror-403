"""Security vulnerability detection using AST analysis."""

import ast
from typing import List, Dict, Any


class IssueDetector:
    """Base class for issue detection rules."""

    def detect(self, **kwargs) -> List[Dict[str, Any]]:
        """Analyzes a node or tree and returns detected issues.

        Args:
            **kwargs: Implementation-specific arguments (usually 'tree' or 'node').

        Returns:
            A list of detected security issues.
        """
        raise NotImplementedError


class ASTSecurityDetector(IssueDetector):
    """Detects security issues using AST analysis."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize detector with configuration.

        Args:
            config: Configuration dictionary containing security patterns.
        """
        self.config = config or {}
        patterns = self.config.get("security_patterns", {})

        # Load configurable patterns or fall back to defaults
        self.dangerous_functions = set(
            patterns.get("dangerous_functions", ["exec", "eval", "__import__", "input"])
        )
        self.dangerous_modules = set(
            patterns.get("dangerous_modules", ["pickle", "marshal", "telnetlib"])
        )

    def detect(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Analyzes an AST for common security vulnerabilities.

        Checks for dangerous function calls (eval, exec), insecure subprocess usage,
        and potential SQL injection patterns.

        Args:
            tree: The AST to analyze.

        Returns:
            List of detected security issues with line numbers and severity.
        """
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

            if isinstance(node, ast.Call):
                # Check for direct dangerous calls
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.dangerous_functions:
                        issues.append(
                            {
                                "pattern": node.func.id,
                                "severity": "high",
                                "line": node.lineno,
                                "description": f"{node.func.id}() usage - potential security risk",
                            }
                        )

                # Check for attribute calls like os.system()
                elif isinstance(node.func, ast.Attribute):
                    # Check os.system
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "os"
                        and node.func.attr == "system"
                    ):
                        issues.append(
                            {
                                "pattern": "os.system",
                                "severity": "high",
                                "line": node.lineno,
                                "description": "os.system() usage - potential command injection",
                            }
                        )

                    # Check subprocess.call, subprocess.Popen
                    elif (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "subprocess"
                        and node.func.attr in ["call", "Popen", "run"]
                    ):
                        # Check if shell=True is present in keywords
                        shell_true = False
                        for keyword in node.keywords:
                            if (
                                keyword.arg == "shell"
                                and isinstance(keyword.value, ast.Constant)
                                and keyword.value.value is True
                            ):
                                shell_true = True
                                break

                        if shell_true:
                            issues.append(
                                {
                                    "pattern": f"subprocess.{node.func.attr}",
                                    "severity": "high",
                                    "line": node.lineno,
                                    "description": f"subprocess.{node.func.attr}() with shell=True - potential command injection",
                                }
                            )

                    # Insecure deserialization checks
                    elif (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id in self.dangerous_modules
                    ):
                        issues.append(
                            {
                                "pattern": f"{node.func.value.id}.{node.func.attr}",
                                "severity": "high",
                                "line": node.lineno,
                                "description": f"{node.func.value.id} usage - possible insecure deserialization",
                            }
                        )

                    # Existing SQL Injection checks
                    elif node.func.attr == "execute":
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
                            elif isinstance(arg, ast.BinOp) and isinstance(
                                arg.op, ast.Mod
                            ):
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


def detect_ast_security_issues(tree: ast.AST) -> List[Dict[str, Any]]:
    """Legacy wrapper for AST security detection.

    Args:
        tree: The AST to analyze.

    Returns:
        List of detected security issues.
    """
    return ASTSecurityDetector({}).detect(tree)

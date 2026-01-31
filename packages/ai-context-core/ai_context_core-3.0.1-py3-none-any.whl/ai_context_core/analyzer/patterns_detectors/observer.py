"""Observer pattern detector implementation."""

import ast
from typing import Dict, List, Any
from .base import PatternDetector


class ObserverDetector(PatternDetector):
    """Detects Observer pattern implementations."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Detects Observer pattern implementations in a node.

        Args:
            node: The AST node to analyze.

        Returns:
            List of detected observer instances.
        """
        self.evidence, self.confidence = [], 0
        name = getattr(node, "name", "Module")

        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    for sub in ast.walk(item):
                        if isinstance(sub, ast.Assign):
                            for t in sub.targets:
                                if isinstance(t, ast.Attribute) and any(
                                    kw in t.attr.lower()
                                    for kw in ("observers", "subscribers", "listeners")
                                ):
                                    self._add_evidence(
                                        f"Collection '{t.attr}' initialized in __init__",
                                        20,
                                    )
                                    break
                        if isinstance(sub, ast.Call):
                            # Detection of signal connections in __init__
                            try:
                                func_name = ast.unparse(sub.func).lower()
                                if ".connect" in func_name:
                                    self._add_evidence(
                                        f"Signal connection detected: {func_name}", 10
                                    )
                            except Exception:
                                pass

                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_low = item.name.lower()
                    if any(
                        kw in m_low
                        for kw in (
                            "attach",
                            "detach",
                            "subscribe",
                            "unsubscribe",
                            "register",
                            "unregister",
                        )
                    ):
                        self._add_evidence(
                            f"Management method '{item.name}' detected", 15
                        )
                    if any(kw in m_low for kw in ("notify", "emit", "broadcast")):
                        self._add_evidence(
                            f"Notification method '{item.name}' detected", 15
                        )
                        for sub in ast.walk(item):
                            if isinstance(sub, ast.For) and any(
                                kw in ast.unparse(sub.iter).lower()
                                for kw in ("observers", "subscribers", "listeners")
                            ):
                                self._add_evidence(
                                    "Notification method iterates over collection", 30
                                )
                                break

        # Module level or class level pyqtSignal detection
        if isinstance(node, (ast.ClassDef, ast.Module)):
            signals_found = 0
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.Assign, ast.AnnAssign)):
                    val = item.value if isinstance(item, ast.Assign) else item.value
                    if val and isinstance(val, ast.Call):
                        try:
                            func_str = ast.unparse(val.func).lower()
                            if "pyqtsignal" in func_str or "signal" in func_str:
                                signals_found += 1
                        except Exception:
                            pass

            if signals_found > 0:
                self._add_evidence(
                    f"Detected {signals_found} signals (PyQt/Signals)",
                    signals_found * 20,
                )

        if self.confidence >= 50:
            return [
                {
                    "class": name,
                    "confidence": min(self.confidence, 100),
                    "evidence": self.evidence,
                }
            ]
        return []

"""Design patterns detection module for ai-context-core.

Uses AST to identify common architectural patterns through a class-based detection system.
"""

import ast
from typing import Dict, List, Any


class PatternDetector:
    """Base class for design pattern detectors."""

    def __init__(self):
        self.evidence = []
        self.confidence = 0

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        """Analyzes a node and returns detected pattern instances."""
        raise NotImplementedError

    def _add_evidence(self, msg: str, weight: int):
        self.evidence.append(msg)
        self.confidence += weight


class SingletonDetector(PatternDetector):
    """Detects Singleton pattern implementations."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        if not isinstance(node, ast.ClassDef):
            return []
        self.evidence, self.confidence = [], 0

        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__new__":
                self._add_evidence("Overrides __new__ to control instantiation", 60)

            if isinstance(item, ast.FunctionDef):
                is_static = any(
                    isinstance(d, (ast.Name, ast.Attribute))
                    and (
                        getattr(d, "id", "") in ("classmethod", "staticmethod")
                        or getattr(d, "attr", "") in ("classmethod", "staticmethod")
                    )
                    for d in item.decorator_list
                )
                if is_static and any(
                    k in item.name.lower()
                    for k in ("instance", "singleton", "get_inst")
                ):
                    self._add_evidence(
                        f"Static/Class method '{item.name}' detected", 30
                    )

            if isinstance(item, (ast.Assign, ast.AnnAssign)):
                targets = (
                    item.targets if isinstance(item, ast.Assign) else [item.target]
                )
                for t in targets:
                    if isinstance(t, ast.Name) and any(
                        k in t.id.lower() for k in ("instance", "_inst")
                    ):
                        self._add_evidence(
                            f"Static instance variable '{t.id}' found", 20
                        )

        if self.confidence >= 50:
            return [
                {
                    "class": node.name,
                    "confidence": min(self.confidence, 100),
                    "evidence": self.evidence,
                }
            ]
        return []


class FactoryDetector(PatternDetector):
    """Detects Factory pattern implementations."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        if not isinstance(node, ast.ClassDef):
            return []
        res = []
        base_conf = 30 if "factory" in node.name.lower() else 0

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.evidence, self.confidence = [], base_conf
                if base_conf:
                    self.evidence.append(
                        f"Class '{node.name}' contains 'Factory' in name"
                    )

                if any(
                    p in item.name.lower()
                    for p in ("create_", "build_", "make_", "factory")
                ):
                    self._add_evidence(
                        f"Method '{item.name}' matches factory naming", 40
                    )

                for sub in ast.walk(item):
                    if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Call):
                        self._add_evidence(
                            "Method instantiates and returns an object", 30
                        )
                        break

                if self.confidence >= 60:
                    res.append(
                        {
                            "class": node.name,
                            "method": item.name,
                            "confidence": min(self.confidence, 100),
                            "evidence": self.evidence,
                        }
                    )
        return res


class ObserverDetector(PatternDetector):
    """Detects Observer pattern implementations."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        if not isinstance(node, ast.ClassDef):
            return []
        self.evidence, self.confidence = [], 0

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
                                    f"Collection '{t.attr}' initialized in __init__", 20
                                )
                                break

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
                    self._add_evidence(f"Management method '{item.name}' detected", 15)
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

        if self.confidence >= 50:
            return [
                {
                    "class": node.name,
                    "confidence": min(self.confidence, 100),
                    "evidence": self.evidence,
                }
            ]
        return []


class StrategyDetector(PatternDetector):
    """Detects Strategy pattern implementations."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        if not isinstance(node, ast.ClassDef):
            return []
        self.evidence, self.confidence = [], 0
        has_inj = False

        for item in node.body:
            if isinstance(item, ast.FunctionDef) and (
                item.name == "__init__" or "set_" in item.name
            ):
                for arg in item.args.args:
                    if any(
                        kw in arg.arg.lower()
                        for kw in ("strategy", "algorithm", "engine", "handler", "mode")
                    ):
                        has_inj = True
                        self._add_evidence(
                            f"Injection detected in '{item.name}' via '{arg.arg}'", 30
                        )
                        break

        if has_inj:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name not in (
                    "__init__",
                    "set_",
                ):
                    for sub in ast.walk(item):
                        if isinstance(sub, ast.Call) and isinstance(
                            sub.func, ast.Attribute
                        ):
                            if any(
                                kw in ast.unparse(sub.func).lower()
                                for kw in ("strategy", "algorithm", "engine", "handler")
                            ):
                                self._add_evidence(
                                    f"Strategy call in '{item.name}': {ast.unparse(sub.func)}()",
                                    40,
                                )
                                break

        if self.confidence >= 50:
            return [
                {
                    "class": node.name,
                    "confidence": min(self.confidence, 100),
                    "evidence": self.evidence,
                }
            ]
        return []


class DecoratorDetector(PatternDetector):
    """Detects Decorator pattern implementations."""

    def detect(self, node: ast.AST) -> List[Dict[str, Any]]:
        res = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.evidence, self.confidence = [], 0
            inner = next(
                (
                    i
                    for i in node.body
                    if isinstance(i, (ast.FunctionDef, ast.AsyncFunctionDef))
                ),
                None,
            )
            if inner:
                if any(
                    isinstance(i, ast.Return)
                    and isinstance(i.value, ast.Name)
                    and i.value.id == inner.name
                    for i in node.body
                ):
                    self._add_evidence(
                        f"Function contains and returns inner '{inner.name}'", 50
                    )
                    if any(
                        isinstance(d, ast.Call)
                        and (
                            getattr(d.func, "attr", "") == "wraps"
                            or getattr(d.func, "id", "") == "wraps"
                        )
                        for d in inner.decorator_list
                    ):
                        self._add_evidence("Uses @functools.wraps", 40)
            if self.confidence >= 50:
                res.append(
                    {
                        "name": node.name,
                        "type": "function",
                        "confidence": min(self.confidence, 100),
                        "evidence": self.evidence,
                    }
                )

        elif isinstance(node, ast.ClassDef):
            self.evidence, self.confidence = [], 0
            names = {i.name for i in node.body if isinstance(i, ast.FunctionDef)}
            if "__init__" in names and "__call__" in names:
                self._add_evidence("Class implements both __init__ and __call__", 60)
            if self.confidence >= 50:
                res.append(
                    {
                        "name": node.name,
                        "type": "class",
                        "confidence": min(self.confidence, 100),
                        "evidence": self.evidence,
                    }
                )
        return res


def detect_patterns(tree: ast.AST) -> Dict[str, Any]:
    """Analyzes an AST to detect common design patterns using specialized detectors."""
    detectors = {
        "Singleton": SingletonDetector(),
        "Factory": FactoryDetector(),
        "Observer": ObserverDetector(),
        "Strategy": StrategyDetector(),
        "Decorator": DecoratorDetector(),
    }
    results = {}

    for node in ast.walk(tree):
        for name, det in detectors.items():
            found = det.detect(node)
            if found:
                if name not in results:
                    results[name] = []
                results[name].extend(found)
    return results


# --- Legacy Compatibility Wrappers ---


def detect_singleton(tree: ast.AST) -> List[Dict[str, Any]]:
    det = SingletonDetector()
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res


def detect_factory(tree: ast.AST) -> List[Dict[str, Any]]:
    det = FactoryDetector()
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res


def detect_observer(tree: ast.AST) -> List[Dict[str, Any]]:
    det = ObserverDetector()
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res


def detect_strategy(tree: ast.AST) -> List[Dict[str, Any]]:
    det = StrategyDetector()
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res


def detect_decorator(tree: ast.AST) -> List[Dict[str, Any]]:
    det = DecoratorDetector()
    res = []
    for node in ast.walk(tree):
        res.extend(det.detect(node))
    return res

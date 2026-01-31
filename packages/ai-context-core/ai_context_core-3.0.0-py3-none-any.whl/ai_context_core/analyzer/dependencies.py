"""Dependency analysis module for Python projects."""

from typing import Dict, Any, List, Set, Callable
import sys
import logging
from pathlib import Path
from . import graph_engine

logger = logging.getLogger(__name__)


# Get standard library modules dynamically (Python 3.10+)
# Fallback for older python versions if needed, though project requires >=3.9
if sys.version_info >= (3, 10):
    STDLIB_MODULES = sys.stdlib_module_names
else:
    # Minimal fallback or rely on isort/stdlib-list if installed,
    # but for zero-deps we keep a larger hardcoded list or just accept imperfection on <3.10
    # Extending the previous list slightly for better coverage on 3.9
    STDLIB_MODULES = {
        "abc",
        "argparse",
        "ast",
        "asyncio",
        "base64",
        "collections",
        "concurrent",
        "contextlib",
        "copy",
        "csv",
        "datetime",
        "decimal",
        "email",
        "enum",
        "functools",
        "hashlib",
        "html",
        "http",
        "importlib",
        "inspect",
        "io",
        "itertools",
        "json",
        "logging",
        "math",
        "multiprocessing",
        "os",
        "pathlib",
        "pickle",
        "platform",
        "random",
        "re",
        "shutil",
        "socket",
        "sqlite3",
        "statistics",
        "subprocess",
        "sys",
        "tempfile",
        "threading",
        "time",
        "traceback",
        "typing",
        "unittest",
        "urllib",
        "uuid",
        "warnings",
        "xml",
        "zipfile",
    }

DEPENDENCY_FILES = [
    "requirements.txt",
    "setup.py",
    "pyproject.toml",
    "Pipfile",
    "setup.cfg",
    "environment.yml",
]


def analyze_dependencies(
    modules_data: List[Dict[str, Any]], project_path: Path, read_file_func: Callable
) -> Dict[str, Any]:
    """Analyzes project dependencies, builds the import graph, and detects circularities."""
    dependencies = {
        "internal": [],
        "external": [],
        "third_party": [],
        "files": {},
        "import_graph": {},
        "circular_dependencies": [],
        "graph_metrics": {},
    }

    # 1. Parse common dependency files
    dependencies["files"] = _parse_dependency_files(project_path, read_file_func)

    # 2. Build import graph and identify internal modules
    builder = graph_engine.ImportGraphBuilder(modules_data)
    import_graph = builder.build()
    dependencies["import_graph"] = {k: list(v) for k, v in import_graph.items()}

    # Store known internal module names for classification
    known_internal = builder.known_internal_modules

    # 3. Detect circular dependencies
    try:
        detector = graph_engine.CycleDetector(import_graph, limit=5)
        cycles = detector.find_cycles()
        if cycles:
            dependencies["circular_dependencies"] = cycles
    except Exception:
        pass

    # 4. Calculate graph metrics
    metrics_calc = graph_engine.GraphMetricsCalculator(import_graph)
    try:
        num_edges = metrics_calc.count_edges()
        dependencies["graph_metrics"] = {
            "nodes": len(import_graph),
            "edges": num_edges,
            "density": metrics_calc.calculate_density(num_edges),
            "is_dag": len(
                graph_engine.CycleDetector(import_graph, limit=1).find_cycles()
            )
            == 0,
            "weakly_connected_components": metrics_calc.count_connected_components(),
        }
        dependencies["coupling_metrics"] = metrics_calc.calculate_coupling_metrics()
    except Exception as e:
        logger.exception(f"Error calculating graph metrics: {e}")

    # 5. Collect unused imports
    unused_imports = {}
    for mod in modules_data:
        if mod.get("unused_imports"):
            unused_imports[mod["path"]] = mod["unused_imports"]
    dependencies["unused_imports"] = unused_imports

    # 6. Classify imports
    all_imports = set()
    for module in modules_data:
        all_imports.update(module.get("imports", []))

    classified = _classify_imports(all_imports, known_internal)
    dependencies.update(classified)

    return dependencies


def _parse_dependency_files(
    project_path: Path, read_file_func: Callable
) -> Dict[str, str]:
    """Read content from common dependency files.

    Args:
        project_path: Path to the project root.
        read_file_func: Function to read file content.

    Returns:
        Dictionary mapping filename to its content.
    """
    files_content = {}
    for req_file in DEPENDENCY_FILES:
        path = project_path / req_file
        if path.exists():
            try:
                content = read_file_func(path)
                if content:
                    files_content[req_file] = content[:2000]
            except Exception:
                pass
    return files_content


def _classify_imports(
    all_imports: Set[str], known_internal: Set[str] = None
) -> Dict[str, List[str]]:
    """Categorizes imports into internal, external (StdLib), and third-party modules.

    Args:
        all_imports: Set of all import strings found in the project.
        known_internal: Set of known internal module names (optional).

    """
    results = {"internal": [], "external": [], "third_party": []}
    known_internal = known_internal or set()

    for imp in sorted(all_imports):
        root_pkg = imp.split(".")[0]

        # Check for explicitly known internal modules
        is_known_internal = False
        if imp in known_internal:
            is_known_internal = True
        else:
            # Check prefixes (e.g., if 'my_pkg.utils' is known, 'my_pkg' should be internal too?)
            # Actually, reverse: if 'my_pkg' is in known_internal, 'my_pkg.utils' is internal.
            # But known_internal usually contains full paths 'my_pkg.utils'.
            # We need to check if 'imp' or any parent is in known_internal.
            # A simpler heuristic for this step: check if root package matches any known internal root
            for internal in known_internal:
                if imp == internal or imp.startswith(internal + "."):
                    is_known_internal = True
                    break

        if (
            is_known_internal
            or imp.startswith(".")
            or any(seg in imp for seg in ["..", "./"])
        ):
            results["internal"].append(imp)
        elif root_pkg in STDLIB_MODULES:
            results["external"].append(imp)
        else:
            results["third_party"].append(imp)

    return results


# Re-export legacy functions if needed for API compatibility,
# although they are now mostly handled by classes internally.
# Exposing them as simple wrappers just in case.


def count_edges(import_graph: Dict[str, Set[str]]) -> int:
    """Count total edges in the graph (Legacy wrapper).

    Args:
        import_graph: The import graph dictionary.

    Returns:
        Total number of edges.
    """
    return graph_engine.GraphMetricsCalculator(import_graph).count_edges()


def find_simple_cycles(
    import_graph: Dict[str, Set[str]], limit: int = 5
) -> List[List[str]]:
    """Find simple cycles in the graph (Legacy wrapper)."""
    return graph_engine.CycleDetector(import_graph, limit).find_cycles()


def count_connected_components(import_graph: Dict[str, Set[str]]) -> int:
    """Count connected components (Legacy wrapper)."""
    return graph_engine.GraphMetricsCalculator(
        import_graph
    ).count_connected_components()


def calculate_coupling_metrics(
    import_graph: Dict[str, Set[str]],
) -> Dict[str, Dict[str, int]]:
    """Calculate coupling metrics (Legacy wrapper)."""
    return graph_engine.GraphMetricsCalculator(
        import_graph
    ).calculate_coupling_metrics()


class DependencyAnalyzer:
    """Legacy wrapper for dependency analysis."""

    def __init__(self, project_path: Path):
        """Initialize the legacy analyzer.

        Args:
            project_path: Path to the project root.
        """
        self.project_path = project_path

    def build_graph(self, modules_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build the dependency graph for the project."""

        def _read_file(p: Path) -> str:
            """Reads a file content safely.

            Args:
                p: Path to the file.

            Returns:
                The file content.
            """
            return p.read_text(errors="ignore")

        return analyze_dependencies(modules_data, self.project_path, _read_file)


def detect_unused_imports_in_project(
    modules_data: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Collects unused imports across all modules."""
    unused = {}
    for mod in modules_data:
        if mod.get("unused_imports"):
            unused[mod["path"]] = mod["unused_imports"]
    return unused

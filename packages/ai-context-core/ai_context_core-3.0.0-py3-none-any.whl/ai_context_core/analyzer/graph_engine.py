"""Internal engine for building and analyzing dependency graphs.

Extracted from dependencies.py to improve modularity and reduce file size.
"""

import logging
from typing import Dict, Any, List, Set, Optional

logger = logging.getLogger(__name__)


class ImportGraphBuilder:
    """Class responsible for building the internal import graph of the project."""

    def __init__(self, modules_data: List[Dict[str, Any]]):
        """Initialize the builder with module data."""
        self.modules_data = modules_data
        self.import_graph = {}
        self.import_map = {}
        self.known_internal_modules = set()

    def build(self) -> Dict[str, Set[str]]:
        """Build and return the import graph."""
        self._initialize_graph()
        self._resolve_imports()
        return self.import_graph

    def _initialize_graph(self):
        """Initialize graph nodes and populate import map."""
        for mod in self.modules_data:
            path = mod.get("path", "")
            if not path:
                continue

            if path not in self.import_graph:
                self.import_graph[path] = set()

            importable = self._add_to_import_map(path)
            if importable:
                self.known_internal_modules.add(importable)

    def _add_to_import_map(self, path: str) -> Optional[str]:
        """Map importable python paths to file paths.

        Args:
            path: Relative file path of the module.

        Returns:
            The importable python path (e.g., 'pkg.mod') if successful.
        """
        clean_path = path.replace("\\", "/")
        if clean_path.startswith("src/"):
            clean_path = clean_path[4:]

        importable = clean_path.replace(".py", "").replace("/", ".")
        if importable.endswith(".__init__"):
            importable = importable[:-9]

        self.import_map[importable] = path
        return importable

    def _resolve_imports(self):
        """Iterate through modules and resolve their imports to project files."""
        for module in self.modules_data:
            source_path = module.get("path", "")
            if not source_path:
                continue

            for imp in module.get("imports", []):
                target = self._resolve_single_import(imp)
                if target and target != source_path:
                    self.import_graph[source_path].add(target)

    def _resolve_single_import(self, imp: str) -> Optional[str]:
        """Resolve a single import string to a file path.

        Args:
            imp: Import string (e.g., 'pkg.mod').

        Returns:
            Resolved file path or None if not found in project.
        """
        if imp in self.import_map:
            return self.import_map[imp]

        if "." in imp:
            parts = imp.split(".")
            for i in range(len(parts), 0, -1):
                prefix = ".".join(parts[:i])
                if prefix in self.import_map:
                    return self.import_map[prefix]
        return None


class CycleDetector:
    """Class responsible for detecting cycles in the graph."""

    def __init__(self, graph: Dict[str, Set[str]], limit: int = 5):
        """Initialize the cycle detector.

        Args:
            graph: Dependency graph (adj. list of module paths).
            limit: Maximum number of cycles to detect.
        """
        self.graph = graph
        self.limit = limit
        self.cycles = []
        self.visited = set()
        self.path = []
        self.path_set = set()

    def find_cycles(self) -> List[List[str]]:
        """Find simple cycles in the graph up to the configured limit."""
        for node in list(self.graph.keys()):
            if node not in self.visited:
                self._dfs(node)
        return self.cycles

    def _dfs(self, u: str):
        """Perform recursive DFS to detect cycles."""
        if len(self.cycles) >= self.limit:
            return

        self.visited.add(u)
        self.path.append(u)
        self.path_set.add(u)

        if u in self.graph:
            for v in self.graph[u]:
                if v in self.path_set:
                    cycle_start = self.path.index(v)
                    self.cycles.append(self.path[cycle_start:])
                elif v not in self.visited:
                    self._dfs(v)

        self.path_set.remove(u)
        self.path.pop()


class GraphMetricsCalculator:
    """Class to calculate various graph metrics."""

    def __init__(self, import_graph: Dict[str, Set[str]]):
        """Initialize the graph metrics calculator.

        Args:
            import_graph: Project dependency graph.
        """
        self.graph = import_graph
        self.num_nodes = len(import_graph)

    def count_edges(self) -> int:
        """Count total edges in the graph.

        Returns:
            Total count of directed edges.
        """
        return sum(len(neighbors) for neighbors in self.graph.values())

    def calculate_density(self, num_edges: int) -> float:
        """Calculate graph density.

        Args:
            num_edges: Total number of edges in the graph.

        Returns:
            Density value (edges / max_possible_edges).
        """
        max_edges = self.num_nodes * (self.num_nodes - 1)
        return num_edges / max_edges if max_edges > 0 else 0

    def count_connected_components(self) -> int:
        """Count weakly connected components in the graph.

        Returns:
            Number of weakly connected components.
        """
        undirected = {}
        for u, neighbors in self.graph.items():
            if u not in undirected:
                undirected[u] = set()
            for v in neighbors:
                undirected[u].add(v)
                if v not in undirected:
                    undirected[v] = set()
                undirected[v].add(u)

        visited = set()
        count = 0
        for node in undirected:
            if node not in visited:
                count += 1
                self._bfs_visit(node, visited, undirected)
        return count

    def _bfs_visit(
        self, start_node: str, visited: Set[str], undirected: Dict[str, Set[str]]
    ):
        """Perform BFS traversal for component counting."""
        queue = [start_node]
        visited.add(start_node)
        while queue:
            curr = queue.pop(0)
            for neighbor in undirected.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

    def calculate_coupling_metrics(self) -> Dict[str, Dict[str, int]]:
        """Calculate Fan-In, Fan-Out, and CBO for each node.

        Returns:
            Dictionary mapping node paths to their coupling metrics.
        """
        metrics = {}
        all_nodes = set(self.graph.keys())
        for neighbors in self.graph.values():
            all_nodes.update(neighbors)

        fan_in = {node: 0 for node in all_nodes}
        fan_out = {node: 0 for node in all_nodes}

        for u, neighbors in self.graph.items():
            fan_out[u] = len(neighbors)
            for v in neighbors:
                fan_in[v] += 1

        for node in all_nodes:
            metrics[node] = {
                "fan_in": fan_in[node],
                "fan_out": fan_out[node],
                "cbo": fan_in[node] + fan_out[node],
            }
        return metrics

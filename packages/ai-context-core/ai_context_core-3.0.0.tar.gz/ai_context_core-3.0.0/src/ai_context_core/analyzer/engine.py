"""Main orchestration engine for project analysis.

The ProjectAnalyzer coordinates the analysis of multiple Python modules,
aggregating results from AST analysis, dependency checking, and issue detection.
"""

import logging
import time
import ast
import concurrent.futures
import pathlib
import json
from typing import Dict, Any, List, Optional
from . import (
    ast_utils,
    fs_utils,
    metrics,
    issues,
    reporting,
    dependencies,
    antipatterns,
    patterns,
    git_analysis,
    aggregator,
)
from .constants import PARALLEL_MIN_FILES
from ..context.manager import AIContextManager

logger = logging.getLogger(__name__)


try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def load_config(root_path: pathlib.Path) -> Dict[str, Any]:
    """Load configuration from defaults.toml and optional project overrides.

    Adheres to zero-dependency policy by using stdlib tomllib (Py3.11+)
    or optional tomli. If neither is available, falls back to hardcoded defaults.

    Args:
        root_path: Project root path to look for override config.

    Return:
        Merged configuration dictionary.

    """
    # Load defaults from package
    default_config = {}
    if tomllib:
        try:
            defaults_path = (
                pathlib.Path(__file__).parent / ".." / "config" / "defaults.toml"
            )
            if defaults_path.exists():
                with open(defaults_path, "rb") as f:
                    default_config = tomllib.load(f)
        except Exception as e:
            logger.warning(f"Failed to load defaults.toml: {e}")

    if not default_config:
        # Fallback if TOML parsing fails or fails to load
        return _get_hardcoded_defaults()

    # Load overrides from project
    override_config = {}
    if tomllib:
        try:
            project_config_path = root_path / ".ai-context" / "config.toml"
            if project_config_path.exists():
                with open(project_config_path, "rb") as f:
                    override_config = tomllib.load(f)
        except Exception as e:
            logger.warning(f"Failed to load project config.toml: {e}")

    # Merge configs (shallow merge for now, or recursive if needed)
    # Simple recursive merge for top-level keys
    final_config = default_config.copy()
    for section, values in override_config.items():
        if isinstance(values, dict) and section in final_config:
            final_config[section].update(values)
        else:
            final_config[section] = values

    return final_config


def _get_hardcoded_defaults() -> Dict[str, Any]:
    """Return fallback hardcoded configuration.

    Returns:
        Dictionary with default quality weights and thresholds.
    """
    return {
        "quality_weights": {
            "docstrings": 30,
            "complexity_low": 20,
            "size_small": 15,
            "has_main": 5,
            "no_syntax_error": 30,
            "complexity_medium": 10,
            "complexity_high": -10,
            "size_medium": 10,
        },
        "thresholds": {
            "complexity_low": 5,
            "complexity_medium": 15,
            "complexity_high": 25,
            "size_small": 200,
            "size_medium": 500,
        },
    }


class ProjectAnalyzer:
    """Optimized and modular Python project analyzer."""

    def __init__(
        self,
        project_path: str,
        config: Optional[Dict[str, Any]] = None,
        max_workers: Optional[int] = None,
        exclude_patterns: Optional[List[str]] = None,
        ignore_cache: bool = False,
    ):
        """Initialize the analyzer with project settings.

        Args:
            project_path: Absolute or relative path to the project root.
            config: Optional configuration dictionary. If None, loads from defaults.
            max_workers: Maximum number of parallel workers for analysis.
            exclude_patterns: List of glob patterns to exclude from scanning.
            ignore_cache: Whether to force a full analysis ignoring existing cache.
        """
        self.project_path = pathlib.Path(project_path).resolve()
        self.max_workers = max_workers or (
            2 * (4 if hasattr(time, "get_clock_info") else 1)
        )
        # Load config from file if not provided explicitly
        self.config = config or load_config(self.project_path)

        self.exclusion_patterns = fs_utils.load_exclusion_patterns(
            self.project_path, exclude_patterns
        )
        self.context_manager = AIContextManager(project_path)
        self.analysis_cache = (
            {} if ignore_cache else fs_utils.load_cache(self.project_path)
        )
        self.error_log = {}

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration. Deprecated: Use load_config."""
        return _get_hardcoded_defaults()

    def analyze(self, output_format: str = "markdown") -> Dict[str, Any]:
        """Execute the complete project analysis pipeline.

        Orchestrates scanning, parallel module analysis, dependency graph building,
        git evolution tracking, and results aggregation.

        Args:
            output_format: Desired report format ('markdown' or 'html').

        Returns:
            A comprehensive dictionary containing all analysis results.
        """
        start_time = time.time()
        logger.info(f"Starting analysis for {self.project_path}")

        # 1. Scanning and Parallel Analysis
        scan_res = fs_utils.scan_project(self.project_path, self.exclusion_patterns)
        modules_data = self._analyze_modules_parallel(scan_res.python_files)

        # 2. Dependency Analysis
        dep_analyzer = dependencies.DependencyAnalyzer(self.project_path)
        graph_data = dep_analyzer.build_graph(modules_data)

        # 3. Evolution analysis (Git)
        git_data = git_analysis.analyze_git_evolution(self.project_path)

        # 4. Aggregate results
        qgis_metadata = fs_utils.parse_qgis_metadata(self.project_path)
        agg = aggregator.ResultsAggregator(self.project_path, self.config)
        results = agg.aggregate(modules_data, graph_data, git_data, qgis_metadata)

        # Add tree structure and manual notes
        results["structure"] = {
            "tree": fs_utils.generate_tree_optimized(self.project_path),
            "modules_count": len(modules_data),
            "file_types": scan_res.file_types,
            "size_stats": scan_res.size_stats,
        }
        results["manual_notes"] = self._read_manual_notes()

        # 5. Finalization
        self._generate_outputs(results, output_format)
        fs_utils.save_cache(self.project_path, self.analysis_cache)

        logger.info(f"Analysis completed in {time.time() - start_time:.2f}s")
        return results

    def _read_manual_notes(self) -> str:
        """Read manual architecture notes if they exist.

        Looks for architecture_notes.md or project_brain.md in .ai-context directory.

        Returns:
            The content of the notes file if found, otherwise an empty string.
        """
        notes_path = self.project_path / ".ai-context" / "architecture_notes.md"
        if not notes_path.exists():
            # Try legacy or alternative name
            notes_path = self.project_path / ".ai-context" / "project_brain.md"

        if notes_path.exists():
            try:
                return notes_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not read manual notes: {e}")
        return ""

    def _analyze_modules_parallel(
        self, files: List[pathlib.Path]
    ) -> List[Dict[str, Any]]:
        """Analyze modules in parallel using process pool.

        Uses cached results if hashes match, otherwise submits to worker pool.

        Args:
            files: List of file paths to analyze.

        Returns:
            List of dictionaries containing individual module analysis data.
        """
        results, to_analyze = [], []
        for f in files:
            rel = str(f.relative_to(self.project_path))
            h = fs_utils.calculate_file_hash(f)
            cached = self.analysis_cache.get(rel)
            if cached and cached.get("hash") == h:
                results.append(cached["data"])
            else:
                to_analyze.append(f)

        if not to_analyze:
            return results

        # Optimization: Sequential execution for small projects
        if len(to_analyze) < PARALLEL_MIN_FILES:
            logger.info(f"Analyzing {len(to_analyze)} modules sequentially...")
            for f in to_analyze:
                data = self._analyze_single_module(f)
                if data:
                    results.append(data)
                    self.analysis_cache[str(f.relative_to(self.project_path))] = {
                        "hash": fs_utils.calculate_file_hash(f),
                        "data": data,
                        "timestamp": time.time(),
                    }
            return results

        logger.info(f"Analyzing {len(to_analyze)} modules in parallel...")
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers
        ) as exc:
            futures = {
                exc.submit(self._analyze_single_module, f): f for f in to_analyze
            }
            for fut in concurrent.futures.as_completed(futures):
                f = futures[fut]
                try:
                    data = fut.result()
                    if data:
                        results.append(data)
                        self.analysis_cache[str(f.relative_to(self.project_path))] = {
                            "hash": fs_utils.calculate_file_hash(f),
                            "data": data,
                            "timestamp": time.time(),
                        }
                except Exception as e:
                    logger.error(f"Error analyzing {f}: {e}")
                    self.error_log[str(f)] = str(e)
        return results

    def _analyze_single_module(self, file_path: pathlib.Path) -> Dict[str, Any]:
        """Analyze a single module's content and metrics.

        Performs AST parsing and runs multiple internal detectors.

        Args:
            file_path: Absolute path to the module file.

        Returns:
            Dictionary with module metrics (LOC, complexity, imports, etc.).
        """
        try:
            content = fs_utils.read_file_fast(file_path)
            if not content:
                return {}
            tree = ast.parse(content)
            entry_data = ast_utils.is_entry_point(tree)
            complexity = ast_utils.calculate_complexity(tree)
            halstead = ast_utils.calculate_halstead_metrics(tree)
            sloc = ast_utils.calculate_sloc(tree, content)
            line_count = len(content.splitlines())

            return {
                "path": str(file_path.relative_to(self.project_path)),
                "lines": line_count,
                "sloc": sloc,
                "file_size_kb": file_path.stat().st_size / 1024,
                "complexity": complexity,
                "imports": ast_utils.extract_imports(tree),
                "classes": ast_utils.extract_classes(tree),
                "functions": ast_utils.extract_functions(tree),
                "docstrings": ast_utils.check_docstrings(tree),
                "entry_point_info": entry_data,
                "has_main": entry_data["is_entry_point"],
                "type_hints": ast_utils.calculate_type_hint_coverage(tree),
                "halstead": halstead,
                "antipatterns": self._detect_antipatterns(tree),
                "ast_security": issues.detect(tree),
                "patterns": patterns.detect_patterns(tree),
                "unused_imports": ast_utils.detect_unused_imports(tree),
                "maintenance_index": metrics.calculate_maintenance_index(
                    halstead["volume"], complexity, sloc
                ),
                "qgis_compliance": ast_utils.check_qgis_compliance(tree),
                "syntax_error": False,
            }
        except Exception as e:
            return {
                "path": str(file_path.relative_to(self.project_path)),
                "syntax_error": True,
                "error": str(e),
            }

    def _detect_antipatterns(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Run all antipattern detectors on the AST.

        Args:
            tree: The parsed AST of the module.

        Returns:
            List of detected anti-patterns with details.
        """
        return (
            antipatterns.detect_god_object(tree)
            + antipatterns.detect_spaghetti_code(tree)
            + antipatterns.detect_magic_numbers(tree)
            + antipatterns.detect_dead_code(tree)
        )

    def _generate_outputs(self, results: Dict[str, Any], fmt: str):
        """Generate final report files based on analysis results.

        Creates PROJECT_SUMMARY and AI_CONTEXT files.

        Args:
            results: The aggregated analysis data.
            fmt: Output format for the summary ('markdown' or 'html').
        """
        try:
            ext = ".html" if fmt == "html" else ".md"
            reporting.generate_project_summary(
                results,
                self.project_path / f"PROJECT_SUMMARY{ext}",
                self.project_path.name,
                format=fmt,
            )
            reporting.generate_ai_context(
                results, self.project_path / "AI_CONTEXT.md", self.project_path.name
            )
            with open(
                self.project_path / "project_context.json", "w", encoding="utf-8"
            ) as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error generating outputs: {e}")

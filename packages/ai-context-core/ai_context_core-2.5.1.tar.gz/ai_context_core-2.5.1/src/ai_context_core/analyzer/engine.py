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
    ai_recommendations,
)
from ..context.manager import AIContextManager

logger = logging.getLogger(__name__)

PARALLEL_MIN_FILES = 5  # Minimum files to trigger multiprocessing overhead


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
        self.project_path = pathlib.Path(project_path).resolve()
        self.max_workers = max_workers or (
            2 * (4 if hasattr(time, "get_clock_info") else 1)
        )
        self.config = config or self._get_default_config()
        self.exclusion_patterns = fs_utils.load_exclusion_patterns(
            self.project_path, exclude_patterns
        )
        self.context_manager = AIContextManager(project_path)
        self.analysis_cache = {} if ignore_cache else fs_utils.load_cache(self.project_path)
        self.error_log = {}

    def _get_default_config(self) -> Dict[str, Any]:
        """Returns default configuration values for metrics and thresholds."""
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

    def analyze(self, output_format: str = "markdown") -> Dict[str, Any]:
        """Executes the complete project analysis pipeline."""
        start_time = time.time()
        logger.info(f"Starting analysis for {self.project_path}")

        # 1. Pipeline Execution
        data = self._execute_pipeline()

        # 2. Results Aggregation
        results = self._aggregate_all(data)

        # 3. Finalization
        self._generate_outputs(results, output_format)
        fs_utils.save_cache(self.project_path, self.analysis_cache)

        logger.info(f"Analysis completed in {time.time() - start_time:.2f}s")
        return results

    def _execute_pipeline(self) -> Dict[str, Any]:
        """Runs the sequential analysis steps."""
        scan_res = fs_utils.scan_project(self.project_path, self.exclusion_patterns)
        modules_data = self._analyze_modules_parallel(scan_res.python_files)

        return {
            "modules_data": modules_data,
            "deps_data": dependencies.analyze_dependencies(
                modules_data, self.project_path, fs_utils.read_file_fast
            ),
            "structure": {
                "tree": fs_utils.generate_tree_optimized(self.project_path),
                "modules_count": len(modules_data),
                "file_types": scan_res.file_types,
                "size_stats": scan_res.size_stats,
            },
            "test_files_count": scan_res.test_files_count,
            "git_data": {
                "hotspots": git_analysis.get_git_hotspots(self.project_path),
                "churn": git_analysis.get_git_churn(self.project_path),
            },
            "manual_notes": self._read_manual_notes(),
            "qgis_metadata": fs_utils.parse_qgis_metadata(self.project_path),
        }

    def _read_manual_notes(self) -> str:
        """Reads manual architecture notes if they exist."""
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

    def _aggregate_all(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Final aggregation of all analysis data."""
        m_data = data["modules_data"]
        entry_points = [m["path"] for m in m_data if m.get("has_main")]

        proj_metrics = metrics.calculate_project_metrics(
            m_data,
            entry_points,
            data["test_files_count"],
            self.config,
            {"qgis_compliance": data.get("qgis_metadata", {})},
        )
        comp_dist = metrics.calculate_complexity_distribution(m_data)

        results = {
            "project_name": self.project_path.name,
            "timestamp": time.time(),
            "metrics": proj_metrics,
            "structure": data["structure"],
            "complexity": self._build_complexity_meta(m_data, proj_metrics, comp_dist),
            "dependencies": data["deps_data"],
            "debt": issues.find_technical_debt(m_data),
            "optimizations": self._get_optimizations(
                m_data, data, proj_metrics, comp_dist
            ),
            "security": self._aggregate_security(m_data),
            "antipatterns": self._aggregate_antipatterns(m_data),
            "entry_points": entry_points,
            "patterns": self._aggregate_patterns(m_data),
            "git": data["git_data"],
            "manual_notes": data.get("manual_notes", ""),
            "qgis_compliance": self._aggregate_qgis_compliance(m_data, data.get("qgis_metadata", {})),
        }
        return results

    def _get_optimizations(
        self, m_data, data, metrics_val, comp_dist
    ) -> List[Dict[str, Any]]:
        suggestions = issues.find_optimizations(m_data)
        recommender = ai_recommendations.AIRecommender(self.config)

        # Prepare context for AI recommendation
        ctx = {
            "metrics": metrics_val,
            "complexity": self._build_complexity_meta(m_data, metrics_val, comp_dist),
            "dependencies": data["deps_data"],
            "structure": data["structure"],
        }
        ai_sug = recommender.analyze_codebase(ctx)
        if ai_sug:
            suggestions.insert(0, {"module": "PROJECT_WIDE", "suggestions": ai_sug})
        return suggestions

    def _build_complexity_meta(self, m_data, metrics_val, dist) -> Dict[str, Any]:
        return {
            "total_modules": len(m_data),
            "total_lines": metrics_val.get("total_lines_code", 0),
            "total_functions": sum(len(m.get("functions", [])) for m in m_data),
            "total_classes": sum(len(m.get("classes", [])) for m in m_data),
            "average_complexity": metrics_val.get("avg_complexity", 0),
            "complexity_distribution": dist,
            "most_complex_modules": sorted(
                [(m["path"], m["complexity"]) for m in m_data],
                key=lambda x: x[1],
                reverse=True,
            )[:5],
        }

    def _aggregate_security(self, m_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sec_list = issues.find_security_issues(m_data, str(self.project_path))
        sev_map = {"high": 3, "medium": 2, "low": 1}

        for m in m_data:
            ast_sec = m.get("ast_security", [])
            if not ast_sec:
                continue

            existing = next((x for x in sec_list if x["module"] == m["path"]), None)
            if existing:
                existing["issues"].extend(ast_sec)
                existing["total_issues"] += len(ast_sec)
                new_max = max(ast_sec, key=lambda i: sev_map.get(i["severity"], 0))[
                    "severity"
                ]
                if sev_map.get(new_max, 0) > sev_map.get(existing["max_severity"], 0):
                    existing["max_severity"] = new_max
            else:
                sec_list.append(
                    {
                        "module": m["path"],
                        "issues": ast_sec,
                        "total_issues": len(ast_sec),
                        "max_severity": max(
                            ast_sec, key=lambda i: sev_map.get(i["severity"], 0)
                        )["severity"],
                    }
                )
        return sec_list

    def _aggregate_antipatterns(
        self, m_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return [
            {
                "module": m["path"],
                "issues": m["antipatterns"],
                "total_issues": len(m["antipatterns"]),
            }
            for m in m_data
            if m.get("antipatterns")
        ]

    def _aggregate_patterns(self, m_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        aggregated = {}
        for m in m_data:
            for p_name, occurrences in m.get("patterns", {}).items():
                if p_name not in aggregated:
                    aggregated[p_name] = []
                for occ in occurrences:
                    occ["module"] = m["path"]
                    aggregated[p_name].append(occ)
        return aggregated

    def _analyze_modules_parallel(
        self, files: List[pathlib.Path]
    ) -> List[Dict[str, Any]]:
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

    def _aggregate_qgis_compliance(self, m_data: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregates QGIS-specific results from modules and metadata."""
        agg = {
            "metadata": metadata,
            "processing_framework_detected": any(m.get("qgis_compliance", {}).get("processing_framework") for m in m_data),
            "i18n_stats": {
                "total_tr": sum(m.get("qgis_compliance", {}).get("i18n_usage", {}).get("tr", 0) for m in m_data),
                "total_strings": sum(m.get("qgis_compliance", {}).get("i18n_usage", {}).get("total_strings", 0) for m in m_data),
            },
            "gdal_style": "Correct" if all(m.get("qgis_compliance", {}).get("gdal_import_style") != "Legacy" for m in m_data) else "Legacy",
            "qt_transition": {
                "pyqt5_count": sum(len(m.get("qgis_compliance", {}).get("qt_transition", {}).get("pyqt5_imports", [])) for m in m_data),
                "pyqt6_count": sum(len(m.get("qgis_compliance", {}).get("qt_transition", {}).get("pyqt6_imports", [])) for m in m_data),
            },
            "legacy_signals": sum(m.get("qgis_compliance", {}).get("signals_slots", {}).get("legacy", 0) for m in m_data),
        }
        
        # Calculate overall QGIS compliance score
        score = metadata.get("compliance_score", 0) * 0.4
        if agg["processing_framework_detected"]:
            score += 20
        if agg["i18n_stats"]["total_strings"] > 0:
            i18n_ratio = agg["i18n_stats"]["total_tr"] / agg["i18n_stats"]["total_strings"]
            score += min(20, i18n_ratio * 40)
        if agg["gdal_style"] == "Correct":
            score += 10
        if agg["qt_transition"]["pyqt5_count"] == 0:
            score += 10
        
        agg["compliance_score"] = round(min(100, score), 1)
        return agg

    def _analyze_single_module(self, file_path: pathlib.Path) -> Dict[str, Any]:
        try:
            content = fs_utils.read_file_fast(file_path)
            if not content:
                return {}
            tree = ast.parse(content)
            entry_data = ast_utils.is_entry_point(tree)
            complexity = ast_utils.calculate_complexity(tree)
            halstead = ast_utils.calculate_halstead_metrics(tree)
            line_count = len(content.splitlines())

            return {
                "path": str(file_path.relative_to(self.project_path)),
                "lines": line_count,
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
                "ast_security": issues.detect_ast_security_issues(tree),
                "patterns": patterns.detect_patterns(tree),
                "unused_imports": ast_utils.detect_unused_imports(tree),
                "maintenance_index": metrics.calculate_maintenance_index(
                    halstead["volume"], complexity, line_count
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
        return (
            antipatterns.detect_god_object(tree)
            + antipatterns.detect_spaghetti_code(tree)
            + antipatterns.detect_magic_numbers(tree)
            + antipatterns.detect_dead_code(tree)
        )

    def _generate_outputs(self, results: Dict[str, Any], fmt: str):
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

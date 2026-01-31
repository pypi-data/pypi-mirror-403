"""Summary generation utilities for ai-context-core reporting."""

import pathlib
from typing import Dict, Any
from .html_builder import HTMLBuilder


class SummaryGenerator:
    """Orchestrates the generation of project summaries in different formats."""

    def __init__(self, analyses: Dict[str, Any], project_name: str):
        """Initialize the generator.

        Args:
            analyses: Dictionary of project analysis results.
            project_name: The name of the project.
        """
        self.analyses = analyses
        self.project_name = project_name

    def generate_html(self, output_path: pathlib.Path):
        """Generates the HTML report.

        Args:
            output_path: Path where the HTML report will be saved.
        """
        builder = HTMLBuilder(f"PROJECT SUMMARY - {self.project_name}")

        # Metrics
        m = self.analyses.get("metrics", {})
        c = self.analyses.get("complexity", {})
        m_html = f"""
        <div class="metric">Quality Score: <span class="metric-value">{m.get("quality_score", 0)}/100</span></div>
        <div class="metric">Source Lines (SLOC): <span class="metric-value">{m.get("total_lines_code", 0):,}</span></div>
        <div class="metric">Physical Lines: <span class="metric-value">{m.get("total_physical_lines", 0):,}</span></div>
        <div class="metric">Modules: <span class="metric-value">{c.get("total_modules", 0)}</span></div>
        """
        builder.add_section("📊 KEY METRICS", m_html)

        # Issues
        sec = self.analyses.get("security", [])
        if sec:
            s_list = [
                f"<strong>{i['module']}</strong>: {i['total_issues']} issues (Max: {i['max_severity']})"
                for i in sec[:5]
            ]
            builder.add_section("🚨 SECURITY ISSUES", builder.build_list(s_list))

        # Recommendations
        opt = self.analyses.get("optimizations", [])
        if opt:
            o_list = [
                f"<strong>{o['module']}</strong>: {'; '.join(s.get('message', '') for s in o.get('suggestions', []))}"
                for o in opt[:5]
            ]
            builder.add_section("💡 RECOMMENDATIONS", builder.build_list(o_list))

        # Graph
        from .reporting import generate_dependency_diagram

        graph = generate_dependency_diagram(self.analyses.get("dependencies", {}))
        if graph:
            builder.add_section(
                "🕸️ DEPENDENCY GRAPH", f'<div class="mermaid">{graph}</div>'
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(builder.render())

    def generate_markdown(self, output_path: pathlib.Path):
        """Generates the Markdown report.

        Args:
            output_path: Path where the Markdown report will be saved.
        """
        from .reporting import MarkdownBuilder

        builder = MarkdownBuilder(f"PROJECT SUMMARY - {self.project_name}")

        sections = [
            ("📊 KEY METRICS", self._build_metrics()),
            ("📁 STRUCTURE", self._build_structure()),
            ("🚨 CRITICAL ISSUES", self._build_issues()),
            ("📦 QGIS STANDARDS", self._build_qgis()),
            ("💡 MAIN RECOMMENDATIONS", self._build_recommendations()),
            ("🏗️ DESIGN PATTERNS", self._build_patterns()),
            ("📝 ARCHITECTURE NOTES", self._build_manual_notes()),
            ("🔄 GIT ANALYSIS", self._build_git()),
            ("📈 COMPLEXITY DISTRIBUTION", self._build_complexity()),
        ]

        for title, content in sections:
            if content:
                builder.add_section(title, content)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(builder.build())

    def _build_metrics(self) -> str:
        """Constructs the metrics section for Markdown report.

        Returns:
            Formatted strings with key project metrics.
        """
        c = self.analyses.get("complexity", {})
        m = self.analyses.get("metrics", {})
        s = self.analyses.get("structure", {}).get("size_stats", {})
        return (
            f"- **Total Modules**: {c.get('total_modules', 0):,}\n"
            f"- **Source Lines (SLOC)**: {c.get('total_lines', 0):,}\n"
            f"- **Total Physical Lines**: {m.get('total_physical_lines', 0):,}\n"
            f"- **Total Size**: {s.get('total_size_mb', 0):.1f} MB\n"
            f"- **Average Complexity**: {c.get('average_complexity', 0):.1f}\n"
            f"- **Avg Maintenance Index**: {m.get('avg_maintenance_index', 0):.1f}\n"
            f"- **Docstring Coverage**: {m.get('docstring_coverage', 0):.1f}%\n"
            f"- **Quality Score**: {m.get('quality_score', 0):.1f}/100\n"
            f"- **Test Files**: {m.get('test_files_count', 0)}"
        )

    def _build_structure(self) -> str:
        """Constructs the project structure section for Markdown report.

        Returns:
            Formatted strings with file counts and type distribution.
        """
        s = self.analyses.get("structure", {})
        sz = s.get("size_stats", {})
        ft = list(s.get("file_types", {}).keys())
        return (
            f"- **Python Files**: {sz.get('python_files', 0)}\n"
            f"- **Total Files**: {sz.get('total_files', 0)}\n"
            f"- **Primary File Types**: {', '.join(ft[:5])}"
        )

    def _build_issues(self) -> str:
        """Constructs the critical issues section for Markdown report.

        Returns:
            Formatted strings with security, debt, and circularity findings.
        """
        lines = []
        sec = self.analyses.get("security", [])
        if sec:
            lines.append("### 🔒 Security Issues:")
            for i in sec[:3]:
                lines.append(
                    f"- **{i['module']}**: {i['total_issues']} issues (Max: {i['max_severity'].upper()})"
                )

        debt = self.analyses.get("debt", [])
        if debt:
            lines.append("\n### 🏗️ Critical Technical Debt:")
            for i in [d for d in debt if d.get("severity_score", 0) >= 4][:5]:
                lines.append(
                    f"- **{i['module']}**: {i['total_issues']} issues (Score: {i['severity_score']})"
                )

        circ = self.analyses.get("dependencies", {}).get("circular_dependencies", [])
        if circ:
            lines.append("\n### 🔄 Circular Dependencies:")
            for cycle in circ[:3]:
                lines.append(
                    f"- {' -> '.join(cycle) if isinstance(cycle, list) else str(cycle)}"
                )

        return "\n".join(lines)

    def _build_qgis(self) -> str:
        """Constructs the QGIS standards section for Markdown report.

        Returns:
            Formatted strings highlighting QGIS-specific compliance items.
        """
        q = self.analyses.get("qgis_compliance", {})
        if not q:
            return ""
        res = [f"- **Compliance Score**: {q.get('compliance_score', 0):.1f}/100"]

        if q.get("processing_framework_detected"):
            res.append("- ✅ **Architecture**: Processing Framework detected")
        else:
            res.append(
                "- ⚠️ **Architecture**: No Processing Algorithms found (Recommended)"
            )

        i18n = q.get("i18n_stats", {})
        if i18n.get("total_strings", 0) > 0:
            cov = (i18n["total_tr"] / i18n["total_strings"]) * 100
            res.append(
                f"- **i18n Coverage**: {cov:.1f}% ({i18n['total_tr']}/{i18n['total_strings']} strings)"
            )

        qt = q.get("qt_transition", {})
        if qt.get("pyqt5_count", 0) > 0:
            res.append(
                f"- 🍎 **Qt6 Transition**: {qt['pyqt5_count']} PyQt5 imports (Action required for QGIS 4)"
            )

        if q.get("gdal_style") == "Legacy":
            res.append("- ⚠️ **GDAL Style**: Legacy imports detected (`import gdal`)")

        if q.get("legacy_signals", 0) > 0:
            res.append(
                f"- ⚠️ **Signals**: {q['legacy_signals']} legacy SIGNAL/SLOT macros detected"
            )

        issues = q.get("metadata", {}).get("issues", [])
        if issues:
            res.append("\n### 🚩 Metadata Issues:")
            for issue in issues[:5]:
                res.append(f"- {issue}")

        return "\n".join(res)

    def _build_recommendations(self) -> str:
        """Constructs the recommendations section for Markdown report.

        Returns:
            Formatted strings with optimization suggestions.
        """
        opts = self.analyses.get("optimizations", [])
        if not opts:
            return ""
        res = []
        for o in opts[:3]:
            res.append(f"### {o.get('module')}")
            for sug in o.get("suggestions", [])[:2]:
                res.append(f"- {sug.get('message', 'N/A')}")
        return "\n".join(res)

    def _build_patterns(self) -> str:
        """Constructs the design patterns section for Markdown report.

        Returns:
            Formatted strings detailing detected design patterns.
        """
        pats = self.analyses.get("patterns", {})
        if not pats:
            return ""
        res = []
        for name, occs in pats.items():
            res.append(f"### {name}")
            for occ in occs[:5]:
                res.append(
                    f"- **{occ.get('class') or occ.get('name') or 'N/A'}** in `{occ.get('module', 'N/A')}` ({occ.get('confidence', 0)}%)"
                )
        return "\n".join(res)

    def _build_git(self) -> str:
        """Constructs the Git analysis section for Markdown report.

        Returns:
            Formatted strings with code churn and hotspot information.
        """
        git = self.analyses.get("git", {})
        if not git:
            return ""
        res = []
        churn = git.get("churn", {})
        if churn.get("available"):
            res.append(f"### Code Churn (last {churn.get('period_days')} days)")
            res.append(
                f"- **Files Changed**: {churn['files_changed']}\n- **Additions**: +{churn['added']}\n- **Deletions**: -{churn['deleted']}\n- **Total Churn**: {churn['total_churn']}"
            )

        hot = git.get("hotspots", [])
        if hot:
            res.append("\n### 🔥 Hotspots")
            for h in hot[:5]:
                res.append(f"- `{h['path']}`: {h['commits']} commits")
        return "\n".join(res)

    def _build_complexity(self) -> str:
        """Constructs the complexity distribution section for Markdown report.

        Returns:
            Formatted strings with module complexity distribution.
        """
        c = self.analyses.get("complexity", {})
        dist = c.get("complexity_distribution", {})
        total = c.get("total_modules", 1) or 1
        return "\n".join(
            f"- {k}: {v} modules ({v / total * 100:.1f}%)" for k, v in dist.items()
        )

    def _build_manual_notes(self) -> str:
        """Reads manual architecture notes from the project configuration."""
        notes_content = self.analyses.get("manual_notes", "")
        return notes_content

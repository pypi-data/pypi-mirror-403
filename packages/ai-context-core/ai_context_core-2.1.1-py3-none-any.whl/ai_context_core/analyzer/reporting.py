"""Reporting and context generation tools.

Generates executive Markdown summaries and optimized context files for
AI interaction (LLM prompts). Includes Mermaid graph support.
"""

import pathlib
import time
import string
from typing import Dict, Any, List


def generate_dependency_diagram(dependencies: Dict[str, Any]) -> str:
    """Generates a Mermaid-formatted dependency graph for the top project modules."""
    graph = ["graph TD"]
    import_graph = dependencies.get("import_graph", {})
    if not import_graph:
        return ""

    node_scores = {u: len(v) for u, v in import_graph.items()}
    top_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)[:20]
    top_node_names = {name for name, _ in top_nodes}

    added_edges = set()
    for u, neighbors in import_graph.items():
        if u in top_node_names or any(v in top_node_names for v in neighbors):
            u_short = u.split("/")[-1].replace(".py", "").replace("__init__", "init")
            for v in neighbors:
                if u == v:
                    continue
                v_short = v.split(".")[-1]
                edge = f"{u_short}->{v_short}"
                if edge not in added_edges:
                    graph.append(f"    {u_short} --> {v_short}")
                    added_edges.add(edge)

    graph.append("    classDef module fill:#f9f,stroke:#333,stroke-width:2px;")
    for name in top_node_names:
        short = name.split("/")[-1].replace(".py", "").replace("__init__", "init")
        graph.append(f"    {short}")
        graph.append(f"    class {short} module;")

    return "\n".join(graph)


class MarkdownBuilder:
    """Helper class for building Markdown documents."""

    def __init__(self, title: str):
        self.lines = [
            f"# {title}",
            f"Analysis Date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "Analyzer Version: 2.0 (Ai-Context-Core)",
            "",
        ]

    def add_section(self, title: str, content: str, level: int = 2):
        self.lines.append(f"{'#' * level} {title}")
        self.lines.append(content)
        self.lines.append("")

    def build(self) -> str:
        return "\n".join(self.lines)


class HTMLBuilder:
    """Helper class for building HTML documents using string.Template."""

    CSS = """
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background: #f4f6f9; }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { color: #2c3e50; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 10px; }
    h3 { color: #34495e; }
    .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .metric { display: inline-block; margin-right: 20px; font-weight: bold; }
    .metric-value { color: #2980b9; }
    ul { list-style-type: none; padding: 0; }
    li { padding: 5px 0; border-bottom: 1px solid #eee; }
    li:last-child { border-bottom: none; }
    .mermaid { text-align: center; overflow-x: auto; background: white; padding: 20px; }
    """

    TEMPLATE = string.Template(
        "<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "<title>$title</title><style>$css</style><script type='module'>"
        "import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';"
        "mermaid.initialize({ startOnLoad: true });"
        "</script></head><body><h1>$title</h1><div class='card'><p><strong>Date:</strong> $date</p>"
        "<p><strong>Version:</strong> 2.0 (Ai-Context-Core)</p></div>$content</body></html>"
    )

    def __init__(self, title: str):
        self.title = title
        self.content_parts = []

    def add_section(self, title: str, content: str):
        self.content_parts.append(f'<div class="card"><h2>{title}</h2>{content}</div>')

    def build_list(self, items: List[str]) -> str:
        if not items:
            return ""
        return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

    def render(self) -> str:
        return self.TEMPLATE.substitute(
            title=self.title,
            css=self.CSS,
            date=time.strftime("%Y-%m-%d %H:%M:%S"),
            content="\n".join(self.content_parts),
        )


class SummaryGenerator:
    """Orchestrates the generation of project summaries in different formats."""

    def __init__(self, analyses: Dict[str, Any], project_name: str):
        self.analyses = analyses
        self.project_name = project_name

    def generate_html(self, output_path: pathlib.Path):
        builder = HTMLBuilder(f"PROJECT SUMMARY - {self.project_name}")

        # Metrics
        m = self.analyses.get("metrics", {})
        c = self.analyses.get("complexity", {})
        m_html = f"""
        <div class="metric">Quality Score: <span class="metric-value">{m.get("quality_score", 0)}/100</span></div>
        <div class="metric">Lines of Code: <span class="metric-value">{m.get("total_lines_code", 0):,}</span></div>
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
        graph = generate_dependency_diagram(self.analyses.get("dependencies", {}))
        if graph:
            builder.add_section(
                "🕸️ DEPENDENCY GRAPH", f'<div class="mermaid">{graph}</div>'
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(builder.render())

    def generate_markdown(self, output_path: pathlib.Path):
        builder = MarkdownBuilder(f"PROJECT SUMMARY - {self.project_name}")

        sections = [
            ("📊 KEY METRICS", self._build_metrics()),
            ("📁 STRUCTURE", self._build_structure()),
            ("🚨 CRITICAL ISSUES", self._build_issues()),
            ("📦 QGIS STANDARDS", self._build_qgis()),
            ("💡 MAIN RECOMMENDATIONS", self._build_recommendations()),
            ("🏗️ DESIGN PATTERNS", self._build_patterns()),
            ("🔄 GIT ANALYSIS", self._build_git()),
            ("📈 COMPLEXITY DISTRIBUTION", self._build_complexity()),
        ]

        for title, content in sections:
            if content:
                builder.add_section(title, content)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(builder.build())

    def _build_metrics(self) -> str:
        c = self.analyses.get("complexity", {})
        m = self.analyses.get("metrics", {})
        s = self.analyses.get("structure", {}).get("size_stats", {})
        return (
            f"- **Total Modules**: {c.get('total_modules', 0):,}\n"
            f"- **Lines of Code**: {c.get('total_lines', 0):,}\n"
            f"- **Total Size**: {s.get('total_size_mb', 0):.1f} MB\n"
            f"- **Average Complexity**: {c.get('average_complexity', 0):.1f}\n"
            f"- **Avg Maintenance Index**: {m.get('avg_maintenance_index', 0):.1f}\n"
            f"- **Docstring Coverage**: {m.get('docstring_coverage', 0):.1f}%\n"
            f"- **Quality Score**: {m.get('quality_score', 0):.1f}/100\n"
            f"- **Test Files**: {m.get('test_files_count', 0)}"
        )

    def _build_structure(self) -> str:
        s = self.analyses.get("structure", {})
        sz = s.get("size_stats", {})
        ft = list(s.get("file_types", {}).keys())
        return (
            f"- **Python Files**: {sz.get('python_files', 0)}\n"
            f"- **Total Files**: {sz.get('total_files', 0)}\n"
            f"- **Primary File Types**: {', '.join(ft[:5])}"
        )

    def _build_issues(self) -> str:
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
        q = self.analyses.get("qgis_compliance", {})
        if not q:
            return ""
        missing = [
            f
            for f, exists in q.get("mandatory_files", {}).get("files", {}).items()
            if not exists
        ]
        arch_v = q.get("architecture", {}).get("violations", [])
        res = [f"- **Compliance Score**: {q.get('compliance_score', 0):.1f}/100"]
        if missing:
            res.append(f"- ❌ **Missing Files**: {', '.join(missing)}")
        if arch_v:
            res.append(f"- ⚠️ **Architecture**: {len(arch_v)} violations")
        return "\n".join(res)

    def _build_recommendations(self) -> str:
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
        pats = self.analyses.get("patterns", {})
        if not pats:
            return ""
        res = []
        for name, occs in pats.items():
            res.append(f"### {name}")
            for occ in occs[:5]:
                res.append(
                    f"- **{occ['class']}** in `{occ['module']}` ({occ['confidence']}%)"
                )
        return "\n".join(res)

    def _build_git(self) -> str:
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
        c = self.analyses.get("complexity", {})
        dist = c.get("complexity_distribution", {})
        total = c.get("total_modules", 1) or 1
        return "\n".join(
            f"- {k}: {v} modules ({v/total*100:.1f}%)" for k, v in dist.items()
        )


def generate_project_summary(
    analyses: Dict[str, Any],
    output_path: pathlib.Path,
    project_name: str,
    format: str = "markdown",
) -> None:
    """Generates an executive summary of the project."""
    gen = SummaryGenerator(analyses, project_name)
    if format == "html":
        gen.generate_html(output_path)
    else:
        gen.generate_markdown(output_path)


def generate_ai_context(
    analyses: Dict[str, Any], output_path: pathlib.Path, project_name: str
) -> None:
    """Generates an optimized project overview file for AI consumption."""
    gen = AICtxGenerator(analyses, project_name)
    content = gen.build()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


class AICtxGenerator:
    """Generator for AI Context documents."""

    def __init__(self, analyses: Dict[str, Any], project_name: str):
        self.analyses = analyses
        self.project_name = project_name
        self.lines = [
            f"# AI CONTEXT - {project_name}",
            "Automatically generated by Ai-Context-Core",
            "",
        ]

    def build(self) -> str:
        s = self.analyses.get("structure", {})
        c = self.analyses.get("complexity", {})
        m = self.analyses.get("metrics", {})

        self.lines.append("## 📁 PROJECT STRUCTURE")
        self.lines.append(f"\n{s.get('tree', 'N/A')[:1200]}\n")

        self._add_entry_points()
        self._add_patterns()
        self._add_antipatterns()

        self.lines.append("\n## 📈 COMPLEXITY AND METRICS")
        self.lines.append(f"- **Total Modules**: {c.get('total_modules', 0)}")
        self.lines.append(f"- **Lines of Code**: {c.get('total_lines', 0):,}")
        self.lines.append(f"- **Functions**: {c.get('total_functions', 0)}")
        self.lines.append(f"- **Classes**: {c.get('total_classes', 0)}")
        self.lines.append(
            f"- **Average Complexity**: {c.get('average_complexity', 0):.1f}"
        )
        self.lines.append(
            f"- **Avg Maintenance Index**: {c.get('avg_maintenance_index', 0) or m.get('avg_maintenance_index', 0):.1f}"
        )

        cm = [m[0] for m in c.get("most_complex_modules", [])[:3]]
        self.lines.append(f"- **Most Complex Modules**: {', '.join(cm)}")

        self._add_dependencies()
        self._add_optimizations()
        self._add_git()

        self.lines.append("\n## 🔑 PROJECT KEYWORDS")
        ft = list(s.get("file_types", {}).keys())
        self.lines.append(f"- **Technologies**: {', '.join(ft[:8])}")

        return "\n".join(self.lines)

    def _add_entry_points(self):
        ep = self.analyses.get("entry_points", [])
        self.lines.append("## 🎯 ENTRY POINTS")
        for p in ep[:10]:
            self.lines.append(f"- `{p}`")
        if len(ep) > 10:
            self.lines.append(f"... and {len(ep) - 10} more")

    def _add_patterns(self):
        pats = self.analyses.get("patterns", {})
        self.lines.append("\n## 🏗️ DETECTED PATTERNS")
        if not pats:
            self.lines.append("No clear design patterns detected.")
            return
        for name, occs in pats.items():
            self.lines.append(f"### {name}")
            for o in occs[:3]:
                self.lines.append(
                    f"- **{o['class']}** in `{o['module']}` ({o['confidence']}%)"
                )
                for ev in o.get("evidence", []):
                    self.lines.append(f"  - _Evidence: {ev}_")

    def _add_antipatterns(self):
        ap = self.analyses.get("antipatterns", [])
        if not ap:
            return
        self.lines.append("\n## ⚠️ DETECTED ANTI-PATTERNS")
        for i in ap[:5]:
            self.lines.append(f"- **{i['module']}**")
            for issue in i.get("issues", [])[:2]:
                self.lines.append(f"  - {issue.get('message', 'N/A')}")

    def _add_dependencies(self):
        deps = self.analyses.get("dependencies", {})
        self.lines.append("\n## 🔗 PRIMARY DEPENDENCIES")
        tp = deps.get("third_party", [])
        if tp:
            counts = {}
            for d in tp:
                base = d.split(".")[0]
                counts[base] = counts.get(base, 0) + 1
            self.lines.append("### Third Party (most frequent):")
            for p, c in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:15]:
                self.lines.append(f"- `{p}` ({c} imports)")

        unused = deps.get("unused_imports", {})
        if unused:
            self.lines.append("\n## ⚠️ UNUSED IMPORTS")
            for mod, items in list(unused.items())[:5]:
                self.lines.append(f"- **{mod}**: {', '.join(items[:5])}")

        high_c = sorted(
            deps.get("coupling_metrics", {}).items(),
            key=lambda x: x[1].get("cbo", 0),
            reverse=True,
        )[:5]
        high_c = [i for i in high_c if i[1].get("cbo", 0) > 5]
        if high_c:
            self.lines.append("\n## 🔗 HIGH COUPLING MODULES (CBO)")
            for mod, m in high_c:
                self.lines.append(
                    f"- **{mod}**: CBO {m['cbo']} (In: {m['fan_in']}, Out: {m['fan_out']})"
                )

        g_m = deps.get("graph_metrics", {})
        if g_m:
            self.lines.append("\n## 🕸️  DEPENDENCY STRUCTURE")
            self.lines.append(
                f"- **Nodes**: {g_m.get('nodes', 0)}\n- **Edges**: {g_m.get('edges', 0)}\n- **Density**: {g_m.get('density', 0):.3f}"
            )
            self.lines.append("\n## 🕸️ DEPENDENCY DIAGRAM (Conceptual)\n```mermaid")
            self.lines.append(generate_dependency_diagram(deps))
            self.lines.append("```")

    def _add_optimizations(self):
        opts = self.analyses.get("optimizations", [])
        if not opts:
            return
        self.lines.append("\n## 💡 OPTIMIZATION RECOMMENDATIONS")
        for o in opts[:5]:
            self.lines.append(f"### {o.get('module')}")
            for s in o.get("suggestions", [])[:2]:
                self.lines.append(
                    f"- **{s.get('type', 'Opt')}**: {s.get('message', 'N/A')}"
                )

    def _add_git(self):
        git = self.analyses.get("git", {})
        if not git:
            return
        self.lines.append("\n## 🔄 GIT AND EVOLUTION")
        hot = git.get("hotspots", [])
        if hot:
            self.lines.append("### Top Hotspots:")
            for h in hot[:5]:
                self.lines.append(f"- `{h['path']}` ({h['commits']} commits)")

        ch = git.get("churn", {})
        if ch.get("available"):
            self.lines.append(f"### Recent Churn ({ch.get('period_days')} days):")
            self.lines.append(f"- Total lines changed: {ch.get('total_churn')}")

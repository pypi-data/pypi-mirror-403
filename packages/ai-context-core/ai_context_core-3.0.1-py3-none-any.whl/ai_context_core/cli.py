"""Command Line Interface for Ai-Context-Core."""

import click
import pathlib
import shutil
import os
import sys
from typing import Optional
from .analyzer.engine import ProjectAnalyzer
from .config.loader import ConfigLoader, list_profiles
import http.server
import socketserver
import webbrowser
from rich.console import Console
from rich.table import Table


class CLIHandler:
    """Handles the business logic for CLI commands."""

    @staticmethod
    def initialize_project(path: str, profile: str):
        """Sets up the initial project structure and configuration.

        Args:
            path: Target project path.
            profile: Configuration profile to use.
        """
        proj = pathlib.Path(path).resolve()
        ai_ctx, agent_wf = proj / ".ai-context", proj / ".agent" / "workflows"
        click.echo(f"🔄 Initializing {proj} with '{profile}'...")
        ai_ctx.mkdir(exist_ok=True)
        agent_wf.mkdir(parents=True, exist_ok=True)

        loader = ConfigLoader()
        if profile != "generic":
            p_path = loader.profiles_path / f"{profile}.yaml"
            if p_path.exists():
                shutil.copy2(p_path, ai_ctx / "config.yaml")

        templates = pathlib.Path(__file__).parent / "templates"
        for wf in (templates / "workflows").glob("*.md"):
            dest = agent_wf / wf.name
            if not dest.exists():
                shutil.copy2(wf, dest)

        prompt_src = templates / "initial_prompt.md"
        prompt_dest = ai_ctx / "prompt_inicial.md"
        if prompt_src.exists() and not prompt_dest.exists():
            c = (
                prompt_src.read_text(encoding="utf-8")
                .replace("{project_name}", proj.name)
                .replace("{project_type}", profile)
            )
            prompt_dest.write_text(c, encoding="utf-8")
        click.secho("✨ Ready.", fg="green")

    @staticmethod
    def run_analysis(path: str, workers: Optional[int], format: str, no_cache: bool):
        """Executes the full project analysis pipeline.

        Args:
            path: Project path to analyze.
            workers: Number of parallel workers.
            format: Output format ('markdown' or 'html').
            no_cache: Whether to bypass analysis cache.
        """
        proj = pathlib.Path(path).resolve()
        loader = ConfigLoader()
        local_cfg_path = proj / ".ai-context" / "config.yaml"
        local_cfg = {}
        if local_cfg_path.exists():
            try:
                import yaml

                local_cfg = yaml.safe_load(local_cfg_path.read_text()) or {}
            except Exception:
                pass

        cfg = loader.load_config(
            profile_name=local_cfg.get("profile_name"), override_config=local_cfg
        )
        analyzer = ProjectAnalyzer(
            project_path=str(proj),
            config=cfg,
            max_workers=workers,
            ignore_cache=no_cache,
        )
        click.echo(f"🚀 Analyzing {proj.name}...")
        try:
            res = analyzer.analyze(output_format=format)
            m = res.get("metrics", {})
            q = m.get("quality_score", 0)
            click.echo("-" * 40)
            click.secho(
                f"🏆 Quality Score: {q:.1f}/100", fg="green" if q > 80 else "yellow"
            )
            click.echo(
                f"📊 Lines: {m.get('total_lines_code', 0):,}\n💡 Opts: {len(res.get('optimizations', []))}"
            )
            click.echo("-" * 40)
            click.secho("✅ Completed.", fg="green")
        except Exception as e:
            click.secho(f"❌ Error: {e}", fg="red")
            if os.environ.get("DEBUG"):
                raise e
            sys.exit(1)

    @staticmethod
    def inspect_file(file_path: str):
        path = pathlib.Path(file_path).resolve()
        if not path.exists() or not path.is_file():
            click.secho(f"❌ File not found: {file_path}", fg="red")
            sys.exit(1)

        loader = ConfigLoader()
        cfg = loader.load_config()
        # We need a ProjectAnalyzer to access its analysis methods
        analyzer = ProjectAnalyzer(project_path=str(path.parent), config=cfg)
        click.echo(f"🔍 Inspecting {path.name}...")

        data = analyzer._analyze_single_module(path)
        if data.get("syntax_error"):
            click.secho(f"❌ Syntax Error: {data.get('error')}", fg="red")
            sys.exit(1)

        click.echo("-" * 40)
        click.echo(f"📄 Module: {data['path']}")
        click.echo(f"📏 Lines: {data['lines']}")
        click.echo(f"📉 Complexity: {data['complexity']}")
        click.echo(f"🏗️  Patterns: {len(data.get('patterns', {}))}")
        click.echo(f"🔒 Security Issues: {len(data.get('ast_security', []))}")
        click.echo("-" * 40)

    @staticmethod
    def start_server(port: int, open_browser: bool):
        handler = http.server.SimpleHTTPRequestHandler
        try:
            with socketserver.TCPServer(("", port), handler) as httpd:
                url = f"http://localhost:{port}/PROJECT_SUMMARY.html"
                click.secho(f"🌐 Serving report at: {url}", fg="cyan")
                if open_browser:
                    webbrowser.open(url)
                httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\n🛑 Server stopped.")
        except Exception as e:
            click.secho(f"❌ Server error: {e}", fg="red")

    @staticmethod
    def run_audit(path: str, threshold: float):
        """Performs a security and quality audit, exits with error if below threshold.

        Args:
            path: Project path.
            threshold: Minimum acceptable Quality Score.
        """
        proj = pathlib.Path(path).resolve()
        loader = ConfigLoader()
        cfg = loader.load_config()
        analyzer = ProjectAnalyzer(project_path=str(proj), config=cfg)
        click.echo(f"🛡️  Auditing {proj.name} (Threshold: {threshold})...")
        res = analyzer.analyze()
        score = res.get("metrics", {}).get("quality_score", 0)

        if score < threshold:
            click.secho(
                f"❌ Audit Failed: Score {score:.1f} is below {threshold}", fg="red"
            )
            sys.exit(1)
        else:
            click.secho(f"✅ Audit Passed: Score {score:.1f}", fg="green")

    @staticmethod
    def show_specific(path: str, category: str):
        proj = pathlib.Path(path).resolve()
        loader = ConfigLoader()
        cfg = loader.load_config()
        analyzer = ProjectAnalyzer(project_path=str(proj), config=cfg)
        res = analyzer.analyze()

        if category == "patterns":
            click.secho("🏗️  DETECTED PATTERNS", fg="cyan", bold=True)
            pats = res.get("patterns", {})
            if not pats:
                click.echo("No patterns detected.")
            for name, occs in pats.items():
                for o in occs:
                    class_name = o.get("class", o.get("name", "N/A"))
                    module_path = o.get("module", "N/A")
                    confidence = o.get("confidence", 0)
                    click.echo(
                        f"- {name}: {class_name} in {module_path} ({confidence}%)"
                    )

        elif category == "security":
            click.secho("🚨 SECURITY ISSUES", fg="red", bold=True)
            sec = res.get("security", [])
            if not sec:
                click.echo("No issues found.")
            for mod in sec:
                for issue in mod.get("issues", []):
                    severity = issue.get("severity", "unknown").upper()
                    module_name = mod.get("module", "N/A")
                    message = issue.get(
                        "message", issue.get("description", "No description")
                    )
                    click.echo(f"- [{severity}] {module_name}: {message}")

        elif category == "recommendations":
            click.secho("💡 AI RECOMMENDATIONS", fg="yellow", bold=True)
            opts = res.get("optimizations", [])
            if not opts:
                click.echo("No recommendations.")
            for o in opts:
                module_name = o.get("module", "N/A")
                for sug in o.get("suggestions", []):
                    message = sug.get("message", "N/A")
                    click.echo(f"- [{module_name}] {message}")

    @staticmethod
    def show_dependencies(
        path: str, show_unused: bool, show_cycles: bool, show_metrics: bool
    ):
        """Shows dependency analysis results.

        Args:
            path: Project path.
            show_unused: Show unused imports.
            show_cycles: Show circular dependencies.
            show_metrics: Show coupling metrics.
        """
        proj = pathlib.Path(path).resolve()
        loader = ConfigLoader()
        cfg = loader.load_config()
        analyzer = ProjectAnalyzer(project_path=str(proj), config=cfg)
        res = analyzer.analyze()
        deps = res.get("dependencies", {})
        console = Console()

        if show_unused:
            click.secho("🗑️  UNUSED IMPORTS", fg="yellow", bold=True)
            unused = deps.get("unused_imports", {})
            if not unused:
                click.echo("No unused imports detected.")
            else:
                for module, imports in unused.items():
                    click.echo(f"\n📄 {module}:")
                    for imp in imports:
                        click.echo(f"  - {imp}")

        if show_cycles:
            click.secho("\n🔄 CIRCULAR DEPENDENCIES", fg="red", bold=True)
            cycles = deps.get("circular_dependencies", [])
            if not cycles:
                click.echo("No circular dependencies detected. ✅")
            else:
                for i, cycle in enumerate(cycles, 1):
                    click.echo(f"{i}. {' → '.join(cycle)}")

        if show_metrics:
            click.secho("\n📊 DEPENDENCY METRICS", fg="cyan", bold=True)
            metrics = deps.get("graph_metrics", {})
            coupling = deps.get("coupling_metrics", {})

            table = Table(title="Graph Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Nodes", str(metrics.get("nodes", 0)))
            table.add_row("Edges", str(metrics.get("edges", 0)))
            table.add_row("Density", f"{metrics.get('density', 0):.3f}")
            table.add_row("Is DAG", "✅" if metrics.get("is_dag") else "❌")
            table.add_row(
                "Components", str(metrics.get("weakly_connected_components", 0))
            )

            console.print(table)

            if coupling:
                click.echo("\n🔗 Top 5 Most Coupled Modules:")
                sorted_coupling = sorted(
                    coupling.items(), key=lambda x: x[1].get("cbo", 0), reverse=True
                )[:5]
                for mod, metrics in sorted_coupling:
                    cbo = metrics.get("cbo", 0)
                    click.echo(f"  - {mod}: CBO={cbo}")

    @staticmethod
    def show_git_evolution(path: str, days: int):
        """Shows git evolution analysis.

        Args:
            path: Project path.
            days: Number of days for churn analysis.
        """
        from .analyzer import git_analysis

        proj = pathlib.Path(path).resolve()
        analyzer = git_analysis.GitAnalyzer(proj)
        console = Console()

        if not analyzer.is_repo():
            click.secho("❌ Not a git repository", fg="red")
            sys.exit(1)

        # Hotspots
        click.secho("🔥 GIT HOTSPOTS (Most Modified Files)", fg="red", bold=True)
        hotspots = analyzer.get_hotspots(limit=10)
        if not hotspots:
            click.echo("No hotspots found.")
        else:
            table = Table()
            table.add_column("File", style="cyan")
            table.add_column("Commits", style="yellow", justify="right")

            for h in hotspots:
                table.add_row(h["path"], str(h["commits"]))

            console.print(table)

        # Churn
        click.secho(f"\n📈 CODE CHURN (Last {days} days)", fg="yellow", bold=True)
        churn = analyzer.get_churn(days=days)
        if not churn.get("available"):
            click.echo("No churn data available.")
        else:
            click.echo(f"Files Changed: {churn.get('files_changed', 0)}")
            click.echo(f"Lines Added: {churn.get('added', 0):,}")
            click.echo(f"Lines Deleted: {churn.get('deleted', 0):,}")
            click.echo(f"Total Churn: {churn.get('total_churn', 0):,}")

    @staticmethod
    def show_quick_stats(path: str):
        """Shows quick project statistics.

        Args:
            path: Project path.
        """
        proj = pathlib.Path(path).resolve()
        loader = ConfigLoader()
        cfg = loader.load_config()
        analyzer = ProjectAnalyzer(project_path=str(proj), config=cfg)
        res = analyzer.analyze()
        console = Console()

        metrics = res.get("metrics", {})
        complexity = res.get("complexity", {})

        # Summary table
        click.secho("📊 PROJECT STATISTICS", fg="cyan", bold=True)
        table = Table(title=f"Summary for {proj.name}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Source Lines (SLOC)", f"{metrics.get('total_lines_code', 0):,}")
        table.add_row("Physical Lines", f"{metrics.get('total_physical_lines', 0):,}")
        table.add_row("Modules", str(complexity.get("total_modules", 0)))
        table.add_row("Functions", str(complexity.get("total_functions", 0)))
        table.add_row("Classes", str(complexity.get("total_classes", 0)))
        table.add_row(
            "Avg Complexity", f"{complexity.get('average_complexity', 0):.1f}"
        )
        table.add_row(
            "Avg Maintenance Index", f"{complexity.get('avg_maintenance_index', 0):.1f}"
        )
        table.add_row("Quality Score", f"{metrics.get('quality_score', 0):.1f}/100")

        console.print(table)

        # Top complex modules
        click.secho("\n🔴 Top 5 Most Complex Modules", fg="red", bold=True)
        complex_mods = complexity.get("most_complex_modules", [])[:5]
        if complex_mods:
            for mod, comp in complex_mods:
                click.echo(f"  - {mod}: {comp}")

    @staticmethod
    def validate_qgis(path: str):
        """Validates QGIS plugin compliance.

        Args:
            path: Project path.
        """
        proj = pathlib.Path(path).resolve()
        loader = ConfigLoader()
        cfg = loader.load_config()
        analyzer = ProjectAnalyzer(project_path=str(proj), config=cfg)
        res = analyzer.analyze()

        qgis = res.get("qgis_compliance", {})
        metadata = qgis.get("metadata", {})

        click.secho("🗺️  QGIS PLUGIN VALIDATION", fg="green", bold=True)

        # Metadata validation
        if metadata.get("valid"):
            click.secho("\n✅ metadata.txt is valid", fg="green")
            content = metadata.get("content", {})
            click.echo(f"Plugin Name: {content.get('name', 'N/A')}")
            click.echo(f"Version: {content.get('version', 'N/A')}")
            click.echo(
                f"QGIS Min Version: {content.get('qgisminimumversion', 'N/A')}"
            )
        else:
            click.secho("\n❌ metadata.txt validation failed", fg="red")
            for err in metadata.get("errors", []):
                click.echo(f"  - {err}")

        # i18n stats
        i18n = qgis.get("i18n_stats", {})
        total_tr = i18n.get("total_tr", 0)
        total_strings = i18n.get("total_strings", 0)
        coverage = (total_tr / total_strings * 100) if total_strings > 0 else 0

        click.secho("\n🌍 Internationalization (i18n)", fg="cyan", bold=True)
        click.echo(f"Translated strings: {total_tr}/{total_strings} ({coverage:.1f}%)")

        # Qt6 readiness
        qt = qgis.get("qt_transition", {})
        pyqt5_count = qt.get("pyqt5_count", 0)
        pyqt6_count = qt.get("pyqt6_count", 0)

        click.secho("\n🔄 Qt6 Transition Readiness", fg="yellow", bold=True)
        if pyqt5_count == 0:
            click.secho("✅ No PyQt5 imports detected (Qt6 ready!)", fg="green")
        else:
            click.secho(f"⚠️  {pyqt5_count} PyQt5 imports found", fg="yellow")

        if pyqt6_count > 0:
            click.echo(f"PyQt6 imports: {pyqt6_count}")

        # Overall score
        score = qgis.get("compliance_score", 0)
        click.secho(
            f"\n🏆 QGIS Compliance Score: {score:.1f}/100",
            fg="green" if score > 70 else "yellow",
        )

    @staticmethod
    def clean_artifacts(path: str, dry_run: bool):
        """Cleans cache and generated artifacts.

        Args:
            path: Project path.
            dry_run: If True, only shows what would be deleted.
        """
        proj = pathlib.Path(path).resolve()

        artifacts = [
            proj / ".ai_context_cache.json",
            proj / "AI_CONTEXT.md",
            proj / "project_context.json",
            proj / "PROJECT_SUMMARY.md",
            proj / "PROJECT_SUMMARY.html",
            proj / "ANALYSIS_REPORT.md",
        ]

        click.secho("🧹 CLEANING ARTIFACTS", fg="cyan", bold=True)

        deleted_count = 0
        for artifact in artifacts:
            if artifact.exists():
                if dry_run:
                    click.echo(f"Would delete: {artifact.name}")
                else:
                    artifact.unlink()
                    click.secho(f"✅ Deleted: {artifact.name}", fg="green")
                deleted_count += 1

        if deleted_count == 0:
            click.echo("No artifacts found to clean.")
        elif dry_run:
            click.echo(
                f"\n{deleted_count} file(s) would be deleted. Run without --dry-run to delete."
            )
        else:
            click.secho(f"\n✨ Cleaned {deleted_count} file(s)", fg="green")


@click.group()
@click.version_option(package_name="ai-context-core")
def cli():
    """CLI tool for AI context management."""
    pass


@cli.command()
@click.option("--profile", "-p", default="generic", help="Config profile")
@click.option("--path", default=".", help="Project path")
def init(profile: str, path: str):
    """Initializes the .ai-context structure."""
    CLIHandler.initialize_project(path, profile)


@cli.command()
@click.option("--path", default=".", help="Project path")
@click.option("--workers", "-w", default=None, type=int, help="Parallel workers")
@click.option(
    "--format", "-f", type=click.Choice(["markdown", "html"]), default="markdown"
)
@click.option("--no-cache", is_flag=True, help="Force full analysis, ignoring cache")
def analyze(path: str, workers: Optional[int], format: str, no_cache: bool):
    """Runs project analysis."""
    CLIHandler.run_analysis(path, workers, format, no_cache)


@cli.command()
@click.argument("file_path")
def inspect(file_path: str):
    """Deep analysis of a single file."""
    CLIHandler.inspect_file(file_path)


@cli.command()
@click.option("--port", "-p", default=8000, help="Server port")
@click.option("--open", "open_browser", is_flag=True, help="Open browser automatically")
def serve(port: int, open_browser: bool):
    """Serves the HTML report locally."""
    CLIHandler.start_server(port, open_browser)


@cli.command()
@click.option("--path", default=".", help="Project path")
@click.option(
    "--threshold", "-t", default=70.0, type=float, help="Minimum Quality Score"
)
def audit(path: str, threshold: float):
    """Fails if Quality Score is below threshold."""
    CLIHandler.run_audit(path, threshold)


@cli.command()
@click.option("--path", default=".", help="Project path")
def patterns(path: str):
    """Shows only detected design patterns."""
    CLIHandler.show_specific(path, "patterns")


@cli.command()
@click.option("--path", default=".", help="Project path")
def security(path: str):
    """Shows only security issues."""
    CLIHandler.show_specific(path, "security")


@cli.command(name="help-me")
@click.option("--path", default=".", help="Project path")
def help_me(path: str):
    """Shows only AI recommendations."""
    CLIHandler.show_specific(path, "recommendations")


@cli.command()
def profiles():
    """Lists available profiles."""
    for p in list_profiles():
        click.echo(f" - {p}")


@cli.command()
@click.option("--path", default=".", help="Project path")
@click.option("--unused", is_flag=True, help="Show unused imports")
@click.option("--cycles", is_flag=True, help="Show circular dependencies")
@click.option("--metrics", is_flag=True, help="Show coupling metrics")
def deps(path: str, unused: bool, cycles: bool, metrics: bool):
    """Analyzes project dependencies."""
    # If no flags, show all
    if not (unused or cycles or metrics):
        unused = cycles = metrics = True
    CLIHandler.show_dependencies(path, unused, cycles, metrics)


@cli.command()
@click.option("--path", default=".", help="Project path")
@click.option("--days", "-d", default=30, type=int, help="Days for churn analysis")
def git(path: str, days: int):
    """Shows git evolution analysis (hotspots and churn)."""
    CLIHandler.show_git_evolution(path, days)


@cli.command()
@click.option("--path", default=".", help="Project path")
def stats(path: str):
    """Shows quick project statistics."""
    CLIHandler.show_quick_stats(path)


@cli.command()
@click.option("--path", default=".", help="Project path")
def qgis(path: str):
    """Validates QGIS plugin compliance."""
    CLIHandler.validate_qgis(path)


@cli.command()
@click.option("--path", default=".", help="Project path")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be deleted without deleting"
)
def clean(path: str, dry_run: bool):
    """Cleans cache and generated artifacts."""
    CLIHandler.clean_artifacts(path, dry_run)


if __name__ == "__main__":
    cli()

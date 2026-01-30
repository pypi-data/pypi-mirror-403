"""Command Line Interface for Ai-Context-Core."""

import click
import pathlib
import shutil
import os
import sys
from typing import Optional, Dict, Any
from .analyzer.engine import ProjectAnalyzer
from .config.loader import ConfigLoader, list_profiles
import http.server
import socketserver
import threading
import webbrowser


class CLIHandler:
    """Handles the business logic for CLI commands."""

    @staticmethod
    def initialize_project(path: str, profile: str):
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
            project_path=str(proj), config=cfg, max_workers=workers, ignore_cache=no_cache
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
        proj = pathlib.Path(path).resolve()
        loader = ConfigLoader()
        cfg = loader.load_config()
        analyzer = ProjectAnalyzer(project_path=str(proj), config=cfg)
        click.echo(f"🛡️  Auditing {proj.name} (Threshold: {threshold})...")
        res = analyzer.analyze()
        score = res.get("metrics", {}).get("quality_score", 0)

        if score < threshold:
            click.secho(f"❌ Audit Failed: Score {score:.1f} is below {threshold}", fg="red")
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
                    click.echo(f"- {name}: {o['class']} in {o['module']} ({o['confidence']}%)")

        elif category == "security":
            click.secho("🚨 SECURITY ISSUES", fg="red", bold=True)
            sec = res.get("security", [])
            if not sec:
                click.echo("No issues found.")
            for mod in sec:
                for issue in mod.get("issues", []):
                    click.echo(f"- [{issue['severity'].upper()}] {mod['module']}: {issue.get('message', issue.get('description'))}")

        elif category == "recommendations":
            click.secho("💡 AI RECOMMENDATIONS", fg="yellow", bold=True)
            opts = res.get("optimizations", [])
            if not opts:
                click.echo("No recommendations.")
            for o in opts:
                for sug in o.get("suggestions", []):
                    click.echo(f"- [{o['module']}] {sug.get('message')}")


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
@click.option("--threshold", "-t", default=70.0, type=float, help="Minimum Quality Score")
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


if __name__ == "__main__":
    cli()

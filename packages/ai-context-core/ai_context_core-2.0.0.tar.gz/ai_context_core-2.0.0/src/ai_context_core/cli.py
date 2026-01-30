"""Command Line Interface for Ai-Context-Core."""

import click
import pathlib
import shutil
import os
import sys
from typing import Optional
from .analyzer.engine import ProjectAnalyzer
from .config.loader import ConfigLoader, list_profiles


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
    def run_analysis(path: str, workers: Optional[int], format: str):
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
            project_path=str(proj), config=cfg, max_workers=workers
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


@click.group()
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
def analyze(path: str, workers: Optional[int], format: str):
    """Runs project analysis."""
    CLIHandler.run_analysis(path, workers, format)


@cli.command()
def profiles():
    """Lists available profiles."""
    for p in list_profiles():
        click.echo(f" - {p}")


if __name__ == "__main__":
    cli()

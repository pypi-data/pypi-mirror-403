"""CLI entry point for accuralai-core."""

from __future__ import annotations

from pathlib import Path

import click

from .commands.generate import register_generate_command
from .interactive import run_interactive_cli


@click.group(invoke_without_command=True)
@click.option(
    "--config",
    "config_paths",
    multiple=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (TOML). Can be supplied multiple times.",
)
@click.pass_context
def app(ctx: click.Context, config_paths: tuple[Path, ...]) -> None:
    """AccuralAI core orchestrator CLI."""
    ctx.ensure_object(dict)
    ctx.obj["config_paths"] = [str(path) for path in config_paths]
    ctx.obj["config_overrides"] = None

    if ctx.invoked_subcommand is None:
        run_interactive_cli(
            config_paths=ctx.obj["config_paths"],
            config_overrides=ctx.obj.get("config_overrides"),
        )


register_generate_command(app)


def main() -> None:
    """Console entry point."""
    app(obj={})

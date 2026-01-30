"""CLI command for running the generation pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import anyio
import click

from ...core.orchestrator import CoreOrchestrator
from ...contracts.models import GenerateRequest
from ..output import render_json, render_text


def register_generate_command(app: click.Group) -> None:
    """Register the generate command on the provided CLI app."""

    @app.command("generate")
    @click.option("--prompt", type=str, help="Prompt text to send to the backend.")
    @click.option(
        "--prompt-file",
        type=click.Path(exists=True, path_type=Path),
        help="File containing prompt text.",
    )
    @click.option("--system-prompt", type=str, help="Optional system prompt to include.")
    @click.option("--route", type=str, help="Route hint for the router module.")
    @click.option(
        "--tag",
        "tags",
        multiple=True,
        help="Tag applied to the request (repeatable).",
    )
    @click.option(
        "--format",
        "output_format",
        type=click.Choice(["text", "json"]),
        default="text",
        show_default=True,
    )
    @click.option(
        "--metadata",
        multiple=True,
        help="Additional metadata key=value (repeatable).",
    )
    @click.option(
        "--param",
        "param_pairs",
        multiple=True,
        help="Generation parameter key=value (repeatable).",
    )
    @click.pass_context
    def generate_command(ctx: click.Context, **kwargs: object) -> None:
        """Execute the generation pipeline."""
        prompt = kwargs.get("prompt")
        prompt_file: Path | None = kwargs.get("prompt_file")
        output_format = kwargs.get("output_format", "text")
        route = kwargs.get("route")
        system_prompt = kwargs.get("system_prompt")
        tags = kwargs.get("tags", ())
        metadata_pairs = kwargs.get("metadata", [])
        param_pairs = kwargs.get("param_pairs", [])

        if not prompt and not prompt_file:
            raise click.UsageError("Either --prompt or --prompt-file must be provided.")
        if prompt and prompt_file:
            raise click.UsageError("Provide only one of --prompt or --prompt-file.")

        if prompt_file:
            prompt = prompt_file.read_text().strip()
        assert isinstance(prompt, str)

        metadata = _parse_kv_pairs(metadata_pairs, label="metadata")
        parameters = _parse_kv_pairs(param_pairs, label="parameter")

        async def _run() -> None:
            orchestrator = CoreOrchestrator(
                config_paths=ctx.obj.get("config_paths"),
                config_overrides=ctx.obj.get("config_overrides"),
            )
            try:
                request = GenerateRequest(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    route_hint=route,
                    metadata=metadata,
                    parameters=parameters,
                    tags=list(tags),
                )
                response = await orchestrator.generate(request)
            finally:
                await orchestrator.aclose()

            if output_format == "json":
                click.echo(render_json(response))
            else:
                click.echo(render_text(response))

        anyio.run(_run)


def _parse_kv_pairs(pairs: tuple[str, ...], *, label: str) -> Dict[str, object]:
    metadata: Dict[str, object] = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"{label.title()} entry '{pair}' must be key=value.")
        key, value = pair.split("=", 1)
        value = value.strip()
        try:
            metadata[key] = json.loads(value)
        except json.JSONDecodeError:
            metadata[key] = value
    return metadata

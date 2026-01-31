"""CLI wrapper for link-groups."""

from __future__ import annotations

import os
import typer

from worai.core.link_groups import LinkGroupsOptions, run as link_groups_run
from worai.core.wordlift import resolve_api_key
from worai.errors import UsageError

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    input_file: str = typer.Argument(..., help="Path to input CSV file."),
    output_format: str = typer.Option("turtle", "--format", "-f", help="RDF output format."),
    apply: bool = typer.Option(False, "--apply", help="Apply changes via WordLift API."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show curl commands without executing them."),
    concurrency: int = typer.Option(2, "--concurrency", help="Number of concurrent API requests."),
    retries: int = typer.Option(3, "--retries", help="Number of retries for failed requests."),
) -> None:
    api_key = None
    if apply:
        api_key = resolve_api_key(ctx.obj.get("config") if ctx.obj else None) or os.environ.get("WORDLIFT_KEY")
        if not api_key:
            raise UsageError("WORDLIFT_KEY is required when using --apply.")

    options = LinkGroupsOptions(
        input_file=input_file,
        output_format=output_format,
        apply=apply,
        dry_run=dry_run,
        api_key=api_key,
        concurrency=concurrency,
        retries=retries,
    )

    output = link_groups_run(options)
    if output:
        typer.echo(output)

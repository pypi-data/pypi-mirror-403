"""CLI wrapper for patch."""

from __future__ import annotations

import os
import typer

from worai.core.patch import PatchOptions, run as patch_run
from worai.core.wordlift import resolve_api_key
from worai.errors import UsageError

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    input_file: str = typer.Argument(..., help="Path to RDF input file (.ttl or .jsonld)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print curl commands instead of executing them."),
    add_types: bool = typer.Option(False, "--add-types", help="Use 'add' for rdf:type properties."),
    types_only: bool = typer.Option(False, "--types-only", help="Only process rdf:type triples."),
    subjects_file: str | None = typer.Option(None, "--subjects-file", help="File of subject URIs to process."),
    workers: int = typer.Option(2, "--workers", help="Number of concurrent requests."),
    retries: int = typer.Option(3, "--retries", help="Number of retries for failed requests."),
) -> None:
    api_key = resolve_api_key(ctx.obj.get("config") if ctx.obj else None) or os.environ.get("WORDLIFT_API_KEY")
    if not api_key:
        raise UsageError("WORDLIFT_KEY is required (or set wordlift.api_key in config).")

    options = PatchOptions(
        input_file=input_file,
        api_key=api_key,
        dry_run=dry_run,
        add_types=add_types,
        types_only=types_only,
        subjects_file=subjects_file,
        workers=workers,
        retries=retries,
    )
    patch_run(options)

"""CLI wrapper for delete-entities-from-csv."""

from __future__ import annotations

import typer

from worai.core.delete_entities_from_csv import DeleteEntitiesOptions, delete_entities
from worai.core.wordlift import resolve_api_key
from worai.errors import UsageError

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    csv_file: str = typer.Argument(..., help="CSV file with IRIs (first column)."),
    batch_size: int = typer.Option(10, "--batch-size", help="Number of IRIs to delete per batch."),
) -> None:
    api_key = resolve_api_key(ctx.obj.get("config") if ctx.obj else None)
    if not api_key:
        raise UsageError("WORDLIFT_KEY is required (or set wordlift.api_key in config).")

    options = DeleteEntitiesOptions(api_key=api_key, csv_file=csv_file, batch_size=batch_size)
    delete_entities(options)

"""CLI wrapper for find-missing-names."""

from __future__ import annotations

import sys

import typer

from worai.core.find_missing_names import run as find_run

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def run(
    file_path: str = typer.Argument(..., help="Path to RDF file."),
) -> None:
    try:
        results = find_run(file_path)
    except FileNotFoundError:
        typer.echo(f"Error: The file '{file_path}' was not found.", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"An error occurred while parsing the file: {exc}", err=True)
        raise typer.Exit(code=1)

    if results:
        typer.echo(
            f"Found URLs for {len(results)} schema:CollectionPage entities without a 'schema:name' or 'schema:headline':"
        )
        typer.echo("-" * 80)
        for url in results:
            typer.echo(url)
    else:
        typer.echo("No schema:CollectionPage entities are missing both 'schema:name' and 'schema:headline'.")

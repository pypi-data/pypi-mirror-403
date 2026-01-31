"""CLI wrapper for find-url-by-type."""

from __future__ import annotations

import typer

from worai.core.find_url_by_type import FindUrlByTypeOptions, find_urls, resolve_types

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def run(
    filename: str = typer.Argument(..., help="Path to Turtle (.ttl) graph file."),
    types: list[str] = typer.Argument(..., help="One or more schema types (schema:Service)."),
    show_id: bool = typer.Option(False, "--show-id", help="Print subject URI instead of schema:url."),
) -> None:
    try:
        resolved = resolve_types(types)
        if not resolved:
            typer.echo("No valid schema types provided for filtering.", err=True)
            raise typer.Exit(code=1)
        results = find_urls(FindUrlByTypeOptions(filename=filename, types=types, show_id=show_id))
    except FileNotFoundError:
        typer.echo(f"Error: File not found at '{filename}'.", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"Error parsing graph file '{filename}': {exc}", err=True)
        raise typer.Exit(code=1)

    if not results:
        typer.echo("No schema:url found for the specified types in the graph.")
        return

    for subject, url in results:
        typer.echo(subject if show_id else url)

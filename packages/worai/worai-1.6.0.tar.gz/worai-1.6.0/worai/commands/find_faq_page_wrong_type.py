"""CLI wrapper for find-faq-page-wrong-type."""

from __future__ import annotations

import os
import typer

from worai.core.find_faq_page_wrong_type import FaqFixOptions, run as faq_run
from worai.core.wordlift import resolve_api_key
from worai.errors import UsageError

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    file_path: str = typer.Argument(..., help="Path to Turtle RDF file."),
    patch: bool = typer.Option(False, "--patch", help="Execute live API patch calls."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be patched."),
    replace_type: bool = typer.Option(False, "--replace-type", help="Remove existing types before adding FAQPage."),
) -> None:
    mode = "find"
    if patch:
        mode = "patch"
    elif dry_run:
        mode = "dry-run"

    api_key = None
    if mode == "patch":
        api_key = resolve_api_key(ctx.obj.get("config") if ctx.obj else None) or os.environ.get("WORDLIFT_API_KEY")
        if not api_key:
            raise UsageError("WORDLIFT_KEY is required for --patch (or set wordlift.api_key in config).")

    options = FaqFixOptions(
        file_path=file_path,
        mode=mode,
        replace_type=replace_type,
        api_key=api_key,
    )
    faq_run(options)

"""CLI wrapper for upload-entities-from-turtle."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from worai.core.upload_entities_from_turtle import UploadOptions, run as upload_run
from worai.core.wordlift import resolve_api_key
from worai.errors import UsageError

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    folder: Path = typer.Argument(..., help="Folder containing .ttl/.turtle files."),
    recursive: bool = typer.Option(False, "--recursive", help="Search for files recursively."),
    limit: int = typer.Option(0, "--limit", help="Max number of files to upload (0 = no limit)."),
    state_file: Path | None = typer.Option(
        None,
        "--state-file",
        help="Path to resume state file (default: <folder>/.entities_upload_state.json)",
    ),
    base_url: str = typer.Option("https://api.wordlift.io", "--base-url", help="WordLift API base URL."),
    api_key: str | None = typer.Option(None, "--api-key", help="WordLift API key."),
) -> None:
    resolved_key = api_key or resolve_api_key(ctx.obj.get("config") if ctx.obj else None) or os.environ.get("WORDLIFT_API_KEY")
    if not resolved_key:
        raise UsageError("Missing API key. Set WORDLIFT_KEY/WORDLIFT_API_KEY or use --api-key.")

    folder_path = folder.expanduser().resolve()
    if not folder_path.exists() or not folder_path.is_dir():
        raise UsageError(f"Folder not found: {folder_path}")

    options = UploadOptions(
        folder=folder_path,
        recursive=recursive,
        limit=limit,
        state_file=state_file.expanduser().resolve() if state_file else None,
        base_url=base_url,
        api_key=resolved_key,
    )
    exit_code = upload_run(options)
    raise typer.Exit(code=exit_code)

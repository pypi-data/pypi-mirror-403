"""CLI wrapper for dedupe."""

from __future__ import annotations

import typer

from worai.core.dedupe import DedupeOptions, run as dedupe_run
from worai.core.wordlift import resolve_api_key, DEFAULT_GRAPHQL_ENDPOINT
from worai.errors import UsageError

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    endpoint: str = typer.Option(DEFAULT_GRAPHQL_ENDPOINT, "--endpoint", help="GraphQL endpoint URL."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show delete calls without executing them."),
    rate_delay: float = typer.Option(0.0, "--rate-delay", help="Seconds to sleep between delete calls."),
    auto: bool = typer.Option(False, "--auto", help="Automatically keep the last IRI in each group."),
) -> None:
    api_key = resolve_api_key(ctx.obj.get("config") if ctx.obj else None)
    if not api_key:
        raise UsageError("WORDLIFT_KEY is required (or set wordlift.api_key in config).")

    options = DedupeOptions(
        api_key=api_key,
        endpoint=endpoint,
        dry_run=dry_run,
        rate_delay=rate_delay,
        auto=auto,
    )
    dedupe_run(options)

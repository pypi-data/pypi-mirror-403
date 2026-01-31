"""CLI wrapper for canonicalize-duplicate-pages."""

from __future__ import annotations

import typer

from worai.core.canonicalize_duplicate_pages import CanonicalizeOptions, run as canonicalize_run
from worai.core.wordlift import DEFAULT_GRAPHQL_ENDPOINT, resolve_api_key
from worai.errors import UsageError

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    input_csv: str = typer.Option(..., "--input", help="Input GSC CSV from worai google-search-console."),
    output_csv: str = typer.Option("canonical_targets.csv", "--output", help="Output CSV path."),
    url_regex: str | None = typer.Option(None, "--url-regex", help="Regex to filter URLs of interest."),
    entity_type: str | None = typer.Option(
        None,
        "--entity-type",
        help="Expected schema type when multiple entities share the same URL (e.g., Product).",
    ),
    endpoint: str = typer.Option(DEFAULT_GRAPHQL_ENDPOINT, "--endpoint", help="WordLift GraphQL endpoint."),
    batch_size: int = typer.Option(25, "--batch-size", help="Batch size for GraphQL queries."),
    kpi_window: str = typer.Option("28d", "--kpi-window", help="KPI time window (7d, 28d, 3m)."),
    kpi_metric: str = typer.Option("clicks", "--kpi-metric", help="KPI metric (clicks, impressions, ctr)."),
) -> None:
    api_key = resolve_api_key(ctx.obj.get("config") if ctx.obj else None)
    if not api_key:
        raise UsageError("WORDLIFT_KEY is required (or set wordlift.api_key in config).")

    options = CanonicalizeOptions(
        api_key=api_key,
        input_csv=input_csv,
        output_csv=output_csv,
        url_regex=url_regex,
        entity_type=entity_type,
        endpoint=endpoint,
        batch_size=batch_size,
        kpi_window=kpi_window,
        kpi_metric=kpi_metric,
    )
    canonicalize_run(options)

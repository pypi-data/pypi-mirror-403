"""CLI wrapper for listing entities outside the account dataset."""

from __future__ import annotations

import typer

from worai.core.prune_entities_outside_dataset import (
    DEFAULT_BASE_URL,
    DEFAULT_QUERY_TEMPLATE,
    ListOptions,
    run,
)
from worai.core.wordlift import DEFAULT_GRAPHQL_ENDPOINT, resolve_api_key
from worai.errors import UsageError

app = typer.Typer(add_completion=False, no_args_is_help=False, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    dataset_uri: str | None = typer.Option(
        None, "--dataset-uri", help="Dataset URI override (defaults to account get_me)."
    ),
    endpoint: str = typer.Option(
        DEFAULT_GRAPHQL_ENDPOINT, "--endpoint", help="WordLift GraphQL endpoint."
    ),
    base_url: str = typer.Option(DEFAULT_BASE_URL, "--base-url", help="WordLift API base URL."),
    limit: int = typer.Option(0, "--limit", help="Limit number of entities to list."),
    query_template: str = typer.Option(
        DEFAULT_QUERY_TEMPLATE,
        "--query-template",
        help="GraphQL query template with {dataset_uri} placeholder.",
    ),
) -> None:
    api_key = resolve_api_key(ctx.obj.get("config") if ctx.obj else None)
    if not api_key:
        raise UsageError("WORDLIFT_KEY is required (or set wordlift.api_key in config).")

    options = ListOptions(
        api_key=api_key,
        graphql_endpoint=endpoint,
        base_url=base_url,
        query_template=query_template,
        dataset_uri=dataset_uri,
        limit=limit,
    )
    run(options)

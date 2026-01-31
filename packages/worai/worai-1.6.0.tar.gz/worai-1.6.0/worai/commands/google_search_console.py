"""CLI wrapper for Google Search Console export."""

from __future__ import annotations

import os

import typer

from worai.core.gsc import GscOptions, run as gsc_run
from worai.errors import UsageError

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


def _resolve_value(
    ctx: typer.Context,
    value: str | None,
    path: str,
    env_key: str | None,
) -> str | None:
    if value:
        return value
    if env_key and env_key in os.environ:
        return os.environ[env_key]
    config = ctx.obj.get("config") if ctx.obj else None
    if config:
        return config.get(path)
    return None


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    site: str = typer.Option(..., "--site", help="GSC property to query."),
    client_secrets: str | None = typer.Option(None, "--client-secrets", help="OAuth2 client secrets JSON."),
    token: str | None = typer.Option(None, "--token", help="Path to store OAuth2 token."),
    port: int = typer.Option(0, "--port", help="Local redirect port for OAuth flow."),
    output: str | None = typer.Option(None, "--output", help="Output CSV path."),
    row_limit: int = typer.Option(25000, "--row-limit", help="Row limit for GSC API pagination."),
    search_type: str = typer.Option("web", "--type", help="Search type."),
    data_state: str = typer.Option("all", "--data-state", help="Data state to query."),
) -> None:
    resolved_client_secrets = _resolve_value(
        ctx,
        client_secrets,
        "gsc.client_secrets",
        "GSC_CLIENT_SECRETS",
    )
    resolved_token = _resolve_value(ctx, token, "gsc.token", "GSC_TOKEN") or "gsc_token.json"
    resolved_output = _resolve_value(ctx, output, "gsc.output", "GSC_OUTPUT") or "gsc_pages.csv"

    if not resolved_client_secrets:
        raise UsageError("--client-secrets is required (or set gsc.client_secrets in config).")

    options = GscOptions(
        site=site,
        client_secrets=resolved_client_secrets,
        token=resolved_token,
        port=port,
        output=resolved_output,
        row_limit=row_limit,
        search_type=search_type,
        data_state=data_state,
    )
    gsc_run(options)

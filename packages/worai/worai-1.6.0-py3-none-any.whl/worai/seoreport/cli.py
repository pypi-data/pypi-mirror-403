"""SEO Report CLI entry point."""

import os
from pathlib import Path
from typing import Optional

import typer
from jinja2 import Environment, FileSystemLoader

from worai.seoreport.core import ReportOptions, generate_report_data

app = typer.Typer(add_completion=False, no_args_is_help=True)

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
    site: str = typer.Option(..., "--site", help="GSC property URL."),
    url_regex: Optional[str] = typer.Option(None, "--url-regex", help="Regex to filter URLs."),
    output: Optional[str] = typer.Option(None, "--output", help="Output file path."),
    format: str = typer.Option("markdown", "--format", help="Output format: markdown or html."),
    client_secrets: Optional[str] = typer.Option(None, "--client-secrets", help="OAuth2 client secrets JSON."),
    token: Optional[str] = typer.Option(None, "--token", help="Path to store OAuth2 token."),
    port: int = typer.Option(0, "--port", help="Local redirect port for OAuth flow."),
    inspect_limit: int = typer.Option(10, "--inspect-limit", help="Number of top pages to inspect (GSC Quota)."),
) -> None:
    """Generate SEO performance report."""
    
    # Resolve credentials/config
    resolved_client_secrets = _resolve_value(
        ctx,
        client_secrets,
        "gsc.client_secrets",
        "GSC_CLIENT_SECRETS",
    )
    resolved_token = _resolve_value(ctx, token, "gsc.token", "GSC_TOKEN") or "gsc_token.json"
    
    # Default output filename
    if not output:
        ext = "html" if format == "html" else "md"
        timestamp = generate_timestamp_str()
        output = f"seo_report_{timestamp}.{ext}"

    options = ReportOptions(
        site=site,
        url_regex=url_regex,
        client_secrets=resolved_client_secrets,
        token=resolved_token,
        port=port,
        output=output,
        format=format,
        inspect_limit=inspect_limit
    )

    typer.echo(f"Generating {format} report for {site}...")
    
    try:
        data = generate_report_data(options)
        
        # Render
        template_dir = Path(__file__).parent / "templates"
        env = Environment(loader=FileSystemLoader(template_dir))
        
        template_name = "report.html" if format == "html" else "report.md"
        template = env.get_template(template_name)
        
        rendered = template.render(data=data)
        
        with open(output, "w", encoding="utf-8") as f:
            f.write(rendered)
            
        typer.echo(f"Report saved to: {output}")
        
    except Exception as e:
        typer.echo(f"Error generating report: {e}", err=True)
        raise typer.Exit(code=1)

def generate_timestamp_str():
    import datetime
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
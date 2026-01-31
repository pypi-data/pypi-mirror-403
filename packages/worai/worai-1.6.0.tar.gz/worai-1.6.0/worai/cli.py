"""WORAi root CLI."""

from __future__ import annotations

import logging

import typer

from worai.config import load_config
from worai.errors import WoraError
from worai.logging import setup_logging

app = typer.Typer(add_completion=True, no_args_is_help=True)


@app.callback()
def main(
    ctx: typer.Context,
    config: str | None = typer.Option(None, "--config", help="Path to config TOML."),
    profile: str | None = typer.Option(None, "--profile", help="Config profile name."),
    log_level: str = typer.Option("info", "--log-level", help="Log level."),
    log_format: str = typer.Option("text", "--log-format", help="Log format: text or json."),
    quiet: bool = typer.Option(False, "--quiet", help="Only warnings and errors."),
) -> None:
    """WORAi command-line tools."""
    setup_logging(level=log_level, fmt=log_format, quiet=quiet)
    ctx.obj = {
        "config": load_config(config, profile),
        "log_level": log_level,
        "log_format": log_format,
        "quiet": quiet,
    }


@app.command("version")
def version() -> None:
    """Print version."""
    from worai import __version__

    typer.echo(__version__)


def _install_commands() -> None:
    from worai.commands import (
        canonicalize_duplicate_pages,
        delete_entities_from_csv,
        dedupe,
        find_faq_page_wrong_type,
        find_missing_names,
        find_url_by_type,
        google_search_console,
        link_groups,
        list_entities_outside_dataset,
        patch,
        seocheck,
        structured_data,
        upload_entities_from_turtle,
        validate,
    )
    from worai.seoreport import cli as seoreport_cli

    app.command("seocheck", help="Run SEO checks on a sitemap or URL list.")(seocheck.run)
    app.add_typer(
        seoreport_cli.app,
        name="seoreport",
        help="Generate SEO performance report.",
    )
    app.add_typer(
        google_search_console.app,
        name="google-search-console",
        help="Export Google Search Console data to CSV.",
    )
    app.add_typer(dedupe.app, name="dedupe", help="Deduplicate entities by schema:url.")
    app.add_typer(
        canonicalize_duplicate_pages.app,
        name="canonicalize-duplicate-pages",
        help="Suggest canonical targets for duplicate pages.",
    )
    app.add_typer(
        delete_entities_from_csv.app,
        name="delete-entities-from-csv",
        help="Delete entities listed in a CSV file.",
    )
    app.add_typer(
        find_faq_page_wrong_type.app,
        name="find-faq-page-wrong-type",
        help="Find FAQPage entities with the wrong type and patch them.",
    )
    app.add_typer(
        find_missing_names.app,
        name="find-missing-names",
        help="Find entities missing schema:name in a Turtle file.",
    )
    app.add_typer(
        find_url_by_type.app,
        name="find-url-by-type",
        help="List URLs by schema type from a Turtle file.",
    )
    app.add_typer(link_groups.app, name="link-groups", help="Convert or apply internal link groups.")
    app.add_typer(patch.app, name="patch", help="Patch entities from RDF (Turtle/JSON-LD).")
    app.add_typer(
        structured_data.app,
        name="structured-data",
        help="Generate structured data mappings or materialize RDF from YARRRML.",
    )
    app.add_typer(
        list_entities_outside_dataset.app,
        name="list-entities-outside-dataset",
        help="List entities not belonging to the account dataset.",
    )
    app.add_typer(
        upload_entities_from_turtle.app,
        name="upload-entities-from-turtle",
        help="Upload Turtle entities with resume support.",
    )
    app.add_typer(validate.app, name="validate", help="Validate RDF data using SHACL shapes.")


_install_commands()


def run() -> None:
    try:
        app()
    except WoraError as exc:
        logging.getLogger("worai").error(str(exc))
        raise SystemExit(exc.exit_code) from exc


if __name__ == "__main__":
    run()

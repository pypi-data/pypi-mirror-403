"""CLI wrapper for seocheck."""

from __future__ import annotations

import typer

from worai.seocheck import cli as seocheck_cli


def run(
    sitemap_url: str = typer.Argument(..., help="URL or local path to sitemap XML."),
    max_urls: int | None = typer.Option(None, "--max-urls", help="Limit number of URLs checked."),
    timeout: float = typer.Option(20.0, "--timeout", help="Timeout (seconds) for HTTP requests."),
    user_agent: str = typer.Option(
        seocheck_cli.DEFAULT_USER_AGENT,
        "--user-agent",
        help="User-Agent header for HTTP requests.",
    ),
    sitemap_fetch_mode: str = typer.Option(
        "auto",
        "--sitemap-fetch-mode",
        help="How to fetch sitemaps: requests, browser (Playwright), or auto.",
    ),
    page_timeout: int = typer.Option(30000, "--page-timeout", help="Timeout (ms) for browser page loads."),
    wait_until: str = typer.Option(
        "domcontentloaded",
        "--wait-until",
        help="Playwright wait strategy.",
    ),
    ttfb_ok_ms: float = typer.Option(200.0, "--ttfb-ok-ms", help="TTFB ok threshold in ms."),
    ttfb_warn_ms: float = typer.Option(500.0, "--ttfb-warn-ms", help="TTFB warn threshold in ms."),
    headed: bool = typer.Option(False, "--headed", help="Run the browser with a visible UI."),
    output_format: str = typer.Option("text", "--format", help="Output format: text or json."),
    output_dir: str | None = typer.Option(
        None,
        "--output-dir",
        help="Write report outputs to this directory.",
    ),
    concurrency: str = typer.Option(
        "1",
        "--concurrency",
        help="Number of pages to process concurrently, or 'auto'.",
    ),
    output: str | None = typer.Option(None, "--output", help="Write JSON report to this file path."),
    output_summary: str | None = typer.Option(
        None,
        "--output-summary",
        help="Write summary report to this file path.",
    ),
    save_html: bool = typer.Option(False, "--save-html", help="Save rendered HTML per page."),
    no_report_ui: bool = typer.Option(
        False,
        "--no-report-ui",
        help="Do not serve or open the HTML report UI.",
    ),
    checks: str | None = typer.Option(
        None,
        "--checks",
        help="Comma-separated list of page check names to run (others disabled).",
    ),
    disable_checks: str | None = typer.Option(
        None,
        "--disable-checks",
        help="Comma-separated list of page check names to skip.",
    ),
    recheck_failed: bool = typer.Option(
        False,
        "--recheck-failed",
        help="Recheck only failed or warned URLs from a previous report.",
    ),
    recheck_from: str | None = typer.Option(
        None,
        "--recheck-from",
        help="Path to report.json (or output dir containing it) for --recheck-failed.",
    ),
) -> None:
    argv: list[str] = [sitemap_url]
    if max_urls is not None:
        argv += ["--max-urls", str(max_urls)]
    argv += ["--timeout", str(timeout)]
    argv += ["--user-agent", user_agent]
    argv += ["--sitemap-fetch-mode", sitemap_fetch_mode]
    argv += ["--page-timeout", str(page_timeout)]
    argv += ["--wait-until", wait_until]
    argv += ["--ttfb-ok-ms", str(ttfb_ok_ms)]
    argv += ["--ttfb-warn-ms", str(ttfb_warn_ms)]
    if headed:
        argv.append("--headed")
    argv += ["--format", output_format]
    if output_dir is not None:
        argv += ["--output-dir", output_dir]
    argv += ["--concurrency", concurrency]
    if output is not None:
        argv += ["--output", output]
    if output_summary is not None:
        argv += ["--output-summary", output_summary]
    if save_html:
        argv.append("--save-html")
    if no_report_ui:
        argv.append("--no-report-ui")
    if checks is not None:
        argv += ["--checks", checks]
    if disable_checks is not None:
        argv += ["--disable-checks", disable_checks]
    if recheck_failed:
        argv.append("--recheck-failed")
    if recheck_from is not None:
        argv += ["--recheck-from", recheck_from]

    raise typer.Exit(code=seocheck_cli.run(argv))

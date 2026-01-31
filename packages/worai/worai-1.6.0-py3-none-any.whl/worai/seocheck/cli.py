from __future__ import annotations

import argparse
import hashlib
import json
import time
import http.server
import webbrowser
from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import sys
from dataclasses import asdict
from typing import Iterable

import requests

from .browser import Browser
from .checks import CheckResult, get_page_checks
from .checks.llms_txt import check_llms_txt
from .checks.robots_txt import check_robots_txt
from .sitemap import get_base_url, parse_sitemap_urls

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _print_site_results(results: Iterable[dict], *, as_json: bool) -> None:
    if as_json:
        for result in results:
            print(json.dumps(result, ensure_ascii=True))
        return
    for result in results:
        print(f"SITE {result['name']}: {result['status']} - {result['details']}")
        print(f"  {result['url']}")


def _print_page_results(url: str, results: list[CheckResult], *, as_json: bool) -> None:
    if as_json:
        payload = {
            "type": "page",
            "url": url,
            "checks": [asdict(result) for result in results],
        }
        print(json.dumps(payload, ensure_ascii=True))
        return
    print(f"URL {url}")
    for result in results:
        details = f" - {result.details}" if result.details else ""
        print(f"  {result.name}: {result.status}{details}")


def _write_json_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2))


def _write_summary(path: Path, site_results: list[dict], page_results: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("SEO Check Summary")
    lines.append("")
    if site_results:
        lines.append("Site Checks")
        for result in site_results:
            lines.append(f"- {result['name']}: {result['status']} - {result['details']}")
            lines.append(f"  {result['url']}")
        lines.append("")
    if page_results:
        lines.append("Page Checks")
        for page in page_results:
            lines.append(f"URL {page['url']}")
            for check in page["checks"]:
                details = f" - {check.get('details')}" if check.get("details") else ""
                lines.append(f"  {check['name']}: {check['status']}{details}")
    path.write_text("\n".join(lines))


def _hash_url(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _status_rank(status: str | None) -> int:
    if status == "fail":
        return 3
    if status == "warn":
        return 2
    if status == "ok":
        return 1
    return 0


def _aggregate_counts(site_results: list[dict], page_summaries: list[dict]) -> dict:
    def init_counts() -> dict:
        return {"ok": 0, "warn": 0, "fail": 0}

    site_counts = init_counts()
    site_by_name: dict[str, dict] = {}
    for result in site_results:
        status = result.get("status")
        if status in site_counts:
            site_counts[status] += 1
        name = result.get("name", "unknown")
        site_by_name.setdefault(name, init_counts())
        if status in site_by_name[name]:
            site_by_name[name][status] += 1

    page_counts = init_counts()
    page_by_check: dict[str, dict] = {}
    for page in page_summaries:
        status = page.get("status")
        if status in page_counts:
            page_counts[status] += 1
        for check in page.get("checks", []):
            check_name = check.get("name", "unknown")
            page_by_check.setdefault(check_name, init_counts())
            check_status = check.get("status")
            if check_status in page_by_check[check_name]:
                page_by_check[check_name][check_status] += 1

    return {
        "site": {"total": len(site_results), "by_status": site_counts, "by_check": site_by_name},
        "pages": {"total": len(page_summaries), "by_status": page_counts, "by_check": page_by_check},
    }


def _copy_report_assets(output_dir: Path) -> None:
    template_dir = Path(__file__).parent / "report_template"
    for name in ["index.html", "app.js", "styles.css"]:
        source = template_dir / name
        target = output_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text())


def _derive_page_status(checks: list[dict]) -> str:
    status = "ok"
    for result in checks:
        if _status_rank(result.get("status")) > _status_rank(status):
            status = result.get("status")
    return status


def _load_failed_urls(recheck_from: str) -> set[str]:
    path = Path(recheck_from)
    if path.is_dir():
        path = path / "report.json"
    if not path.exists():
        raise RuntimeError(f"Recheck report not found: {path}")
    payload = json.loads(path.read_text())
    pages = payload.get("pages", [])
    failed_urls: set[str] = set()
    for page in pages:
        url = page.get("url")
        if not url:
            continue
        status = page.get("status")
        if status in {"fail", "warn"}:
            failed_urls.add(url)
            continue
        for check in page.get("checks", []):
            if check.get("status") in {"fail", "warn"}:
                failed_urls.add(url)
                break
    return failed_urls


def _serve_report(output_dir: Path, *, open_browser: bool) -> None:
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(output_dir))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    host, port = httpd.server_address
    url = f"http://{host}:{port}/index.html"
    if open_browser:
        webbrowser.open(url)
    print(f"Report server running at {url} (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()


def _process_url(
    url: str,
    *,
    page_checks: list,
    output_dir: Path | None,
    save_html: bool,
    headless: bool,
    page_timeout: int,
    wait_until: str,
    retries: int = 1,
) -> tuple[dict, dict, bool]:
    pages_dir = output_dir / "pages" if output_dir else None
    html_dir = output_dir / "html" if output_dir else None

    response = None
    error_flag = False
    with Browser(headless=headless, timeout_ms=page_timeout, wait_until=wait_until) as browser:
        page = None
        resources = []
        elapsed_ms = 0.0
        for attempt in range(retries + 1):
            page, response, elapsed_ms, resources = browser.open(url)
            if response is not None or attempt >= retries:
                break
            if page is not None:
                page.close()
            time.sleep(0.5)

        if response is None:
            error_flag = True

        results = []
        for check in page_checks:
            try:
                result = check.run(
                    page=page,
                    response=response,
                    elapsed_ms=elapsed_ms,
                    resources=resources,
                )
            except Exception as exc:
                result = CheckResult(
                    name=getattr(check, "name", "unknown"),
                    status="fail",
                    details=f"check failed: {exc}",
                )
            results.append(result)

        if page is not None:
            if save_html and html_dir is not None:
                html_dir.mkdir(parents=True, exist_ok=True)
                page_html = page.content()
                html_path = html_dir / f"{_hash_url(url)}.html"
                html_path.write_text(page_html)
            page.close()

    page_payload = {
        "type": "page",
        "url": url,
        "checks": [asdict(result) for result in results],
    }

    page_file = None
    if pages_dir is not None:
        pages_dir.mkdir(parents=True, exist_ok=True)
        page_file = f"pages/{_hash_url(url)}.json"
        (output_dir / page_file).write_text(json.dumps(page_payload, ensure_ascii=True, indent=2))

    html_file = None
    if save_html and html_dir is not None:
        html_file = f"html/{_hash_url(url)}.html"

    page_summary = {
        "url": url,
        "status": _derive_page_status(page_payload["checks"]),
        "file": page_file,
        "html": html_file,
        "checks": page_payload["checks"],
    }

    return page_payload, page_summary, error_flag


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run SEO checks against URLs found in a sitemap.xml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  worai seocheck https://example.com/sitemap.xml\n"
            "  worai seocheck ./sitemap.xml\n"
            "  worai seocheck /path/to/sitemap.xml.gz\n"
            "  worai seocheck https://example.com/sitemap.xml --wait-until networkidle\n"
            "  worai seocheck https://example.com/sitemap.xml --max-urls 25 --format json\n"
            "  worai seocheck https://example.com/sitemap.xml --output-dir ./seocheck-report\n"
            "  worai seocheck https://example.com/sitemap.xml --output-dir ./seocheck-report --save-html\n"
            "  worai seocheck https://example.com/sitemap.xml --recheck-failed --recheck-from ./seocheck-report\n"
        ),
    )
    parser.add_argument("sitemap_url", help="URL to sitemap.xml or sitemap index")
    parser.add_argument("--max-urls", type=int, default=None, help="Limit number of URLs checked")
    parser.add_argument("--timeout", type=float, default=20.0, help="Timeout (seconds) for HTTP requests")
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="User-Agent header for HTTP requests (sitemaps, robots.txt, llms.txt)",
    )
    parser.add_argument(
        "--sitemap-fetch-mode",
        default="auto",
        choices=["requests", "browser", "auto"],
        help="How to fetch sitemaps: requests, browser (Playwright), or auto (fallback to browser).",
    )
    parser.add_argument(
        "--page-timeout",
        type=int,
        default=30000,
        help="Timeout (ms) for browser page loads",
    )
    parser.add_argument(
        "--wait-until",
        default="domcontentloaded",
        choices=["domcontentloaded", "load", "networkidle"],
        help="Playwright wait strategy",
    )
    parser.add_argument("--ttfb-ok-ms", type=float, default=200.0, help="TTFB ok threshold in ms")
    parser.add_argument("--ttfb-warn-ms", type=float, default=500.0, help="TTFB warn threshold in ms")
    parser.add_argument("--headed", action="store_true", help="Run the browser with a visible UI")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Write report outputs to this directory (report.json, summary.txt, per-page JSONs)",
    )
    parser.add_argument(
        "--concurrency",
        default="1",
        help="Number of pages to process concurrently, or 'auto' (default: 1)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write a comprehensive JSON report to this file path",
    )
    parser.add_argument(
        "--output-summary",
        default=None,
        help="Write a human-readable summary report to this file path",
    )
    parser.add_argument(
        "--save-html",
        action="store_true",
        help="Save rendered HTML for each page to the output directory",
    )
    parser.add_argument(
        "--no-open-report",
        action="store_true",
        help="Do not open the HTML report in a browser",
    )
    parser.add_argument(
        "--no-serve-report",
        action="store_true",
        help="Do not start a local web server for the HTML report",
    )
    parser.add_argument(
        "--no-report-ui",
        action="store_true",
        help="Do not serve or open the HTML report UI",
    )
    parser.add_argument(
        "--checks",
        default=None,
        help="Comma-separated list of page check names to run (others disabled)",
    )
    parser.add_argument(
        "--disable-checks",
        default=None,
        help="Comma-separated list of page check names to skip",
    )
    parser.add_argument(
        "--recheck-failed",
        action="store_true",
        help="Recheck only failed or warned URLs from a previous report",
    )
    parser.add_argument(
        "--recheck-from",
        default=None,
        help="Path to report.json (or output dir containing it) for --recheck-failed",
    )
    args = parser.parse_args(argv)
    if args.no_report_ui:
        args.no_open_report = True
        args.no_serve_report = True

    if args.recheck_failed and args.output_dir is None and args.recheck_from:
        recheck_path = Path(args.recheck_from)
        if recheck_path.is_dir():
            args.output_dir = str(recheck_path)
        else:
            args.output_dir = str(recheck_path.parent)

    session = requests.Session()
    session.headers.update({"User-Agent": args.user_agent, "Referer": "https://wordlift.io"})

    try:
        urls = parse_sitemap_urls(
            args.sitemap_url,
            session=session,
            timeout=args.timeout,
            fetch_mode=args.sitemap_fetch_mode,
            user_agent=args.user_agent,
            browser_timeout_ms=args.page_timeout,
            browser_wait_until=args.wait_until,
            max_urls=args.max_urls,
        )
    except Exception as exc:
        print(f"Failed to parse sitemap: {exc}", file=sys.stderr)
        return 1

    if not urls:
        print("No URLs found in sitemap", file=sys.stderr)
        return 1

    previous_report = None
    if args.recheck_failed:
        recheck_from = args.recheck_from or args.output_dir
        if not recheck_from:
            print(
                "Use --recheck-from or --output-dir with --recheck-failed.",
                file=sys.stderr,
            )
            return 1
        try:
            previous_report_path = Path(recheck_from)
            if previous_report_path.is_dir():
                previous_report_path = previous_report_path / "report.json"
            previous_report = json.loads(previous_report_path.read_text())
            failed_urls = _load_failed_urls(recheck_from)
        except Exception as exc:
            print(f"Failed to load recheck report: {exc}", file=sys.stderr)
            return 1
        if not failed_urls:
            print("No failed URLs found in the recheck report", file=sys.stderr)
            return 0
        urls = [url for url in urls if url in failed_urls]
        if not urls:
            print("No failed URLs found in the current sitemap", file=sys.stderr)
            return 0

    base_urls = {get_base_url(url) for url in urls}

    site_results = []
    for base_url in sorted(base_urls):
        robots_result = check_robots_txt(base_url, session=session, timeout=args.timeout)
        site_results.append(
            {
                "type": "site",
                "name": "robots.txt",
                "url": robots_result.url,
                "status": robots_result.status,
                "details": robots_result.details,
                "data": {
                    "status_code": robots_result.status_code,
                    "disallow_all": robots_result.disallow_all,
                },
            }
        )

        llms_result = check_llms_txt(base_url, session=session, timeout=args.timeout)
        site_results.append(
            {
                "type": "site",
                "name": "llms.txt",
                "url": llms_result.url,
                "status": llms_result.status,
                "details": llms_result.details,
                "data": {
                    "status_code": llms_result.status_code,
                },
            }
        )

    _print_site_results(site_results, as_json=args.format == "json")

    page_checks = get_page_checks(
        ttfb_ok_ms=args.ttfb_ok_ms,
        ttfb_warn_ms=args.ttfb_warn_ms,
    )
    available_checks = {check.name for check in page_checks}
    selected = set(available_checks)
    if args.checks:
        requested = {name.strip() for name in args.checks.split(",") if name.strip()}
        unknown = requested - available_checks
        if unknown:
            print(f"Unknown check(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 1
        selected = requested
    if args.disable_checks:
        disabled = {name.strip() for name in args.disable_checks.split(",") if name.strip()}
        unknown = disabled - available_checks
        if unknown:
            print(f"Unknown check(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 1
        selected = selected - disabled
    page_checks = [check for check in page_checks if check.name in selected]

    page_results: list[dict] = []
    page_summaries: list[dict] = []
    output_dir = Path(args.output_dir) if args.output_dir else None
    pages_dir = output_dir / "pages" if output_dir else None
    html_dir = output_dir / "html" if output_dir else None

    try:
        auto_concurrency = str(args.concurrency).lower() == "auto"
        if not auto_concurrency:
            try:
                concurrency = int(args.concurrency)
            except ValueError:
                print("Invalid --concurrency value. Use an integer or 'auto'.", file=sys.stderr)
                return 1
        else:
            concurrency = 1

        if concurrency <= 1 and not auto_concurrency:
            with Browser(
                headless=not args.headed,
                timeout_ms=args.page_timeout,
                wait_until=args.wait_until,
            ) as browser:
                for url in urls:
                    page = None
                    response = None
                    resources = []
                    elapsed_ms = 0.0
                    for attempt in range(2):
                        page, response, elapsed_ms, resources = browser.open(url)
                        if response is not None or attempt == 1:
                            break
                        if page is not None:
                            page.close()
                        time.sleep(0.5)

                    results = []
                    for check in page_checks:
                        try:
                            result = check.run(
                                page=page,
                                response=response,
                                elapsed_ms=elapsed_ms,
                                resources=resources,
                            )
                        except Exception as exc:
                            result = CheckResult(
                                name=getattr(check, "name", "unknown"),
                                status="fail",
                                details=f"check failed: {exc}",
                            )
                        results.append(result)
                    if page is not None:
                        if args.save_html and html_dir is not None:
                            html_dir.mkdir(parents=True, exist_ok=True)
                            page_html = page.content()
                            html_path = html_dir / f"{_hash_url(url)}.html"
                            html_path.write_text(page_html)
                        page.close()
                    _print_page_results(url, results, as_json=args.format == "json")
                    page_payload = {
                        "type": "page",
                        "url": url,
                        "checks": [asdict(result) for result in results],
                    }
                    page_results.append(page_payload)

                    page_status = _derive_page_status(page_payload["checks"])

                    page_file = None
                    if pages_dir is not None:
                        pages_dir.mkdir(parents=True, exist_ok=True)
                        page_file = f"pages/{_hash_url(url)}.json"
                        (output_dir / page_file).write_text(
                            json.dumps(page_payload, ensure_ascii=True, indent=2)
                        )

                    html_file = None
                    if args.save_html and html_dir is not None:
                        html_file = f"html/{_hash_url(url)}.html"

                    page_summaries.append(
                        {
                            "url": url,
                            "status": page_status,
                            "file": page_file,
                            "html": html_file,
                            "checks": page_payload["checks"],
                        }
                    )
        elif not auto_concurrency:
            indexed_payloads: list[dict | None] = [None] * len(urls)
            indexed_summaries: list[dict | None] = [None] * len(urls)
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = {
                    executor.submit(
                        _process_url,
                        url,
                        page_checks=page_checks,
                        output_dir=output_dir,
                        save_html=args.save_html,
                        headless=not args.headed,
                        page_timeout=args.page_timeout,
                        wait_until=args.wait_until,
                    ): idx
                    for idx, url in enumerate(urls)
                }
                for future in as_completed(futures):
                    idx = futures[future]
                    url = urls[idx]
                    try:
                        page_payload, page_summary, _ = future.result()
                    except Exception as exc:
                        failure = CheckResult(
                            name="page",
                            status="fail",
                            details=f"page processing failed: {exc}",
                        )
                        page_payload = {"type": "page", "url": url, "checks": [asdict(failure)]}
                        page_summary = {
                            "url": url,
                            "status": "fail",
                            "file": None,
                            "html": None,
                            "checks": page_payload["checks"],
                        }
                    _print_page_results(
                        url,
                        [CheckResult(**check) for check in page_payload["checks"]],
                        as_json=args.format == "json",
                    )
                    indexed_payloads[idx] = page_payload
                    indexed_summaries[idx] = page_summary
            page_results = [item for item in indexed_payloads if item is not None]
            page_summaries = [item for item in indexed_summaries if item is not None]
        else:
            current = 1
            max_concurrency = min(8, max(1, len(urls)))
            idx = 0
            while idx < len(urls):
                batch = urls[idx : idx + current]
                indexed_payloads: list[dict | None] = [None] * len(batch)
                indexed_summaries: list[dict | None] = [None] * len(batch)
                errors = 0
                with ThreadPoolExecutor(max_workers=current) as executor:
                    futures = {
                        executor.submit(
                            _process_url,
                            url,
                            page_checks=page_checks,
                            output_dir=output_dir,
                            save_html=args.save_html,
                            headless=not args.headed,
                            page_timeout=args.page_timeout,
                            wait_until=args.wait_until,
                        ): local_idx
                        for local_idx, url in enumerate(batch)
                    }
                    for future in as_completed(futures):
                        local_idx = futures[future]
                        url = batch[local_idx]
                        try:
                            page_payload, page_summary, had_error = future.result()
                            if had_error:
                                errors += 1
                        except Exception as exc:
                            errors += 1
                            failure = CheckResult(
                                name="page",
                                status="fail",
                                details=f"page processing failed: {exc}",
                            )
                            page_payload = {
                                "type": "page",
                                "url": url,
                                "checks": [asdict(failure)],
                            }
                            page_summary = {
                                "url": url,
                                "status": "fail",
                                "file": None,
                                "html": None,
                                "checks": page_payload["checks"],
                            }
                        _print_page_results(
                            url,
                            [CheckResult(**check) for check in page_payload["checks"]],
                            as_json=args.format == "json",
                        )
                        indexed_payloads[local_idx] = page_payload
                        indexed_summaries[local_idx] = page_summary
                page_results.extend([item for item in indexed_payloads if item is not None])
                page_summaries.extend([item for item in indexed_summaries if item is not None])

                if errors > 0 and current > 1:
                    current -= 1
                elif errors == 0 and current < max_concurrency:
                    current += 1
                idx += len(batch)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if previous_report is not None:
        previous_pages = previous_report.get("pages", [])
        new_by_url = {page.get("url"): page for page in page_summaries if page.get("url")}
        merged_pages: list[dict] = []
        for page in previous_pages:
            url = page.get("url")
            if url in new_by_url:
                merged_pages.append(new_by_url.pop(url))
            else:
                merged_pages.append(page)
        merged_pages.extend(new_by_url.values())
        page_summaries = merged_pages

    aggregate = _aggregate_counts(site_results, page_summaries)
    report_payload = {
        "sitemap": args.sitemap_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site_checks": site_results,
        "pages": page_summaries,
        "aggregate": aggregate,
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        _copy_report_assets(output_dir)
        _write_json_report(output_dir / "report.json", report_payload)
        _write_summary(output_dir / "summary.txt", site_results, page_summaries)

    if args.output:
        _write_json_report(Path(args.output), report_payload)

    if args.output_summary:
        _write_summary(Path(args.output_summary), site_results, page_summaries)

    if output_dir is not None and not args.no_serve_report:
        _serve_report(output_dir, open_browser=not args.no_open_report)

    return 0


if __name__ == "__main__":
    raise SystemExit(run())

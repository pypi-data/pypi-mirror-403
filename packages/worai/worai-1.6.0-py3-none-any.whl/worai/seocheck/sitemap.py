from __future__ import annotations

import gzip
from pathlib import Path
from typing import Iterable, Literal
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import requests

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - runtime dependency
    sync_playwright = None
    PlaywrightError = Exception


def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _parse_xml(content: bytes) -> ET.Element:
    return ET.fromstring(content)


def _decode_content(url: str, response: requests.Response) -> bytes:
    if url.endswith(".gz"):
        return gzip.decompress(response.content)
    content_type = response.headers.get("content-type", "").lower()
    if "application/x-gzip" in content_type or "application/gzip" in content_type:
        return gzip.decompress(response.content)
    return response.content


def _iter_locs(root: ET.Element) -> Iterable[str]:
    for loc in root.findall(".//{*}loc"):
        if loc.text:
            yield loc.text.strip()


def _parse_sitemap_xml(content: bytes) -> tuple[str, list[str]]:
    root = _parse_xml(content)
    root_tag = _strip_ns(root.tag)
    return root_tag, list(_iter_locs(root))


def _read_local_sitemap(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix == ".gz":
        return gzip.decompress(data)
    return data


def _fetch_sitemap_requests(url: str, *, session: requests.Session, timeout: float) -> bytes:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return _decode_content(url, response)

def _fetch_sitemap_browser(
    url: str,
    *,
    timeout_ms: int,
    wait_until: str,
    user_agent: str | None,
) -> bytes:
    if sync_playwright is None:
        raise RuntimeError(
            "Playwright is not installed. Run: uv pip install playwright && playwright install"
        )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context_kwargs: dict[str, object] = {}
        if user_agent:
            context_kwargs["user_agent"] = user_agent
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        response = None
        try:
            response = page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        except PlaywrightError as exc:  # pragma: no cover - runtime dependency
            raise RuntimeError(f"Playwright failed to load sitemap: {exc}") from exc
        if response is None:
            raise RuntimeError("Playwright did not return a response for the sitemap URL")
        status = response.status
        if status >= 400:
            raise RuntimeError(f"Playwright sitemap fetch failed with status {status}")
        content = response.body()
        context.close()
        browser.close()
        return content


def parse_sitemap_urls(
    sitemap_url: str,
    *,
    session: requests.Session,
    timeout: float,
    fetch_mode: Literal["requests", "browser", "auto"] = "requests",
    user_agent: str | None = None,
    browser_timeout_ms: int = 30000,
    browser_wait_until: str = "domcontentloaded",
    max_urls: int | None = None,
) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    queue: list[str] = [sitemap_url]

    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)

        parsed = urlparse(current)
        if parsed.scheme in ("http", "https") or parsed.scheme == "":
            if parsed.scheme == "":
                local_path = Path(current)
                if local_path.exists():
                    content = _read_local_sitemap(local_path)
                else:
                    raise ValueError(f"Local sitemap file not found: {current}")
            else:
                if fetch_mode == "browser":
                    content = _fetch_sitemap_browser(
                        current,
                        timeout_ms=browser_timeout_ms,
                        wait_until=browser_wait_until,
                        user_agent=user_agent,
                    )
                elif fetch_mode == "auto":
                    try:
                        content = _fetch_sitemap_requests(current, session=session, timeout=timeout)
                    except Exception as exc:
                        try:
                            content = _fetch_sitemap_browser(
                                current,
                                timeout_ms=browser_timeout_ms,
                                wait_until=browser_wait_until,
                                user_agent=user_agent,
                            )
                        except Exception as browser_exc:
                            raise RuntimeError(
                                f"Requests sitemap fetch failed: {exc}; "
                                f"Playwright sitemap fetch failed: {browser_exc}"
                            ) from browser_exc
                else:
                    content = _fetch_sitemap_requests(current, session=session, timeout=timeout)
        elif parsed.scheme == "file":
            content = _read_local_sitemap(Path(parsed.path))
        else:
            raise ValueError(f"Unsupported sitemap URL scheme: {parsed.scheme}")
        root_tag, locs = _parse_sitemap_xml(content)

        if root_tag == "sitemapindex":
            queue.extend(locs)
            continue

        if root_tag != "urlset":
            raise ValueError(f"Unsupported sitemap type: {root_tag}")

        for loc in locs:
            if loc not in urls:
                urls.append(loc)
                if max_urls is not None and len(urls) >= max_urls:
                    return urls

    return urls


def get_base_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

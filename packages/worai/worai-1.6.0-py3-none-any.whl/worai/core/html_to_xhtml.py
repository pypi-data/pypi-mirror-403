"""HTML to XHTML conversion and cleanup utilities."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from wordlift_sdk.utils import HtmlConverter
from worai.errors import UsageError
from worai.seocheck.browser import Browser



@dataclass
class RenderOptions:
    url: str
    headless: bool = True
    timeout_ms: int = 30000
    wait_until: str = "networkidle"
    locale: str = "en-US"
    user_agent: str | None = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    viewport_width: int = 1365
    viewport_height: int = 768
    ignore_https_errors: bool = False


@dataclass
class RenderedPage:
    html: str
    xhtml: str
    status_code: int | None = None
    resources: list[dict] = field(default_factory=list)


@dataclass
class CleanupOptions:
    max_xhtml_chars: int = 40000
    max_text_node_chars: int = 400
    remove_tags: tuple[str, ...] = (
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "iframe",
        "form",
        "input",
        "button",
        "nav",
        "aside",
    )





class XhtmlCleaner:
    """Cleans and optimizes XHTML content."""

    def clean(self, xhtml: str, options: CleanupOptions) -> str:
        """
        Clean an XHTML string based on the provided options.

        Args:
            xhtml: The XHTML string to clean.
            options: Configuration for cleaning (tags to remove, max chars, etc.).

        Returns:
            The cleaned XHTML string.
        """
        try:
            from lxml import html as lxml_html
        except Exception as exc:
            raise UsageError(
                "lxml is required for XHTML cleanup. Install with: pip install lxml"
            ) from exc
        parser = lxml_html.HTMLParser(encoding="utf-8", recover=True)
        doc = lxml_html.document_fromstring(xhtml, parser=parser)
        self._strip_unwanted_tags(doc, options.remove_tags)
        self._compact_text_nodes(doc, options.max_text_node_chars)
        self._cap_text_content(doc, options.max_xhtml_chars)
        cleaned = lxml_html.tostring(doc, encoding="unicode", method="xml")
        if len(cleaned) > options.max_xhtml_chars:
            self._trim_elements_to_size(doc, options.max_xhtml_chars)
            cleaned = lxml_html.tostring(doc, encoding="unicode", method="xml")
        return cleaned

    def _strip_unwanted_tags(self, doc: Any, tags: tuple[str, ...]) -> None:
        if not tags:
            return
        tag_expr = " | ".join(f"//{tag}" for tag in tags)
        if not tag_expr:
            return
        for element in doc.xpath(tag_expr):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)

    def _compact_text(self, value: str | None, max_chars: int) -> str | None:
        if value is None:
            return None
        text = re.sub(r"\s+", " ", value).strip()
        if not text:
            return None
        if max_chars > 0 and len(text) > max_chars:
            if max_chars <= 3:
                text = text[:max_chars]
            else:
                text = text[: max_chars - 3].rstrip() + "..."
        return text

    def _compact_text_nodes(self, doc: Any, max_chars: int) -> None:
        for element in doc.iter():
            if hasattr(element, "text"):
                element.text = self._compact_text(element.text, max_chars)
            if hasattr(element, "tail"):
                element.tail = self._compact_text(element.tail, max_chars)

    def _cap_text_content(self, doc: Any, max_chars: int) -> None:
        if max_chars <= 0:
            return
        remaining = max_chars
        for element in doc.iter():
            if hasattr(element, "text") and element.text:
                if len(element.text) <= remaining:
                    remaining -= len(element.text)
                else:
                    element.text = element.text[: max(0, remaining)].rstrip()
                    remaining = 0
            if remaining <= 0:
                self._clear_text_after(doc, element)
                break
            if hasattr(element, "tail") and element.tail:
                if len(element.tail) <= remaining:
                    remaining -= len(element.tail)
                else:
                    element.tail = element.tail[: max(0, remaining)].rstrip()
                    remaining = 0
            if remaining <= 0:
                self._clear_text_after(doc, element)
                break

    def _clear_text_after(self, doc: Any, stop_element: Any) -> None:
        seen = False
        for element in doc.iter():
            if element is stop_element:
                seen = True
                continue
            if not seen:
                continue
            if hasattr(element, "text") and element.text:
                element.text = None
            if hasattr(element, "tail") and element.tail:
                element.tail = None

    def _trim_elements_to_size(self, doc: Any, max_chars: int) -> None:
        if max_chars <= 0:
            return
        try:
            from lxml import html as lxml_html
        except Exception:
            return
        elements = list(doc.iter())
        for element in reversed(elements):
            parent = element.getparent()
            if parent is None:
                continue
            parent.remove(element)
            current = lxml_html.tostring(doc, encoding="unicode", method="xml")
            if len(current) <= max_chars:
                return


class HtmlRenderer:
    """Renders a web page using a browser and converts it to XHTML."""

    def render(self, options: RenderOptions) -> RenderedPage:
        """
        Render a URL to HTML and XHTML.

        Args:
            options: Configuration for rendering (URL, headless, timeout, etc.).

        Returns:
            A RenderedPage object containing the HTML, XHTML, and status code.
        """
        ignore_https_errors = options.ignore_https_errors or self._is_localhost_url(
            options.url
        )
        with Browser(
            headless=options.headless,
            timeout_ms=options.timeout_ms,
            wait_until=options.wait_until,
            locale=options.locale,
            user_agent=options.user_agent,
            viewport_width=options.viewport_width,
            viewport_height=options.viewport_height,
            ignore_https_errors=ignore_https_errors,
        ) as browser:
            page, response, _elapsed_ms, resources = browser.open(options.url)
            if page is None:
                raise RuntimeError("Failed to open page in browser.")
            try:
                html = self._safe_page_content(page, options.timeout_ms)
            finally:
                page.close()

        xhtml = HtmlConverter().convert(html)

        status_code = None
        if response is not None:
            try:
                status_code = response.status
            except Exception:
                status_code = None
        return RenderedPage(
            html=html, xhtml=xhtml, status_code=status_code, resources=resources
        )

    def _is_localhost_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        host = (parsed.hostname or "").lower()
        return host == "localhost" or host.endswith(".localhost")

    def _safe_page_content(self, page: Any, timeout_ms: int, retries: int = 3) -> str:
        for attempt in range(retries + 1):
            try:
                return page.content()
            except Exception:
                if attempt >= retries:
                    raise
                try:
                    page.wait_for_load_state("networkidle", timeout=timeout_ms)
                except Exception:
                    try:
                        page.wait_for_load_state("load", timeout=timeout_ms)
                    except Exception:
                        pass
                time.sleep(0.2)
        return page.content()


def render_html(options: RenderOptions) -> RenderedPage:
    """Wrapper for backward compatibility."""
    return HtmlRenderer().render(options)


def clean_xhtml(xhtml: str, options: CleanupOptions) -> str:
    """Wrapper for backward compatibility."""
    return XhtmlCleaner().clean(xhtml, options)
from __future__ import annotations

from .types import CheckResult, PageCheck


class PageMetaCheck(PageCheck):
    name = "page_meta"

    def run(self, *, page, response, elapsed_ms: float, resources: list[dict]) -> CheckResult:
        title = page.title() or ""
        description = page.evaluate(
            """
            () => document.querySelector('meta[name="description"]')?.getAttribute('content') || ''
            """
        )
        robots = page.evaluate(
            """
            () => document.querySelector('meta[name="robots"]')?.getAttribute('content') || ''
            """
        )
        og_title = page.evaluate(
            """
            () => document.querySelector('meta[property="og:title"]')?.getAttribute('content') || ''
            """
        )
        og_description = page.evaluate(
            """
            () => document.querySelector('meta[property="og:description"]')?.getAttribute('content') || ''
            """
        )

        status = "ok"
        details_parts: list[str] = []
        if not title:
            status = "warn"
            details_parts.append("missing title")
        if not description:
            status = "warn"
            details_parts.append("missing meta description")
        if not details_parts:
            details_parts.append("title/description present")

        return CheckResult(
            name=self.name,
            status=status,
            details=", ".join(details_parts),
            data={
                "title": title,
                "meta_description": description,
                "meta_robots": robots,
                "og_title": og_title,
                "og_description": og_description,
            },
        )

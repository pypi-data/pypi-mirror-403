from __future__ import annotations

from .types import CheckResult, PageCheck


class CanonicalCheck(PageCheck):
    name = "canonical"

    def run(self, *, page, response, elapsed_ms: float, resources: list[dict]) -> CheckResult:
        canonical = page.evaluate(
            """
            () => document.querySelector('link[rel="canonical"]')?.getAttribute('href') || ''
            """
        )
        if canonical:
            status = "ok"
            details = "canonical present"
        else:
            status = "warn"
            details = "missing canonical"
        return CheckResult(
            name=self.name,
            status=status,
            details=details,
            data={"canonical": canonical},
        )

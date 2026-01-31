from __future__ import annotations

from .types import CheckResult, PageCheck


class WordLiftBootstrapCheck(PageCheck):
    name = "wordlift_bootstrap"

    def run(self, *, page, response, elapsed_ms: float, resources: list[dict]) -> CheckResult:
        target = "cloud.wordlift.io/app/bootstrap.js"
        ok = page.evaluate(
            """
            (target) => {
              const normalize = (value) => (value || '').trim().toLowerCase();
              const isSrcMatch = (src) => {
                const normalized = normalize(src);
                return (
                  normalized === `https://${target}` ||
                  normalized === `http://${target}` ||
                  normalized === `//${target}`
                );
              };
              return Array.from(document.querySelectorAll('script[src]')).some((el) => {
                const src = el.getAttribute('src');
                if (!isSrcMatch(src)) return false;
                const type = normalize(el.getAttribute('type'));
                const asyncAttr = el.hasAttribute('async');
                return type === 'text/javascript' && asyncAttr;
              });
            }
            """,
            target,
        )
        if ok:
            return CheckResult(
                name=self.name,
                status="ok",
                details="async script present with correct type/src",
                data={"src": target},
            )
        return CheckResult(
            name=self.name,
            status="fail",
            details="missing async script with correct type/src",
            data={"src": target},
        )
